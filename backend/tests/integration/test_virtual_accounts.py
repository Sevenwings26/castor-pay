import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import Currency
from app.models.user import Merchant
from app.models.virtual_account import InboundDepositStatus
from app.services.ledger_service import ledger_service
from app.services.virtual_account_service import virtual_account_service


@pytest.mark.asyncio
async def test_virtual_account_issuance_and_inbound_deposit_credit(
    db_session: AsyncSession,
    test_merchant: Merchant,
):
    """
    Verifies that:
    1. Virtual accounts are issued across currencies.
    2. Inbound transfers match the account and credit the merchant ledger.
    3. Duplicate deposit session IDs are deduplicated to prevent double-crediting.
    """
    # 1. Issue DVA
    va = await virtual_account_service.create_virtual_account(
        session=db_session,
        merchant_id=test_merchant.id,
        customer_name="Emeka Okonjo",
        customer_email="emeka@test.com",
        currency=Currency.NGN,
        merchant_customer_id="cust_nigeria_101",
        bvn="22233344455",
    )

    assert va.account_number is not None
    assert va.bank_name is not None

    # Get balance before
    bal_before = await ledger_service.get_merchant_balances(db_session, test_merchant.id)
    ngn_before = bal_before["NGN"]["available"]

    # 2. Simulate inbound bank deposit of 150,000 kobo (1,500 NGN)
    deposit_amount = 150_000
    session_id = "NIP_SESSION_TEST_998811"

    deposit = await virtual_account_service.process_inbound_deposit(
        session=db_session,
        account_number=va.account_number,
        amount=deposit_amount,
        external_session_id=session_id,
        sender_name="Emeka Okonjo",
        sender_bank="Zenith Bank",
    )

    assert deposit.status == InboundDepositStatus.CREDITED

    # Assert merchant ledger wallet increased by deposit_amount
    bal_after = await ledger_service.get_merchant_balances(db_session, test_merchant.id)
    ngn_after = bal_after["NGN"]["available"]
    assert ngn_after == ngn_before + deposit_amount

    # 3. Test deduplication: identical session ID sent again
    duplicate_deposit = await virtual_account_service.process_inbound_deposit(
        session=db_session,
        account_number=va.account_number,
        amount=deposit_amount,
        external_session_id=session_id,
    )
    assert duplicate_deposit.id == deposit.id

    # Verify balance did NOT increase twice!
    bal_after_dup = await ledger_service.get_merchant_balances(db_session, test_merchant.id)
    assert bal_after_dup["NGN"]["available"] == ngn_after
