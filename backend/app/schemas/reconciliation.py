from datetime import datetime
from pydantic import BaseModel
from app.models.ledger import Currency
from app.models.reconciliation import DiscrepancyType, ReconStatus


class ReconStatementLineInput(BaseModel):
    external_reference: str
    amount: int
    currency: Currency
    transaction_date: str  # ISO format string


class ReconBatchCreateRequest(BaseModel):
    provider: str
    statement_date: datetime
    lines: list[ReconStatementLineInput]


class ReconDiscrepancyResponse(BaseModel):
    id: str
    discrepancy_type: DiscrepancyType
    external_reference: str | None
    internal_reference: str | None
    variance_amount: int
    notes: str | None
    resolved: bool

    class Config:
        from_attributes = True


class ReconBatchResponse(BaseModel):
    id: str
    batch_reference: str
    provider: str
    statement_date: datetime
    total_records: int
    matched_records: int
    unmatched_records: int
    status: ReconStatus
    created_at: datetime
    discrepancies: list[ReconDiscrepancyResponse] = []

    class Config:
        from_attributes = True
