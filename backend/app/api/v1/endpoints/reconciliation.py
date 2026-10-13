from datetime import datetime, timezone
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_or_api_key
from app.db.session import get_db
from app.models.reconciliation import ReconBatch
from app.providers.mock_bank_adapter import mock_bank_adapter
from app.schemas.reconciliation import (
    ReconBatchCreateRequest,
    ReconBatchResponse,
)
from app.services.reconciliation_service import reconciliation_service

router = APIRouter()


@router.post("/batches", response_model=ReconBatchResponse)
async def create_reconciliation_batch(
    req: ReconBatchCreateRequest,
    auth_data: Annotated[Any, Depends(get_current_user_or_api_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Ingests daily bank settlement lines and performs automated 3-way reconciliation.
    Identifies missing transactions, amount discrepancies, and status mismatches.
    """
    batch = await reconciliation_service.create_batch(
        session=db,
        provider=req.provider,
        statement_date=req.statement_date,
        statement_lines_data=[line.model_dump() for line in req.lines],
    )
    stmt = (
        select(ReconBatch)
        .where(ReconBatch.id == batch.id)
        .options(selectinload(ReconBatch.discrepancies))
    )
    res = (await db.execute(stmt)).scalar_one()
    return res


@router.get("/batches", response_model=list[ReconBatchResponse])
async def list_reconciliation_batches(
    auth_data: Annotated[Any, Depends(get_current_user_or_api_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Lists reconciliation audit batches."""
    stmt = (
        select(ReconBatch)
        .options(selectinload(ReconBatch.discrepancies))
        .order_by(ReconBatch.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    batches = (await db.execute(stmt)).scalars().all()
    return batches


@router.post("/batches/simulate-daily-run", response_model=ReconBatchResponse)
async def simulate_daily_reconciliation(
    auth_data: Annotated[Any, Depends(get_current_user_or_api_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Simulates daily bank statement report retrieval from the banking partner and executes 3-way matching.
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mock_lines = await mock_bank_adapter.fetch_settlement_report(today_str)

    batch = await reconciliation_service.create_batch(
        session=db,
        provider="MOCK_BANK",
        statement_date=datetime.now(timezone.utc),
        statement_lines_data=mock_lines,
    )
    stmt = (
        select(ReconBatch)
        .where(ReconBatch.id == batch.id)
        .options(selectinload(ReconBatch.discrepancies))
    )
    res = (await db.execute(stmt)).scalar_one()
    return res
