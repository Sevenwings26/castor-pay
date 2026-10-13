import json
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import QuoteExpiredError
from app.core.logging import logger
from app.models.fx import FXQuote
from app.models.ledger import Currency, Direction
from app.models.payment import OutboxEvent, OutboxStatus
from app.services.ledger_service import ledger_service


class FXService:
    """
    Treasury & Foreign Exchange (FX) Engine.
    Provides guaranteed 60-second rate locks and settles multi-currency ledger conversions.
    """

    # Realistic base reference mid-market rates
    BENCHMARK_RATES: dict[tuple[str, str], float] = {
        ("GBP", "NGN"): 2150.50,
        ("USD", "NGN"): 1620.00,
        ("EUR", "NGN"): 1780.25,
        ("GBP", "USD"): 1.32,
        ("EUR", "USD"): 1.09,
    }

    def get_effective_rate(self, source: str, target: str) -> tuple[float, int]:
        """Calculates exchange rate incorporating a 100 bps (1.0%) treasury markup spread."""
        pair = (source, target)
        reverse_pair = (target, source)

        spread_bps = 100  # 1.0%

        if pair in self.BENCHMARK_RATES:
            mid = self.BENCHMARK_RATES[pair]
            rate = mid * (1.0 - (spread_bps / 10000.0))
            return round(rate, 4), spread_bps
        elif reverse_pair in self.BENCHMARK_RATES:
            mid = 1.0 / self.BENCHMARK_RATES[reverse_pair]
            rate = mid * (1.0 - (spread_bps / 10000.0))
            return round(rate, 6), spread_bps
        else:
            return 1.0, 0

    async def create_quote(
        self,
        session: AsyncSession,
        merchant_id: str,
        source_currency: Currency,
        target_currency: Currency,
        source_amount: int,
    ) -> FXQuote:
        """
        Generates a firm FX quote locked for exactly 60 seconds.
        """
        if source_amount <= 0:
            raise ValueError("Source amount must be greater than zero.")

        rate, spread_bps = self.get_effective_rate(source_currency.value, target_currency.value)
        target_amount = int(source_amount * rate)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=60)  # Strict 60-second execution window

        quote = FXQuote(
            quote_reference=f"fxq_{secrets.token_hex(12)}",
            merchant_id=merchant_id,
            source_currency=source_currency,
            target_currency=target_currency,
            source_amount=source_amount,
            target_amount=target_amount,
            exchange_rate=rate,
            spread_bps=spread_bps,
            expires_at=expires_at,
            is_executed=False,
        )
        session.add(quote)
        await session.flush()

        logger.info(
            f"Created 60s FX quote '{quote.quote_reference}': "
            f"{source_amount/100:.2f} {source_currency.value} -> {target_amount/100:.2f} {target_currency.value} "
            f"at rate {rate} (expires {expires_at.isoformat()})"
        )
        return quote

    async def execute_quote(
        self,
        session: AsyncSession,
        merchant_id: str,
        quote_reference: str,
    ) -> FXQuote:
        """
        Executes an FX conversion trade if within the 60-second window.
        Performs atomic multi-currency ledger transfer.
        """
        stmt = (
            select(FXQuote)
            .where(
                FXQuote.quote_reference == quote_reference,
                FXQuote.merchant_id == merchant_id,
            )
            .with_for_update()
        )
        quote = (await session.execute(stmt)).scalar_one_or_none()
        if not quote:
            raise ValueError(f"FX quote '{quote_reference}' not found")

        if quote.is_executed:
            return quote

        # Enforce strict 60-second window
        now = datetime.now(timezone.utc)
        if now > quote.expires_at:
            logger.warning(f"FX Quote '{quote_reference}' expired at {quote.expires_at.isoformat()}, rejected execution at {now.isoformat()}")
            raise QuoteExpiredError(quote_reference, quote.expires_at.isoformat())

        # Debits Source Currency Merchant Wallet -> Credits Source Clearing
        src_wallet = await ledger_service.get_or_create_merchant_wallet(session, merchant_id, Currency(quote.source_currency))
        src_clearing = await ledger_service.get_or_create_platform_clearing(session, Currency(quote.source_currency))

        await ledger_service.post_journal_entry(
            session=session,
            reference=f"JE-FX-SRC-{quote.quote_reference}",
            description=f"FX swap debit for {quote.quote_reference}",
            currency=Currency(quote.source_currency),
            lines=[
                {
                    "account_id": src_wallet.id,
                    "amount": quote.source_amount,
                    "direction": Direction.DEBIT,
                    "description": f"FX Outflow {quote.quote_reference}",
                },
                {
                    "account_id": src_clearing.id,
                    "amount": quote.source_amount,
                    "direction": Direction.CREDIT,
                    "description": f"FX Clearing Outflow {quote.quote_reference}",
                },
            ],
        )

        # Debits Target Clearing -> Credits Target Currency Merchant Wallet
        tgt_wallet = await ledger_service.get_or_create_merchant_wallet(session, merchant_id, Currency(quote.target_currency))
        tgt_clearing = await ledger_service.get_or_create_platform_clearing(session, Currency(quote.target_currency))

        await ledger_service.post_journal_entry(
            session=session,
            reference=f"JE-FX-TGT-{quote.quote_reference}",
            description=f"FX swap credit for {quote.quote_reference}",
            currency=Currency(quote.target_currency),
            lines=[
                {
                    "account_id": tgt_clearing.id,
                    "amount": quote.target_amount,
                    "direction": Direction.DEBIT,
                    "description": f"FX Clearing Inflow {quote.quote_reference}",
                },
                {
                    "account_id": tgt_wallet.id,
                    "amount": quote.target_amount,
                    "direction": Direction.CREDIT,
                    "description": f"FX Inflow {quote.quote_reference}",
                },
            ],
        )

        quote.is_executed = True
        quote.executed_at = now

        # Emit outbox event
        outbox = OutboxEvent(
            event_type="fx.conversion_settled",
            aggregate_type="FX",
            aggregate_id=quote.id,
            payload_json=json.dumps({
                "quote_reference": quote.quote_reference,
                "merchant_id": merchant_id,
                "source_currency": quote.source_currency,
                "source_amount": quote.source_amount,
                "target_currency": quote.target_currency,
                "target_amount": quote.target_amount,
                "rate": quote.exchange_rate,
            }),
            status=OutboxStatus.PENDING,
        )
        session.add(outbox)
        await session.flush()

        logger.info(f"Successfully settled FX conversion '{quote.quote_reference}'")
        return quote


fx_service = FXService()
