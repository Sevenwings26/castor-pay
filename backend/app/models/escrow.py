import enum
from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.ledger import Currency


class EscrowStatus(str, enum.Enum):
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    IN_INSPECTION = "IN_INSPECTION"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    DISPUTED = "DISPUTED"


class MilestoneStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    RELEASED = "RELEASED"


class EscrowContract(Base, UUIDMixin, TimestampMixin):
    """
    Escrow Agreement holding buyer funds in trust until contractual conditions or gaming milestones are fulfilled.
    Backed by dedicated Liability (Escrow Trust) ledger accounts.
    """
    __tablename__ = "escrow_contracts"

    contract_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    buyer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    seller_email: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # in minor units
    status: Mapped[EscrowStatus] = mapped_column(Enum(EscrowStatus), default=EscrowStatus.CREATED, nullable=False)

    dispute_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    funding_journal_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"), nullable=True)
    release_journal_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"), nullable=True)

    milestones: Mapped[list["EscrowMilestone"]] = relationship("EscrowMilestone", back_populates="contract", cascade="all, delete-orphan")


class EscrowMilestone(Base, UUIDMixin, TimestampMixin):
    """
    A deliverable or game achievement triggering partial escrow disbursement.
    """
    __tablename__ = "escrow_milestones"

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("escrow_contracts.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(Enum(MilestoneStatus), default=MilestoneStatus.PENDING, nullable=False)

    contract: Mapped[EscrowContract] = relationship("EscrowContract", back_populates="milestones")
