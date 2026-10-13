from datetime import datetime
from pydantic import BaseModel, Field
from app.models.ledger import Currency


class FXQuoteRequest(BaseModel):
    source_currency: Currency
    target_currency: Currency
    source_amount: int = Field(..., gt=0, description="Amount in source minor currency units")


class FXQuoteResponse(BaseModel):
    quote_reference: str
    source_currency: Currency
    target_currency: Currency
    source_amount: int
    target_amount: int
    exchange_rate: float
    spread_bps: int
    expires_at: datetime
    is_executed: bool

    class Config:
        from_attributes = True


class FXQuoteExecuteRequest(BaseModel):
    quote_reference: str
