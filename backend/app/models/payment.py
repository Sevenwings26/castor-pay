import enum
from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.ledger import Currency


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    VIRTUAL_ACCOUNT = "VIRTUAL_ACCOUNT"
    MICROPAYMENT = "MICROPAYMENT"


class PaymentProvider(str, enum.Enum):
    MOCK_BANK = "MOCK_BANK"
    PAYSTACK = "PAYSTACK"
    FLUTTERWAVE = "FLUTTERWAVE"
    STRIPE = "STRIPE"


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class PaymentTransaction(Base, UUIDMixin, TimestampMixin):
    """
    Core payment intent and execution record.
    Protected by idempotency keys to guarantee at-most-once execution.
    """
    __tablename__ = "payment_transactions"

    reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), index=True, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # in minor units (kobo, pence, cents)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.CARD, nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider), default=PaymentProvider.MOCK_BANK, nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)

    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fee: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # Platform fee in minor units
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)


class OutboxEvent(Base, UUIDMixin, TimestampMixin):
    """
    Transactional Outbox Table ensuring distributed event publishing without two-phase commit.
    """
    __tablename__ = "outbox_events"

    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # e.g. payment.succeeded
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)         # e.g. PAYMENT
    aggregate_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(Enum(OutboxStatus), default=OutboxStatus.PENDING, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
