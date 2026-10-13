from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.escrow import EscrowContract
from app.models.user import Merchant
from app.schemas.escrow import (
    EscrowCreateRequest,
    EscrowResponse,
)
from app.services.escrow_service import escrow_service

router = APIRouter()


@router.post("/", response_model=EscrowResponse)
async def create_escrow_contract(
    req: EscrowCreateRequest,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Creates an escrow agreement with milestone-based disbursement.
    Used for gaming micropayments, peer-to-peer trades, and conditional contractor billing.
    """
    contract = await escrow_service.create_contract(
        session=db,
        merchant_id=merchant.id,
        title=req.title,
        buyer_email=req.buyer_email,
        seller_email=req.seller_email,
        currency=req.currency,
        total_amount=req.total_amount,
        milestones_data=[m.model_dump() for m in req.milestones],
    )
    # Reload with milestones relationship
    stmt = (
        select(EscrowContract)
        .where(EscrowContract.id == contract.id)
        .options(selectinload(EscrowContract.milestones))
    )
    res = (await db.execute(stmt)).scalar_one()
    return res


@router.get("/", response_model=list[EscrowResponse])
async def list_escrow_contracts(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Lists escrow contracts for the authenticated merchant."""
    stmt = (
        select(EscrowContract)
        .where(EscrowContract.merchant_id == merchant.id)
        .options(selectinload(EscrowContract.milestones))
        .order_by(EscrowContract.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    results = (await db.execute(stmt)).scalars().all()
    return results


@router.post("/{contract_reference}/fund", response_model=EscrowResponse)
async def fund_escrow_contract(
    contract_reference: str,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Locks buyer funds into the escrow reserve liability account.
    """
    contract = await escrow_service.fund_contract(
        session=db,
        contract_reference=contract_reference,
    )
    stmt = (
        select(EscrowContract)
        .where(EscrowContract.id == contract.id)
        .options(selectinload(EscrowContract.milestones))
    )
    res = (await db.execute(stmt)).scalar_one()
    return res


@router.post("/{contract_reference}/milestones/{milestone_id}/release", response_model=EscrowResponse)
async def release_escrow_milestone(
    contract_reference: str,
    milestone_id: str,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Disburses funds for an approved milestone deliverable from escrow reserve to payout.
    """
    contract = await escrow_service.release_milestone(
        session=db,
        contract_reference=contract_reference,
        milestone_id=milestone_id,
    )
    stmt = (
        select(EscrowContract)
        .where(EscrowContract.id == contract.id)
        .options(selectinload(EscrowContract.milestones))
    )
    res = (await db.execute(stmt)).scalar_one()
    return res
