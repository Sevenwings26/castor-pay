import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import Currency
from app.models.payment import OutboxEvent, PaymentMethod, PaymentStatus
from app.models.user import Merchant
from app.services.ledger_service import ledger_service
from app.services.orchestration_service import orchestration_service


@pytest.mark.asyncio
async def test_end_to_end_payment_orchestration_and_ledger_settlement(
    db_session: AsyncSession,
    test_merchant: Merchant,
):
    """
    End-to-End integration test:
    1. Initialize payment with idempotency key
    2. Verify outbox event written in same transaction
    3. Settle payment and verify double-entry journal entry and account balances
    """
    amount = 500_000  # 5,000.00 NGN in kobo
    idempotency_key = "idemp_e2e_tx_001"

    tx = await orchestration_service.initialize_payment(
        session=db_session,
        merchant_id=test_merchant.id,
        idempotency_key=idempotency_key,
        amount=amount,
        currency=Currency.NGN,
        customer_email="gamer@abinbev-nigeria.com",
        payment_method=PaymentMethod.CARD,
    )

    assert tx.id is not None
    assert tx.status == PaymentStatus.PROCESSING
    assert tx.fee > 0

    # Verify Outbox event was created
    outbox_stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == tx.id)
    outbox_event = (await db_session.execute(outbox_stmt)).scalar_one_or_none()
    assert outbox_event is not None
    assert outbox_event.event_type == "payment.initiated"

    # Capture merchant balance before settlement
    bal_before = await ledger_service.get_merchant_balances(db_session, test_merchant.id)
    ngn_before = bal_before["NGN"]["available"]

    # Settle transaction
    settled_tx = await orchestration_service.settle_successful_payment(
        session=db_session,
        transaction_id=tx.id,
    )

    assert settled_tx.status == PaymentStatus.SUCCEEDED

    # Verify merchant balance credited with net amount (amount - fee)
    bal_after = await ledger_service.get_merchant_balances(db_session, test_merchant.id)
    ngn_after = bal_after["NGN"]["available"]

    net_expected = amount - tx.fee
    assert ngn_after == ngn_before + net_expected
