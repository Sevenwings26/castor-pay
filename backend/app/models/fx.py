from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.ledger import Currency


class FXRate(Base, UUIDMixin, TimestampMixin):
    """
    Treasury FX table maintaining base exchange rates and markup spreads.
    """
    __tablename__ = "fx_rates"

    source_currency: Mapped[Currency] = mapped_column(String(3), index=True, nullable=False)
    target_currency: Mapped[Currency] = mapped_column(String(3), index=True, nullable=False)
    mid_market_rate: Mapped[float] = mapped_column(Float, nullable=False)
    spread_bps: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # 100 bps = 1.00% markup
    effective_rate: Mapped[float] = mapped_column(Float, nullable=False)


class FXQuote(Base, UUIDMixin, TimestampMixin):
    """
    Guaranteed FX Quote with a strict 60-second execution window.
    Guarantees the exchange rate against market volatility during the swap flow.
    """
    __tablename__ = "fx_quotes"

    quote_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), index=True, nullable=False)
    source_currency: Mapped[Currency] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[Currency] = mapped_column(String(3), nullable=False)

    source_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # minor units
    target_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # minor units
    exchange_rate: Mapped[float] = mapped_column(Float, nullable=False)
    spread_bps: Mapped[int] = mapped_column(Integer, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    is_executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    journal_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"), nullable=True)
