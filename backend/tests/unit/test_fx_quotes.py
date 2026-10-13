from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import QuoteExpiredError
from app.models.ledger import Currency
from app.models.user import Merchant
from app.services.fx_service import fx_service


@pytest.mark.asyncio
async def test_fx_quote_creation_and_rate_lock(db_session: AsyncSession, test_merchant: Merchant):
    """Verifies that FX quote locks exchange rate with exactly 60-second TTL."""
    quote = await fx_service.create_quote(
        session=db_session,
        merchant_id=test_merchant.id,
        source_currency=Currency.GBP,
        target_currency=Currency.NGN,
        source_amount=10_000,  # 100.00 GBP
    )

    assert quote.id is not None
    assert quote.source_currency == Currency.GBP
    assert quote.target_currency == Currency.NGN
    assert quote.exchange_rate > 2000.0
    assert quote.is_executed is False

    # Check 60-second window
    now = datetime.now(timezone.utc)
    remaining_seconds = (quote.expires_at - now).total_seconds()
    assert 58 <= remaining_seconds <= 61


@pytest.mark.asyncio
async def test_fx_quote_expired_rejection(db_session: AsyncSession, test_merchant: Merchant):
    """Verifies that an expired quote raises QuoteExpiredError upon execution attempt."""
    quote = await fx_service.create_quote(
        session=db_session,
        merchant_id=test_merchant.id,
        source_currency=Currency.USD,
        target_currency=Currency.NGN,
        source_amount=5_000,
    )

    # Force expiration into past
    quote.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    await db_session.flush()

    with pytest.raises(QuoteExpiredError) as exc_info:
        await fx_service.execute_quote(
            session=db_session,
            merchant_id=test_merchant.id,
            quote_reference=quote.quote_reference,
        )

    assert exc_info.value.quote_id == quote.quote_reference
