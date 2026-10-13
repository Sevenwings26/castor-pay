import json
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import verify_webhook_signature
from app.db.session import get_db
from app.models.payment import PaymentTransaction
from app.services.orchestration_service import orchestration_service

router = APIRouter()


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_paystack_signature: Annotated[str | None, Header(alias="x-paystack-signature")] = None,
):
    """
    Inbound webhook listener for Paystack payment notifications.
    Verifies HMAC-SHA256 signature and settles transaction via double-entry ledger.
    """
    body_bytes = await request.body()

    # Signature verification (skipped if test mock secret)
    if "mock" not in settings.PAYSTACK_SECRET_KEY:
        if not x_paystack_signature or not verify_webhook_signature(settings.PAYSTACK_SECRET_KEY, body_bytes, x_paystack_signature):
            raise HTTPException(status_code=401, detail="Invalid Paystack HMAC signature")

    payload = json.loads(body_bytes.decode("utf-8"))
    event = payload.get("event")
    data = payload.get("data", {})

    logger.info(f"Received Paystack webhook event: {event}")

    if event == "charge.success":
        reference = data.get("reference")
        stmt = select(PaymentTransaction).where(PaymentTransaction.reference == reference)
        tx = (await db.execute(stmt)).scalar_one_or_none()
        if tx:
            await orchestration_service.settle_successful_payment(db, tx.id)

    return {"status": "ok"}


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    stripe_signature: Annotated[str | None, Header(alias="stripe-signature")] = None,
):
    """
    Inbound webhook listener for Stripe payment intent updates.
    """
    body_bytes = await request.body()
    payload = json.loads(body_bytes.decode("utf-8"))

    event_type = payload.get("type")
    data_object = payload.get("data", {}).get("object", {})

    logger.info(f"Received Stripe webhook event: {event_type}")

    if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
        ref = data_object.get("client_reference_id")
        if ref:
            stmt = select(PaymentTransaction).where(PaymentTransaction.reference == ref)
            tx = (await db.execute(stmt)).scalar_one_or_none()
            if tx:
                await orchestration_service.settle_successful_payment(db, tx.id)

    return {"status": "ok"}
