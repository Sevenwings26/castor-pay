from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field
from app.models.ledger import Currency
from app.models.payment import PaymentMethod, PaymentProvider, PaymentStatus


class PaymentInitializeRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount in minor currency units (e.g. kobo, pence, cents)")
    currency: Currency = Field(default=Currency.NGN)
    customer_email: EmailStr
    customer_name: str | None = None
    payment_method: PaymentMethod = Field(default=PaymentMethod.CARD)
    metadata: dict[str, Any] | None = None


class PaymentInitializeResponse(BaseModel):
    transaction_id: str
    reference: str
    amount: int
    fee: int
    currency: Currency
    status: PaymentStatus
    checkout_url: str | None
    provider: PaymentProvider


class PaymentTransactionResponse(BaseModel):
    id: str
    reference: str
    idempotency_key: str
    merchant_id: str
    amount: int
    fee: int
    currency: Currency
    status: PaymentStatus
    payment_method: PaymentMethod
    provider: PaymentProvider
    provider_reference: str | None
    customer_email: EmailStr
    customer_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True
