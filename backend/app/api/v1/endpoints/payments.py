from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant
from app.core.idempotency import idempotency_manager
from app.db.session import get_db
from app.models.payment import PaymentTransaction
from app.models.user import Merchant
from app.schemas.payment import (
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    PaymentTransactionResponse,
)
from app.services.orchestration_service import orchestration_service

router = APIRouter()


@router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    req: PaymentInitializeRequest,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
):
    """
    Initializes a new payment transaction with strict distributed idempotency protection.
    If the request with this Idempotency-Key was already processed, returns cached response immediately.
    """
    # 1. Check idempotency response cache
    cached = await idempotency_manager.get_cached_response(idempotency_key)
    if cached:
        return PaymentInitializeResponse(**cached["body"])

    # 2. Acquire exclusive distributed lock
    await idempotency_manager.acquire_lock(idempotency_key, lock_ttl_seconds=30)

    try:
        tx = await orchestration_service.initialize_payment(
            session=db,
            merchant_id=merchant.id,
            idempotency_key=idempotency_key,
            amount=req.amount,
            currency=req.currency,
            customer_email=req.customer_email,
            customer_name=req.customer_name,
            payment_method=req.payment_method,
            metadata=req.metadata,
        )

        response_payload = PaymentInitializeResponse(
            transaction_id=tx.id,
            reference=tx.reference,
            amount=tx.amount,
            fee=tx.fee,
            currency=tx.currency,
            status=tx.status,
            checkout_url=f"https://checkout.castorpay.dev/pay/{tx.reference}",
            provider=tx.provider,
        )

        # 3. Cache response and atomically release lock
        await idempotency_manager.save_response(
            idempotency_key=idempotency_key,
            status_code=status.HTTP_200_OK,
            body=response_payload.model_dump(mode="json"),
        )

        return response_payload
    except Exception:
        # Release lock on error so the client can retry
        await idempotency_manager.release_lock(idempotency_key)
        raise


@router.get("/", response_model=list[PaymentTransactionResponse])
async def list_transactions(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Lists payment transactions for the authenticated merchant."""
    stmt = (
        select(PaymentTransaction)
        .where(PaymentTransaction.merchant_id == merchant.id)
        .order_by(PaymentTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    results = (await db.execute(stmt)).scalars().all()
    return results


@router.get("/{transaction_id}", response_model=PaymentTransactionResponse)
async def get_transaction(
    transaction_id: str,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Fetches details for a specific payment transaction."""
    stmt = select(PaymentTransaction).where(
        PaymentTransaction.id == transaction_id,
        PaymentTransaction.merchant_id == merchant.id,
    )
    tx = (await db.execute(stmt)).scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.post("/{transaction_id}/settle", response_model=PaymentTransactionResponse)
async def settle_transaction(
    transaction_id: str,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Manually/sandbox triggers settlement and posts double-entry ledger lines.
    Transfers funds to merchant wallet and platform fee revenue.
    """
    tx = await orchestration_service.settle_successful_payment(session=db, transaction_id=transaction_id)
    return tx
