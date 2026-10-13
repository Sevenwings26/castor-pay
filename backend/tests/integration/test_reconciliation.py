from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.ledger import Currency
from app.models.payment import PaymentMethod
from app.models.reconciliation import DiscrepancyType, ReconBatch, ReconStatus
from app.models.user import Merchant
from app.services.orchestration_service import orchestration_service
from app.services.reconciliation_service import reconciliation_service


@pytest.mark.asyncio
async def test_3way_reconciliation_matching_and_discrepancy_detection(
    db_session: AsyncSession,
    test_merchant: Merchant,
):
    """
    Verifies 3-Way Reconciliation Engine:
    - Successfully matches valid settlement rows against internal transactions.
    - Accurately detects and flags discrepancies (UNMATCHED_IN_BANK).
    """
    # 1. Initialize and settle an internal transaction
    tx = await orchestration_service.initialize_payment(
        session=db_session,
        merchant_id=test_merchant.id,
        idempotency_key="recon_tx_test_key_01",
        amount=250_000,
        currency=Currency.NGN,
        customer_email="recon_test@example.com",
        payment_method=PaymentMethod.CARD,
    )
    await orchestration_service.settle_successful_payment(db_session, tx.id)

    # 2. Ingest statement with 1 matching line and 1 phantom bank transaction
    statement_date = datetime.now(timezone.utc)
    statement_rows = [
        {
            "external_reference": tx.provider_reference,
            "amount": tx.amount,
            "currency": "NGN",
            "transaction_date": statement_date.isoformat(),
        },
        {
            "external_reference": "bank_phantom_ref_9999",
            "amount": 750_000,
            "currency": "NGN",
            "transaction_date": statement_date.isoformat(),
        },
    ]

    batch = await reconciliation_service.create_batch(
        session=db_session,
        provider="MOCK_BANK",
        statement_date=statement_date,
        statement_lines_data=statement_rows,
    )

    # Reload batch with discrepancies
    stmt = select(ReconBatch).where(ReconBatch.id == batch.id).options(selectinload(ReconBatch.discrepancies))
    batch_loaded = (await db_session.execute(stmt)).scalar_one()

    # 3. Assert matching results
    assert batch_loaded.total_records == 2
    assert batch_loaded.matched_records == 1
    assert batch_loaded.unmatched_records == 1
    assert batch_loaded.status == ReconStatus.DISCREPANCIES_FOUND

    # 4. Assert discrepancy flagged correctly
    assert len(batch_loaded.discrepancies) == 1
    disc = batch_loaded.discrepancies[0]
    assert disc.discrepancy_type == DiscrepancyType.UNMATCHED_IN_BANK
    assert disc.external_reference == "bank_phantom_ref_9999"
    assert disc.variance_amount == 750_000
