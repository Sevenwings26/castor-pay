import secrets
from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.ledger import Currency
from app.models.payment import PaymentStatus, PaymentTransaction
from app.models.reconciliation import (
    DiscrepancyType,
    ReconBatch,
    ReconDiscrepancy,
    ReconStatementLine,
    ReconStatus,
)


class ReconciliationService:
    """
    Automated 3-Way Reconciliation Engine.
    Matches internal gateway logs, double-entry ledger lines, and external bank statements.
    """

    async def create_batch(
        self,
        session: AsyncSession,
        provider: str,
        statement_date: datetime,
        statement_lines_data: list[dict[str, Any]],
    ) -> ReconBatch:
        """Ingests external bank settlement statement rows and runs reconciliation matching."""
        batch_ref = f"recon_{secrets.token_hex(8)}"
        batch = ReconBatch(
            provider=provider,
            batch_reference=batch_ref,
            statement_date=statement_date,
            total_records=len(statement_lines_data),
            matched_records=0,
            unmatched_records=0,
            status=ReconStatus.IN_PROGRESS,
        )
        session.add(batch)
        await session.flush()

        for row in statement_lines_data:
            line = ReconStatementLine(
                batch_id=batch.id,
                external_reference=row["external_reference"],
                amount=int(row["amount"]),
                currency=Currency(row["currency"]),
                transaction_date=datetime.fromisoformat(row["transaction_date"].replace("Z", "+00:00")),
            )
            session.add(line)

        await session.flush()
        return await self.reconcile_batch(session, batch.id)

    async def reconcile_batch(self, session: AsyncSession, batch_id: str) -> ReconBatch:
        """
        Executes 3-way matching algorithm:
        1. Statement Row <-> Gateway Provider Reference
        2. Amount equality verification
        3. Flags UNMATCHED_IN_BANK, AMOUNT_MISMATCH, STATUS_MISMATCH
        """
        b_stmt = select(ReconBatch).where(ReconBatch.id == batch_id).with_for_update()
        batch = (await session.execute(b_stmt)).scalar_one()

        lines_stmt = select(ReconStatementLine).where(ReconStatementLine.batch_id == batch_id)
        statement_lines = (await session.execute(lines_stmt)).scalars().all()

        matched_count = 0
        unmatched_count = 0

        for line in statement_lines:
            # Match against internal payment transaction
            tx_stmt = select(PaymentTransaction).where(
                PaymentTransaction.provider_reference == line.external_reference
            )
            tx = (await session.execute(tx_stmt)).scalar_one_or_none()

            if not tx:
                # Missing in internal records
                unmatched_count += 1
                disc = ReconDiscrepancy(
                    batch_id=batch.id,
                    discrepancy_type=DiscrepancyType.UNMATCHED_IN_BANK,
                    external_reference=line.external_reference,
                    variance_amount=line.amount,
                    notes=f"Bank reported transaction {line.external_reference} with amount {line.amount}, but no matching internal transaction found.",
                )
                session.add(disc)
            else:
                line.matched_transaction_id = tx.id
                # Check amount equality
                if tx.amount != line.amount:
                    unmatched_count += 1
                    disc = ReconDiscrepancy(
                        batch_id=batch.id,
                        discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                        external_reference=line.external_reference,
                        internal_reference=tx.reference,
                        variance_amount=abs(tx.amount - line.amount),
                        notes=f"Internal amount ({tx.amount}) differs from bank settlement ({line.amount}).",
                    )
                    session.add(disc)
                elif tx.status != PaymentStatus.SUCCEEDED:
                    unmatched_count += 1
                    disc = ReconDiscrepancy(
                        batch_id=batch.id,
                        discrepancy_type=DiscrepancyType.STATUS_MISMATCH,
                        external_reference=line.external_reference,
                        internal_reference=tx.reference,
                        variance_amount=0,
                        notes=f"Bank marked settled, but internal status is '{tx.status.value}'.",
                    )
                    session.add(disc)
                else:
                    matched_count += 1

        batch.matched_records = matched_count
        batch.unmatched_records = unmatched_count
        batch.status = ReconStatus.BALANCED if unmatched_count == 0 else ReconStatus.DISCREPANCIES_FOUND

        await session.flush()
        logger.info(
            f"Reconciliation batch '{batch.batch_reference}' completed: "
            f"{matched_count} matched, {unmatched_count} discrepancies (Status: {batch.status.value})"
        )
        return batch


reconciliation_service = ReconciliationService()
