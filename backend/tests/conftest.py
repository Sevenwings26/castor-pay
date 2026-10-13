import asyncio
import os
from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' is resolvable from any working directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Set testing environment variables
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-testing-32-chars"
os.environ["DEBUG"] = "true"

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.ledger import Currency, Direction
from app.models.user import ApiKey, Merchant, RoleEnum, User
from app.services.ledger_service import ledger_service

# Use in-memory SQLite async engine for lightning-fast self-contained unit tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh isolated database session with tables recreated per test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with overridden database session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_merchant(db_session: AsyncSession) -> Merchant:
    """Creates a pre-seeded test merchant entity with API key and ledger accounts."""
    merchant = Merchant(
        name="Test Gaming Studio",
        business_email="test@gamestudio.com",
        webhook_secret="whsec_test_secret_12345",
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.flush()

    # Pre-create wallets in NGN and GBP
    for curr in (Currency.NGN, Currency.GBP, Currency.USD):
        await ledger_service.get_or_create_platform_clearing(db_session, curr)
        await ledger_service.get_or_create_platform_fee_revenue(db_session, curr)
        wallet = await ledger_service.get_or_create_merchant_wallet(db_session, merchant.id, curr)

        # Seed initial float of 1,000,000 minor units
        clearing = await ledger_service.get_or_create_platform_clearing(db_session, curr)
        await ledger_service.post_journal_entry(
            session=db_session,
            reference=f"JE-SEED-TEST-{merchant.id[:6]}-{curr.value}",
            description=f"Initial test float ({curr.value})",
            currency=curr,
            lines=[
                {"account_id": clearing.id, "amount": 1_000_000, "direction": Direction.DEBIT},
                {"account_id": wallet.id, "amount": 1_000_000, "direction": Direction.CREDIT},
            ],
        )

    await db_session.commit()
    await db_session.refresh(merchant)
    return merchant
