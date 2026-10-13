import enum
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.ledger import Currency


class ReconStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    BALANCED = "BALANCED"
    DISCREPANCIES_FOUND = "DISCREPANCIES_FOUND"


class DiscrepancyType(str, enum.Enum):
    UNMATCHED_IN_BANK = "UNMATCHED_IN_BANK"       # Exists in bank settlement but missing in internal ledger
    UNMATCHED_IN_LEDGER = "UNMATCHED_IN_LEDGER"   # Settled in internal gateway but missing in bank settlement
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"           # Provider settled different amount than ledger
    STATUS_MISMATCH = "STATUS_MISMATCH"           # Provider status does not match gateway transaction status


class ReconBatch(Base, UUIDMixin, TimestampMixin):
    """
    Daily or periodic reconciliation job ingesting external partner settlement statements.
    """
    __tablename__ = "recon_batches"

    provider: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    batch_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    statement_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmatched_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ReconStatus] = mapped_column(Enum(ReconStatus), default=ReconStatus.IN_PROGRESS, nullable=False)

    statement_lines: Mapped[list["ReconStatementLine"]] = relationship("ReconStatementLine", back_populates="batch", cascade="all, delete-orphan")
    discrepancies: Mapped[list["ReconDiscrepancy"]] = relationship("ReconDiscrepancy", back_populates="batch", cascade="all, delete-orphan")


class ReconStatementLine(Base, UUIDMixin, TimestampMixin):
    """
    Individual row parsed from bank settlement file.
    """
    __tablename__ = "recon_statement_lines"

    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("recon_batches.id"), index=True, nullable=False)
    external_reference: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    matched_transaction_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    batch: Mapped[ReconBatch] = relationship("ReconBatch", back_populates="statement_lines")


class ReconDiscrepancy(Base, UUIDMixin, TimestampMixin):
    """
    Discrepancy flagged during 3-way reconciliation requiring investigation or adjustment.
    """
    __tablename__ = "recon_discrepancies"

    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("recon_batches.id"), index=True, nullable=False)
    discrepancy_type: Mapped[DiscrepancyType] = mapped_column(Enum(DiscrepancyType), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    internal_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    variance_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # in minor units
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    batch: Mapped[ReconBatch] = relationship("ReconBatch", back_populates="discrepancies")
