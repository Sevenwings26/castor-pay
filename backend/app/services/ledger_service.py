from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccountNotFoundError, InsufficientFundsError, LedgerImbalanceError
from app.core.logging import logger
from app.models.ledger import (
    Account,
    AccountBalance,
    AccountType,
    Currency,
    Direction,
    EntryStatus,
    JournalEntry,
    LedgerLine,
)


class LedgerService:
    """
    Immutable Double-Entry General Ledger Service.
    Enforces the core accounting invariant: sum(Debits) == sum(Credits) at all times.
    """

    async def create_account(
        self,
        session: AsyncSession,
        code: str,
        name: str,
        account_type: AccountType,
        currency: Currency,
        merchant_id: str | None = None,
    ) -> Account:
        """Creates a ledger account and initializes its zero-balance tracking record."""
        # Check if already exists
        stmt = select(Account).where(Account.code == code)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        account = Account(
            code=code,
            name=name,
            account_type=account_type,
            currency=currency,
            merchant_id=merchant_id,
        )
        session.add(account)
        await session.flush()

        balance = AccountBalance(
            account_id=account.id,
            currency=currency,
            cleared_balance=0,
            pending_balance=0,
            version=1,
        )
        session.add(balance)
        await session.flush()

        logger.info(
            f"Created ledger account: {account.code} ({account.account_type.value}) [{account.currency.value}]"
        )
        return account

    async def get_or_create_merchant_wallet(
        self,
        session: AsyncSession,
        merchant_id: str,
        currency: Currency,
    ) -> Account:
        """Gets or initializes the main available funds liability account for a merchant."""
        code = f"LIAB-MERCHANT-{merchant_id[:8]}-{currency.value}"
        name = f"Merchant Available Balance ({currency.value})"
        return await self.create_account(
            session=session,
            code=code,
            name=name,
            account_type=AccountType.LIABILITY,
            currency=currency,
            merchant_id=merchant_id,
        )

    async def get_or_create_merchant_escrow(
        self,
        session: AsyncSession,
        merchant_id: str,
        currency: Currency,
    ) -> Account:
        """Gets or initializes the locked escrow liability account for a merchant."""
        code = f"LIAB-ESCROW-{merchant_id[:8]}-{currency.value}"
        name = f"Merchant Escrow Reserve ({currency.value})"
        return await self.create_account(
            session=session,
            code=code,
            name=name,
            account_type=AccountType.LIABILITY,
            currency=currency,
            merchant_id=merchant_id,
        )

    async def get_or_create_platform_clearing(
        self,
        session: AsyncSession,
        currency: Currency,
    ) -> Account:
        """Gets or initializes the platform bank settlement clearing asset account."""
        code = f"ASSET-PLATFORM-CLEARING-{currency.value}"
        name = f"Platform Bank Float Settlement ({currency.value})"
        return await self.create_account(
            session=session,
            code=code,
            name=name,
            account_type=AccountType.ASSET,
            currency=currency,
            merchant_id=None,
        )

    async def get_or_create_platform_fee_revenue(
        self,
        session: AsyncSession,
        currency: Currency,
    ) -> Account:
        """Gets or initializes the platform processing fee revenue account."""
        code = f"REV-PLATFORM-FEES-{currency.value}"
        name = f"Platform Processing Fees Collected ({currency.value})"
        return await self.create_account(
            session=session,
            code=code,
            name=name,
            account_type=AccountType.REVENUE,
            currency=currency,
            merchant_id=None,
        )

    async def post_journal_entry(
        self,
        session: AsyncSession,
        reference: str,
        description: str,
        currency: Currency,
        lines: list[dict[str, Any]],
        allow_overdraft: bool = False,
    ) -> JournalEntry:
        """
        Atomically records a multi-line Journal Entry.
        Validates accounting invariant sum(Debits) == sum(Credits).
        Updates materialized AccountBalances with optimistic checks.
        """
        if len(lines) < 2:
            raise ValueError("A Journal Entry must contain at least two ledger lines.")

        total_debits = sum(line["amount"] for line in lines if line["direction"] == Direction.DEBIT)
        total_credits = sum(line["amount"] for line in lines if line["direction"] == Direction.CREDIT)

        # Invariant check
        if total_debits != total_credits:
            raise LedgerImbalanceError(total_debits, total_credits, currency.value)

        # Check for duplicate journal entry reference
        stmt = select(JournalEntry).where(JournalEntry.reference == reference)
        existing_entry = (await session.execute(stmt)).scalar_one_or_none()
        if existing_entry:
            return existing_entry

        # Create Journal Entry
        entry = JournalEntry(
            reference=reference,
            description=description,
            status=EntryStatus.POSTED,
            currency=currency,
        )
        session.add(entry)
        await session.flush()

        # Process each ledger line and update corresponding AccountBalance
        for line_data in lines:
            account_id = line_data["account_id"]
            amount = int(line_data["amount"])
            direction = line_data["direction"]
            line_desc = line_data.get("description", description)

            if amount <= 0:
                raise ValueError(f"Ledger line amount must be strictly positive, got {amount}")

            # Fetch account to verify type
            acct_stmt = select(Account).where(Account.id == account_id)
            account = (await session.execute(acct_stmt)).scalar_one_or_none()
            if not account:
                raise AccountNotFoundError(account_id)

            # Insert immutable ledger line
            line = LedgerLine(
                journal_entry_id=entry.id,
                account_id=account.id,
                amount=amount,
                direction=direction,
                description=line_desc,
            )
            session.add(line)

            # Update account balance based on financial accounting rules:
            # - ASSET & EXPENSE: Debit (+), Credit (-)
            # - LIABILITY, EQUITY & REVENUE: Credit (+), Debit (-)
            bal_stmt = select(AccountBalance).where(AccountBalance.account_id == account.id).with_for_update()
            balance_rec = (await session.execute(bal_stmt)).scalar_one()

            if account.account_type in (AccountType.ASSET, AccountType.EXPENSE):
                delta = amount if direction == Direction.DEBIT else -amount
            else:
                delta = amount if direction == Direction.CREDIT else -amount

            new_balance = balance_rec.cleared_balance + delta

            # Enforce non-negative constraint on merchant balances unless overdraft allowed
            if not allow_overdraft and account.account_type == AccountType.LIABILITY and new_balance < 0:
                raise InsufficientFundsError(
                    account_id=account.id,
                    available_balance=balance_rec.cleared_balance,
                    requested_amount=amount,
                    currency=currency.value,
                )

            balance_rec.cleared_balance = new_balance
            balance_rec.version += 1

        await session.flush()
        logger.info(
            f"Posted journal entry: {entry.reference} [{currency.value} {total_debits / 100:.2f}] with {len(lines)} lines"
        )
        return entry

    async def get_merchant_balances(
        self,
        session: AsyncSession,
        merchant_id: str,
    ) -> dict[str, dict[str, int]]:
        """
        Retrieves current wallet and escrow balances for a merchant across all currencies.
        Returns minor unit integers (kobo, pence, cents).
        """
        stmt = (
            select(Account, AccountBalance)
            .join(AccountBalance, Account.id == AccountBalance.account_id)
            .where(Account.merchant_id == merchant_id)
        )
        results = (await session.execute(stmt)).all()

        balances: dict[str, dict[str, int]] = {}
        for account, balance_rec in results:
            curr = account.currency.value
            if curr not in balances:
                balances[curr] = {"available": 0, "escrow": 0}

            if "ESCROW" in account.code:
                balances[curr]["escrow"] += balance_rec.cleared_balance
            else:
                balances[curr]["available"] += balance_rec.cleared_balance

        return balances


ledger_service = LedgerService()
