import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientFundsError, LedgerImbalanceError
from app.models.ledger import AccountType, Currency, Direction
from app.services.ledger_service import ledger_service


@pytest.mark.asyncio
async def test_balanced_journal_entry_succeeds(db_session: AsyncSession):
    """Verifies that a balanced 2-line transaction successfully posts and updates balances."""
    clearing = await ledger_service.get_or_create_platform_clearing(db_session, Currency.NGN)
    wallet = await ledger_service.create_account(
        session=db_session,
        code="LIAB-TEST-MERCHANT-NGN",
        name="Test Merchant Wallet",
        account_type=AccountType.LIABILITY,
        currency=Currency.NGN,
        merchant_id="merchant_test_1",
    )

    amount = 500_000  # 5,000.00 NGN in kobo

    je = await ledger_service.post_journal_entry(
        session=db_session,
        reference="JE-TEST-001",
        description="Customer card deposit",
        currency=Currency.NGN,
        lines=[
            {
                "account_id": clearing.id,
                "amount": amount,
                "direction": Direction.DEBIT,
                "description": "Debit clearing",
            },
            {
                "account_id": wallet.id,
                "amount": amount,
                "direction": Direction.CREDIT,
                "description": "Credit merchant wallet",
            },
        ],
    )

    assert je.id is not None
    assert je.reference == "JE-TEST-001"

    # Verify merchant wallet balance updated to 500,000
    balances = await ledger_service.get_merchant_balances(db_session, "merchant_test_1")
    assert balances["NGN"]["available"] == amount


@pytest.mark.asyncio
async def test_imbalanced_journal_entry_raises_error(db_session: AsyncSession):
    """Verifies that an imbalanced transaction (sum(debits) != sum(credits)) raises LedgerImbalanceError."""
    clearing = await ledger_service.get_or_create_platform_clearing(db_session, Currency.NGN)
    wallet = await ledger_service.create_account(
        session=db_session,
        code="LIAB-TEST-MERCHANT-2",
        name="Test Merchant 2",
        account_type=AccountType.LIABILITY,
        currency=Currency.NGN,
        merchant_id="merchant_test_2",
    )

    # Intentionally imbalanced: 100,000 debit vs 80,000 credit
    with pytest.raises(LedgerImbalanceError) as exc_info:
        await ledger_service.post_journal_entry(
            session=db_session,
            reference="JE-TEST-IMBALANCE",
            description="Broken deposit",
            currency=Currency.NGN,
            lines=[
                {"account_id": clearing.id, "amount": 100_000, "direction": Direction.DEBIT},
                {"account_id": wallet.id, "amount": 80_000, "direction": Direction.CREDIT},
            ],
        )

    assert exc_info.value.total_debit == 100_000
    assert exc_info.value.total_credit == 80_000
    assert exc_info.value.currency == "NGN"


@pytest.mark.asyncio
async def test_multi_leg_transaction_balanced(db_session: AsyncSession):
    """Verifies multi-leg transactions with fees: Debit Clearing = Credit Merchant + Credit Platform Fee."""
    clearing = await ledger_service.get_or_create_platform_clearing(db_session, Currency.GBP)
    fee_account = await ledger_service.get_or_create_platform_fee_revenue(db_session, Currency.GBP)
    wallet = await ledger_service.create_account(
        session=db_session,
        code="LIAB-TEST-GBP-WALLET",
        name="Test GBP Wallet",
        account_type=AccountType.LIABILITY,
        currency=Currency.GBP,
        merchant_id="merchant_test_gbp",
    )

    gross_amount = 10_000  # 100.00 GBP in pence
    fee = 150              # 1.50 GBP fee
    net_amount = 9_850     # 98.50 GBP net

    je = await ledger_service.post_journal_entry(
        session=db_session,
        reference="JE-TEST-MULTI-LEG",
        description="Checkout with fee deduction",
        currency=Currency.GBP,
        lines=[
            {"account_id": clearing.id, "amount": gross_amount, "direction": Direction.DEBIT},
            {"account_id": wallet.id, "amount": net_amount, "direction": Direction.CREDIT},
            {"account_id": fee_account.id, "amount": fee, "direction": Direction.CREDIT},
        ],
    )

    assert je.id is not None
    balances = await ledger_service.get_merchant_balances(db_session, "merchant_test_gbp")
    assert balances["GBP"]["available"] == net_amount


@pytest.mark.asyncio
async def test_insufficient_funds_overdraft_prevention(db_session: AsyncSession):
    """Verifies that attempting to withdraw more than the available balance raises InsufficientFundsError."""
    clearing = await ledger_service.get_or_create_platform_clearing(db_session, Currency.USD)
    wallet = await ledger_service.create_account(
        session=db_session,
        code="LIAB-TEST-USD-WALLET",
        name="Zero Balance USD Wallet",
        account_type=AccountType.LIABILITY,
        currency=Currency.USD,
        merchant_id="merchant_test_zero",
    )

    # Attempt to withdraw 5,000 USD cents when balance is 0
    with pytest.raises(InsufficientFundsError) as exc_info:
        await ledger_service.post_journal_entry(
            session=db_session,
            reference="JE-TEST-OVERDRAFT",
            description="Attempted payout without funds",
            currency=Currency.USD,
            lines=[
                {"account_id": wallet.id, "amount": 5_000, "direction": Direction.DEBIT},
                {"account_id": clearing.id, "amount": 5_000, "direction": Direction.CREDIT},
            ],
            allow_overdraft=False,
        )

    assert exc_info.value.available_balance == 0
    assert exc_info.value.requested_amount == 5_000
