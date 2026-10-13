from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.db.session import get_db
from app.models.user import Merchant
from app.schemas.fx import (
    FXQuoteExecuteRequest,
    FXQuoteRequest,
    FXQuoteResponse,
)
from app.services.fx_service import fx_service

router = APIRouter()


@router.get("/rates")
async def get_live_rates():
    """Returns current benchmark mid-market rates and available currency pairs."""
    return {
        "benchmark_pairs": [
            {"pair": f"{src}/{tgt}", "rate": rate}
            for (src, tgt), rate in fx_service.BENCHMARK_RATES.items()
        ],
        "spread_bps": 100,
        "guaranteed_quote_window_seconds": 60,
    }


@router.post("/quotes", response_model=FXQuoteResponse)
async def request_fx_quote(
    req: FXQuoteRequest,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Requests a binding FX quote with a strict 60-second rate guarantee.
    The exchange rate will remain fixed for 60 seconds regardless of market fluctuations.
    """
    quote = await fx_service.create_quote(
        session=db,
        merchant_id=merchant.id,
        source_currency=req.source_currency,
        target_currency=req.target_currency,
        source_amount=req.source_amount,
    )
    return quote


@router.post("/quotes/execute", response_model=FXQuoteResponse)
async def execute_fx_quote(
    req: FXQuoteExecuteRequest,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Executes a binding FX quote and converts currency between merchant ledger wallets.
    Fails with HTTP 400 (FX_QUOTE_EXPIRED) if the 60-second window has lapsed.
    """
    quote = await fx_service.execute_quote(
        session=db,
        merchant_id=merchant.id,
        quote_reference=req.quote_reference,
    )
    return quote
