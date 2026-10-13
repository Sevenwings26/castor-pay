import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccountNotFoundError, PaymentGatewayException
from app.core.logging import logger
from app.models.ledger import AccountType, Currency, Direction
from app.models.payment import OutboxEvent, OutboxStatus
from app.models.virtual_account import (
    InboundDepositLog,
    InboundDepositStatus,
    VirtualAccount,
    VirtualAccountStatus,
)
from app.providers.mock_bank_adapter import mock_bank_adapter
from app.services.ledger_service import ledger_service


class VirtualAccountService:
    """
    Embedded Finance Dynamic Virtual Account (DVA) engine.
    Issues dedicated collection accounts in NGN, GBP, and USD and credits inbound transfers to the ledger.
    """

    async def create_virtual_account(
        self,
        session: AsyncSession,
        merchant_id: str,
        customer_name: str,
        customer_email: str,
        currency: Currency,
        merchant_customer_id: str,
        bvn: str | None = None,
    ) -> VirtualAccount:
        """Issues a new DVA and creates an isolated ledger account for collections."""
        # Check if already exists for this merchant customer
        stmt = (
            select(VirtualAccount)
            .where(
                VirtualAccount.merchant_id == merchant_id,
                VirtualAccount.merchant_customer_id == merchant_customer_id,
                VirtualAccount.currency == currency,
                VirtualAccount.status == VirtualAccountStatus.ACTIVE,
            )
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        # Request issuance from banking rail
        provider_data = await mock_bank_adapter.create_virtual_account(
            customer_name=customer_name,
            customer_email=customer_email,
            currency=currency.value,
            merchant_customer_id=merchant_customer_id,
            bvn=bvn,
        )

        account_number = provider_data["account_number"]

        # Create dedicated ledger liability account for this DVA
        ledger_acct_code = f"LIAB-DVA-{account_number}-{currency.value}"
        dva_ledger_account = await ledger_service.create_account(
            session=session,
            code=ledger_acct_code,
            name=f"Virtual Account {account_number} ({customer_name})",
            account_type=AccountType.LIABILITY,
            currency=currency,
            merchant_id=merchant_id,
        )

        va = VirtualAccount(
            merchant_id=merchant_id,
            currency=currency,
            account_number=account_number,
            account_name=provider_data["account_name"],
            bank_name=provider_data["bank_name"],
            routing_code=provider_data.get("routing_code"),
            status=VirtualAccountStatus.ACTIVE,
            merchant_customer_id=merchant_customer_id,
            bvn_verified=bool(bvn),
            ledger_account_id=dva_ledger_account.id,
        )
        session.add(va)
        await session.flush()

        logger.info(
            f"Issued virtual account '{account_number}' [{currency.value}] for merchant '{merchant_id}'"
        )
        return va

    async def process_inbound_deposit(
        self,
        session: AsyncSession,
        account_number: str,
        amount: int,
        external_session_id: str,
        sender_name: str | None = None,
        sender_bank: str | None = None,
    ) -> InboundDepositLog:
        """
        Processes inbound bank transfer notification.
        Credits funds to the merchant's ledger wallet and dispatches a webhook.
        """
        # Deduplication check
        stmt = select(InboundDepositLog).where(InboundDepositLog.external_session_id == external_session_id)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        # Look up virtual account
        va_stmt = select(VirtualAccount).where(VirtualAccount.account_number == account_number)
        va = (await session.execute(va_stmt)).scalar_one_or_none()
        if not va:
            raise AccountNotFoundError(f"Virtual account '{account_number}' not found")

        # Accounts for double-entry posting
        clearing_account = await ledger_service.get_or_create_platform_clearing(session, va.currency)
        merchant_wallet = await ledger_service.get_or_create_merchant_wallet(session, va.merchant_id, va.currency)

        # Post balanced Journal Entry (Debit Clearing, Credit Merchant Wallet)
        je = await ledger_service.post_journal_entry(
            session=session,
            reference=f"JE-DVA-DEP-{external_session_id}",
            description=f"Inbound transfer from {sender_name or 'Sender'} to DVA {account_number}",
            currency=va.currency,
            lines=[
                {
                    "account_id": clearing_account.id,
                    "amount": amount,
                    "direction": Direction.DEBIT,
                    "description": f"Inbound clearing for session {external_session_id}",
                },
                {
                    "account_id": merchant_wallet.id,
                    "amount": amount,
                    "direction": Direction.CREDIT,
                    "description": f"DVA credit for {account_number}",
                },
            ],
        )

        deposit = InboundDepositLog(
            virtual_account_id=va.id,
            amount=amount,
            currency=va.currency,
            sender_name=sender_name,
            sender_bank=sender_bank,
            external_session_id=external_session_id,
            status=InboundDepositStatus.CREDITED,
            journal_entry_id=je.id,
        )
        session.add(deposit)

        # Emit outbox notification for merchant webhook
        outbox = OutboxEvent(
            event_type="virtual_account.credited",
            aggregate_type="VIRTUAL_ACCOUNT",
            aggregate_id=va.id,
            payload_json=json.dumps({
                "deposit_id": deposit.id,
                "account_number": va.account_number,
                "amount": amount,
                "currency": va.currency.value,
                "sender_name": sender_name,
                "session_id": external_session_id,
            }),
            status=OutboxStatus.PENDING,
        )
        session.add(outbox)
        await session.flush()

        logger.info(
            f"Successfully credited {va.currency.value} {amount/100:.2f} to DVA '{account_number}' [Session: {external_session_id}]"
        )
        return deposit


virtual_account_service = VirtualAccountService()
