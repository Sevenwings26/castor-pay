from datetime import datetime
from pydantic import BaseModel
from app.models.ledger import AccountType, Currency, Direction, EntryStatus


class LedgerLineResponse(BaseModel):
    id: str
    account_id: str
    amount: int
    direction: Direction
    description: str | None

    class Config:
        from_attributes = True


class JournalEntryResponse(BaseModel):
    id: str
    reference: str
    description: str
    status: EntryStatus
    currency: Currency
    created_at: datetime
    lines: list[LedgerLineResponse] = []

    class Config:
        from_attributes = True


class AccountResponse(BaseModel):
    id: str
    code: str
    name: str
    account_type: AccountType
    currency: Currency
    merchant_id: str | None

    class Config:
        from_attributes = True


class BalanceDetail(BaseModel):
    available: int  # in minor units
    escrow: int     # in minor units


class MerchantBalancesResponse(BaseModel):
    merchant_id: str
    balances: dict[str, BalanceDetail]
