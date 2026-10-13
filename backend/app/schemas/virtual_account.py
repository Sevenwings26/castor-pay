from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.ledger import Currency
from app.models.virtual_account import InboundDepositStatus, VirtualAccountStatus


class VirtualAccountCreateRequest(BaseModel):
    currency: Currency = Currency.NGN
    customer_name: str
    customer_email: EmailStr
    merchant_customer_id: str
    bvn: str | None = None


class VirtualAccountResponse(BaseModel):
    id: str
    currency: Currency
    account_number: str
    account_name: str
    bank_name: str
    routing_code: str | None
    status: VirtualAccountStatus
    merchant_customer_id: str
    bvn_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InboundDepositWebhookRequest(BaseModel):
    account_number: str
    amount: int  # in minor units
    session_id: str
    sender_name: str | None = None
    sender_bank: str | None = None


class InboundDepositResponse(BaseModel):
    id: str
    virtual_account_id: str
    amount: int
    currency: Currency
    status: InboundDepositStatus
    sender_name: str | None
    external_session_id: str
    created_at: datetime

    class Config:
        from_attributes = True
