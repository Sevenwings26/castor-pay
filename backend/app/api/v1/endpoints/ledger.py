from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.ledger import Account, JournalEntry
from app.models.user import Merchant
from app.schemas.ledger import (
    AccountResponse,
    BalanceDetail,
    JournalEntryResponse,
    MerchantBalancesResponse,
)
from app.services.ledger_service import ledger_service

router = APIRouter()


@router.get("/balances", response_model=MerchantBalancesResponse)
async def get_merchant_balances(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Returns live balances across all currencies (NGN, GBP, USD, EUR) for the merchant.
    Distinguishes available spendable funds from locked escrow funds.
    Amounts are in minor units (kobo, pence, cents).
    """
    raw_balances = await ledger_service.get_merchant_balances(db, merchant.id)

    # Format response
    formatted: dict[str, BalanceDetail] = {}
    for curr, b in raw_balances.items():
        formatted[curr] = BalanceDetail(
            available=b.get("available", 0),
            escrow=b.get("escrow", 0),
        )

    # Ensure defaults for common currencies
    for curr in ("NGN", "GBP", "USD"):
        if curr not in formatted:
            formatted[curr] = BalanceDetail(available=0, escrow=0)

    return MerchantBalancesResponse(merchant_id=merchant.id, balances=formatted)


@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists chart of accounts associated with the merchant."""
    stmt = select(Account).where(Account.merchant_id == merchant.id)
    accounts = (await db.execute(stmt)).scalars().all()
    return accounts


@router.get("/journal-entries", response_model=list[JournalEntryResponse])
async def list_journal_entries(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Returns audit trail of immutable journal entries and their balanced debit/credit lines.
    """
    stmt = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    entries = (await db.execute(stmt)).scalars().all()
    return entries
