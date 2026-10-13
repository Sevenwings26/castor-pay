from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.escrow import EscrowStatus, MilestoneStatus
from app.models.ledger import Currency


class MilestoneCreate(BaseModel):
    title: str
    amount: int = Field(..., gt=0, description="Amount in minor units")


class MilestoneResponse(BaseModel):
    id: str
    title: str
    amount: int
    status: MilestoneStatus

    class Config:
        from_attributes = True


class EscrowCreateRequest(BaseModel):
    title: str
    buyer_email: EmailStr
    seller_email: EmailStr
    currency: Currency = Currency.NGN
    total_amount: int = Field(..., gt=0)
    milestones: list[MilestoneCreate]


class EscrowResponse(BaseModel):
    id: str
    contract_reference: str
    title: str
    buyer_email: EmailStr
    seller_email: EmailStr
    currency: Currency
    total_amount: int
    status: EscrowStatus
    created_at: datetime
    milestones: list[MilestoneResponse] = []

    class Config:
        from_attributes = True
