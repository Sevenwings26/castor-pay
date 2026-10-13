import enum
from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


# ---------- Schemas Start####################
# DOUBLE ENTRY GENERAL LEDGER
# Asset = Debit : 
# Liability = Credit 
class AccountType(str, enum.Enum):
    ASSET = "ASSET"          # Bank float, clearing accounts, provider receivables
    LIABILITY = "LIABILITY"  # Merchant available funds, customer escrow balances
    EQUITY = "EQUITY"        # Platform capital reserves
    REVENUE = "REVENUE"      # Processing fees collected, FX markup spreads. e.g. transfer charges, withdrawal fees, ATM charges, currency conversion spreads
    EXPENSE = "EXPENSE"      # Provider processing interchange fees paid. e.g. network fees, interchange fees, currency conversion costs


class Direction(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class EntryStatus(str, enum.Enum):
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class Currency(str, enum.Enum):
    NGN = "NGN" # local
    GBP = "GBP" # international
    USD = "USD" # international
    EUR = "EUR" # international

# ---------- Schemas End####################


# ---------- Models Start####################
class Account(Base, UUIDMixin, TimestampMixin):
    """
    General Ledger Account following standard financial accounting hierarchy.
    """
    __tablename__ = "accounts"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    merchant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    lines: Mapped[list["LedgerLine"]] = relationship("LedgerLine", back_populates="account")
    balance_record: Mapped["AccountBalance | None"] = relationship("AccountBalance", back_populates="account", uselist=False)


class JournalEntry(Base, UUIDMixin, TimestampMixin):
    """
    An immutable financial transaction containing balanced debit and credit lines.
    In accounting: sum(debits) must equal sum(credits).
    """
    __tablename__ = "journal_entries"

    reference: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[EntryStatus] = mapped_column(Enum(EntryStatus), default=EntryStatus.POSTED, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)

    lines: Mapped[list["LedgerLine"]] = relationship("LedgerLine", back_populates="journal_entry", cascade="all, delete-orphan")


class LedgerLine(Base, UUIDMixin, TimestampMixin):
    """
    A single debit or credit line on an account within a Journal Entry.
    Amount is stored as a 64-bit integer in minor units (e.g. kobo, pence, cents).
    """
    __tablename__ = "ledger_lines"

    journal_entry_id: Mapped[str] = mapped_column(String(36), ForeignKey("journal_entries.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Always positive integer in minor units
    direction: Mapped[Direction] = mapped_column(Enum(Direction), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    journal_entry: Mapped[JournalEntry] = relationship("JournalEntry", back_populates="lines")
    account: Mapped[Account] = relationship("Account", back_populates="lines")


class AccountBalance(Base, UUIDMixin, TimestampMixin):
    """
    Materialized balance for fast lookups and optimistic concurrency checks.
    Always verifiable against sum of historical ledger lines.
    """
    __tablename__ = "account_balances"

    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), unique=True, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    cleared_balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    pending_balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Optimistic lock counter

    account: Mapped[Account] = relationship("Account", back_populates="balance_record")
# ---------- Models End####################