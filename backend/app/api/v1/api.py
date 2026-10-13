from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    escrow,
    fx_rates,
    ledger,
    payments,
    reconciliation,
    virtual_accounts,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & API Keys"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payment Orchestration"])
api_router.include_router(virtual_accounts.router, prefix="/virtual-accounts", tags=["Virtual Accounts (DVA)"])
api_router.include_router(fx_rates.router, prefix="/fx", tags=["Cross-Border FX & Quotes"])
api_router.include_router(escrow.router, prefix="/escrow", tags=["Escrow & Gaming Micropayments"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Inbound Webhooks"])
api_router.include_router(ledger.router, prefix="/ledger", tags=["Double-Entry Ledger"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["3-Way Reconciliation"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Treasury & DLQ"])
