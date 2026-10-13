import enum
from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.ledger import Currency


class VirtualAccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class InboundDepositStatus(str, enum.Enum):
    PENDING = "PENDING"
    CREDITED = "CREDITED"
    REJECTED = "REJECTED"


class VirtualAccount(Base, UUIDMixin, TimestampMixin):
    """
    Dedicated Virtual Account (DVA) for merchant collections.
    Supports multi-currency collections across NGN (NUBAN), GBP (Sort Code + Acc No), and USD (Routing).
    """
    __tablename__ = "virtual_accounts"

    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), index=True, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    account_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    routing_code: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Sort code or SWIFT/Routing
    status: Mapped[VirtualAccountStatus] = mapped_column(Enum(VirtualAccountStatus), default=VirtualAccountStatus.ACTIVE, nullable=False)

    merchant_customer_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    bvn_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ledger_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)

    deposits: Mapped[list["InboundDepositLog"]] = relationship("InboundDepositLog", back_populates="virtual_account")


class InboundDepositLog(Base, UUIDMixin, TimestampMixin):
    """
    Audit log of inbound bank transfer notifications sent via webhook.
    Directly credited to the merchant's ledger account upon verification.
    """
    __tablename__ = "inbound_deposit_logs"

    virtual_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("virtual_accounts.id"), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # in minor units
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_bank: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_session_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    status: Mapped[InboundDepositStatus] = mapped_column(Enum(InboundDepositStatus), default=InboundDepositStatus.CREDITED, nullable=False)
    journal_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"), nullable=True)

    virtual_account: Mapped[VirtualAccount] = relationship("VirtualAccount", back_populates="deposits")
