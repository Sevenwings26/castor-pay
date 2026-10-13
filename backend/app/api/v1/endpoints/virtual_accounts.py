from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.user import Merchant
from app.models.virtual_account import VirtualAccount
from app.schemas.virtual_account import (
    InboundDepositResponse,
    InboundDepositWebhookRequest,
    VirtualAccountCreateRequest,
    VirtualAccountResponse,
)
from app.services.virtual_account_service import virtual_account_service

router = APIRouter()


@router.post("/", response_model=VirtualAccountResponse)
async def create_virtual_account(
    req: VirtualAccountCreateRequest,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Issues a multi-currency Dedicated Virtual Account (DVA) for customer collections.
    Supports NGN (NUBAN), GBP (Sort Code + Account Number), and USD (Routing + Account Number).
    """
    va = await virtual_account_service.create_virtual_account(
        session=db,
        merchant_id=merchant.id,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        currency=req.currency,
        merchant_customer_id=req.merchant_customer_id,
        bvn=req.bvn,
    )
    return va


@router.get("/", response_model=list[VirtualAccountResponse])
async def list_virtual_accounts(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Lists virtual accounts issued by this merchant."""
    stmt = (
        select(VirtualAccount)
        .where(VirtualAccount.merchant_id == merchant.id)
        .order_by(VirtualAccount.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    results = (await db.execute(stmt)).scalars().all()
    return results


@router.post("/simulate-inbound-deposit", response_model=InboundDepositResponse)
async def simulate_inbound_deposit(
    req: InboundDepositWebhookRequest,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Simulates an inbound bank transfer into a merchant's virtual account.
    Credits the merchant's ledger wallet instantly and dispatches a webhook.
    """
    deposit = await virtual_account_service.process_inbound_deposit(
        session=db,
        account_number=req.account_number,
        amount=req.amount,
        external_session_id=req.session_id,
        sender_name=req.sender_name,
        sender_bank=req.sender_bank,
    )
    return deposit
