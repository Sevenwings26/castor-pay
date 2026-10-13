from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import PaymentGatewayException
from app.core.idempotency import idempotency_manager
from app.core.logging import logger
from app.core.security import generate_api_key, get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.ledger import Currency, Direction
from app.models.user import ApiKey, Merchant, RoleEnum, User
from app.services.ledger_service import ledger_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle events.
    Bootstraps DB tables and seeds default demo accounts if needed.
    """
    logger.info("Initializing CastorPay Gateway Services...")

    # Create tables automatically for instant dev/sandbox operation
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default platform clearing accounts & demo merchant
    async with AsyncSessionLocal() as session:
        for curr in (Currency.NGN, Currency.GBP, Currency.USD, Currency.EUR):
            await ledger_service.get_or_create_platform_clearing(session, curr)
            await ledger_service.get_or_create_platform_fee_revenue(session, curr)

        # Ensure demo merchant exists
        stmt = select(Merchant).where(Merchant.business_email == "demo@castorpay.dev")
        demo_merchant = (await session.execute(stmt)).scalar_one_or_none()
        if not demo_merchant:
            demo_merchant = Merchant(
                name="Demo Gaming Platform (AB InBev Nigeria)",
                business_email="demo@castorpay.dev",
                webhook_url="https://webhook.site/demo-castor-test",
                webhook_secret="whsec_demo_secret_key_12345",
                is_active=True,
            )
            session.add(demo_merchant)
            await session.flush()

            # Seed demo user
            demo_user = User(
                email="demo@castorpay.dev",
                hashed_password=get_password_hash("CastorSecret123!"),
                full_name="Alex Oladipo",
                role=RoleEnum.MERCHANT_ADMIN,
                merchant_id=demo_merchant.id,
                is_active=True,
            )
            session.add(demo_user)

            # Seed admin user
            admin_user = User(
                email="admin@castorpay.dev",
                hashed_password=get_password_hash("AdminSecret123!"),
                full_name="Platform Treasury Officer",
                role=RoleEnum.ADMIN,
                merchant_id=None,
                is_active=True,
            )
            session.add(admin_user)

            # Seed demo API Key
            raw_key = "sk_test_castordemo9921827482"
            api_key = ApiKey(
                merchant_id=demo_merchant.id,
                key_prefix="sk_test",
                key_hash=generate_api_key("sk_test")[1],  # hashed
                name="Default Production Sandbox Key",
                is_active=True,
            )
            session.add(api_key)

            # Pre-fund demo wallet with 5,000,000 kobo (50,000 NGN) and 100,000 pence (1,000 GBP) for testing
            for curr, amt in [(Currency.NGN, 5_000_000), (Currency.GBP, 100_000), (Currency.USD, 150_000)]:
                wallet = await ledger_service.get_or_create_merchant_wallet(session, demo_merchant.id, curr)
                clearing = await ledger_service.get_or_create_platform_clearing(session, curr)
                await ledger_service.post_journal_entry(
                    session=session,
                    reference=f"JE-SEED-DEMO-{curr.value}",
                    description=f"Initial demo float funding ({curr.value})",
                    currency=curr,
                    lines=[
                        {
                            "account_id": clearing.id,
                            "amount": amt,
                            "direction": Direction.DEBIT,
                            "description": "Platform clearing float",
                        },
                        {
                            "account_id": wallet.id,
                            "amount": amt,
                            "direction": Direction.CREDIT,
                            "description": "Initial merchant wallet balance",
                        },
                    ],
                )

            await session.commit()
            logger.info("Database initialized with standard accounts and demo merchant credentials.")

    yield

    # Teardown
    await idempotency_manager.close()
    await engine.dispose()
    logger.info("CastorPay Gateway Services shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Production-Grade Payment Gateway & Embedded Finance Infrastructure. "
        "Built for Multi-Currency Virtual Accounts, Payment Orchestration, Treasury FX, and Escrow."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PaymentGatewayException)
async def gateway_exception_handler(request: Request, exc: PaymentGatewayException):
    """Uniform JSON error formatting for all domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


@app.get("/health", tags=["Health & Monitoring"])
async def health_check():
    """Service health and liveness probe."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "features": {
            "double_entry_ledger": "ACTIVE",
            "idempotency_engine": "ACTIVE",
            "virtual_accounts": "ACTIVE",
            "fx_quote_engine": "ACTIVE",
            "escrow_contracts": "ACTIVE",
            "reconciliation_engine": "ACTIVE",
        },
    }


# Mount API V1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)
