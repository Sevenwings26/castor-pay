import enum
from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    TREASURY = "TREASURY"
    MERCHANT_ADMIN = "MERCHANT_ADMIN"
    DEVELOPER = "DEVELOPER"
    AUDITOR = "AUDITOR"


class Merchant(Base, UUIDMixin, TimestampMixin):
    """Business entity using CastorPay for payment processing and embedded finance."""
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    webhook_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="merchant", cascade="all, delete-orphan")
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="merchant", cascade="all, delete-orphan")


class User(Base, UUIDMixin, TimestampMixin):
    """User account with Role-Based Access Control (RBAC)."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.MERCHANT_ADMIN, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    merchant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("merchants.id"), nullable=True)
    merchant: Mapped[Merchant | None] = relationship("Merchant", back_populates="users")


class ApiKey(Base, UUIDMixin, TimestampMixin):
    """API Keys for server-to-server merchant integrations."""
    __tablename__ = "api_keys"

    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. sk_test_, sk_live_
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="Default Secret Key", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="api_keys")
