import json
import secrets
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EscrowTransitionError
from app.core.logging import logger
from app.models.escrow import EscrowContract, EscrowMilestone, EscrowStatus, MilestoneStatus
from app.models.ledger import Currency, Direction
from app.models.payment import OutboxEvent, OutboxStatus
from app.services.ledger_service import ledger_service


class EscrowService:
    """
    Escrow & Gaming Micropayments Engine.
    Locks player/buyer funds into escrow reserve liability accounts and handles milestone releases and dispute arbitrations.
    """

    async def create_contract(
        self,
        session: AsyncSession,
        merchant_id: str,
        title: str,
        buyer_email: str,
        seller_email: str,
        currency: Currency,
        total_amount: int,
        milestones_data: list[dict[str, Any]],
    ) -> EscrowContract:
        """Creates a new escrow agreement with milestones."""
        if total_amount <= 0:
            raise ValueError("Total amount must be greater than zero.")

        contract_ref = f"esc_{secrets.token_hex(12)}"
        contract = EscrowContract(
            contract_reference=contract_ref,
            merchant_id=merchant_id,
            title=title,
            buyer_email=buyer_email,
            seller_email=seller_email,
            currency=currency,
            total_amount=total_amount,
            status=EscrowStatus.CREATED,
        )
        session.add(contract)
        await session.flush()

        for m in milestones_data:
            milestone = EscrowMilestone(
                contract_id=contract.id,
                title=m["title"],
                amount=int(m["amount"]),
                status=MilestoneStatus.PENDING,
            )
            session.add(milestone)

        await session.flush()
        logger.info(f"Created escrow contract '{contract_ref}' [{currency.value} {total_amount/100:.2f}]")
        return contract

    async def fund_contract(
        self,
        session: AsyncSession,
        contract_reference: str,
    ) -> EscrowContract:
        """
        Locks buyer funds into the escrow reserve liability account.
        Debit: Merchant Available Wallet
        Credit: Merchant Escrow Reserve
        """
        stmt = (
            select(EscrowContract)
            .where(EscrowContract.contract_reference == contract_reference)
            .with_for_update()
        )
        contract = (await session.execute(stmt)).scalar_one_or_none()
        if not contract:
            raise ValueError(f"Escrow contract '{contract_reference}' not found")

        if contract.status != EscrowStatus.CREATED:
            raise EscrowTransitionError(contract.status.value, "FUND")

        wallet = await ledger_service.get_or_create_merchant_wallet(session, contract.merchant_id, contract.currency)
        escrow_acct = await ledger_service.get_or_create_merchant_escrow(session, contract.merchant_id, contract.currency)

        # Move funds into locked escrow ledger account
        je = await ledger_service.post_journal_entry(
            session=session,
            reference=f"JE-ESC-FUND-{contract.contract_reference}",
            description=f"Fund escrow contract {contract.title}",
            currency=contract.currency,
            lines=[
                {
                    "account_id": wallet.id,
                    "amount": contract.total_amount,
                    "direction": Direction.DEBIT,
                    "description": f"Lock funds for escrow {contract.contract_reference}",
                },
                {
                    "account_id": escrow_acct.id,
                    "amount": contract.total_amount,
                    "direction": Direction.CREDIT,
                    "description": f"Escrow hold for {contract.contract_reference}",
                },
            ],
        )

        contract.status = EscrowStatus.FUNDED
        contract.funding_journal_entry_id = je.id

        # Outbox event
        outbox = OutboxEvent(
            event_type="escrow.funded",
            aggregate_type="ESCROW",
            aggregate_id=contract.id,
            payload_json=json.dumps({
                "contract_reference": contract.contract_reference,
                "amount": contract.total_amount,
                "currency": contract.currency.value,
                "title": contract.title,
            }),
            status=OutboxStatus.PENDING,
        )
        session.add(outbox)
        await session.flush()

        logger.info(f"Escrow contract '{contract_reference}' funded successfully")
        return contract

    async def release_milestone(
        self,
        session: AsyncSession,
        contract_reference: str,
        milestone_id: str,
    ) -> EscrowContract:
        """
        Disburses milestone funds from escrow reserve to payout clearing.
        Debit: Merchant Escrow Reserve
        Credit: Platform Clearing (payout)
        """
        stmt = (
            select(EscrowContract)
            .where(EscrowContract.contract_reference == contract_reference)
            .with_for_update()
        )
        contract = (await session.execute(stmt)).scalar_one_or_none()
        if not contract:
            raise ValueError(f"Escrow contract '{contract_reference}' not found")

        if contract.status not in (EscrowStatus.FUNDED, EscrowStatus.IN_INSPECTION):
            raise EscrowTransitionError(contract.status.value, "RELEASE_MILESTONE")

        # Find milestone
        m_stmt = (
            select(EscrowMilestone)
            .where(
                EscrowMilestone.id == milestone_id,
                EscrowMilestone.contract_id == contract.id,
            )
            .with_for_update()
        )
        milestone = (await session.execute(m_stmt)).scalar_one_or_none()
        if not milestone:
            raise ValueError(f"Milestone '{milestone_id}' not found")

        if milestone.status == MilestoneStatus.RELEASED:
            return contract

        escrow_acct = await ledger_service.get_or_create_merchant_escrow(session, contract.merchant_id, contract.currency)
        clearing = await ledger_service.get_or_create_platform_clearing(session, contract.currency)

        # Release milestone amount
        await ledger_service.post_journal_entry(
            session=session,
            reference=f"JE-ESC-REL-{contract.contract_reference}-{milestone.id[:8]}",
            description=f"Release milestone '{milestone.title}' for {contract.contract_reference}",
            currency=contract.currency,
            lines=[
                {
                    "account_id": escrow_acct.id,
                    "amount": milestone.amount,
                    "direction": Direction.DEBIT,
                    "description": f"Escrow release for milestone {milestone.title}",
                },
                {
                    "account_id": clearing.id,
                    "amount": milestone.amount,
                    "direction": Direction.CREDIT,
                    "description": f"Disbursement clearing {contract.contract_reference}",
                },
            ],
        )

        milestone.status = MilestoneStatus.RELEASED

        # Check if all milestones released
        all_milestones_stmt = select(EscrowMilestone).where(EscrowMilestone.contract_id == contract.id)
        all_m = (await session.execute(all_milestones_stmt)).scalars().all()
        if all(m.status == MilestoneStatus.RELEASED for m in all_m):
            contract.status = EscrowStatus.RELEASED

        await session.flush()
        logger.info(f"Released milestone '{milestone.title}' for escrow '{contract_reference}'")
        return contract


escrow_service = EscrowService()
