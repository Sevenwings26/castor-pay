import json
import secrets
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import PaymentGatewayException, ProviderUnavailableError
from app.core.logging import logger
from app.models.ledger import Currency, Direction
from app.models.payment import (
    OutboxEvent,
    OutboxStatus,
    PaymentMethod,
    PaymentProvider,
    PaymentStatus,
    PaymentTransaction,
)
from app.providers.base import PaymentProviderInterface
from app.providers.flutterwave_adapter import flutterwave_adapter
from app.providers.mock_bank_adapter import mock_bank_adapter
from app.providers.paystack_adapter import paystack_adapter
from app.providers.stripe_adapter import stripe_adapter
from app.services.ledger_service import ledger_service


class OrchestrationService:
    """
    Intelligent payment routing and lifecycle orchestration engine.
    Orchestrates provider selection, fee calculation, double-entry settlement, and transactional outbox.
    """

    def select_provider(self, currency: Currency, payment_method: PaymentMethod) -> PaymentProviderInterface:
        """
        Smart routing rules based on currency, rail availability, and cost:
        - NGN -> Paystack (or MockBank if sandbox)
        - GBP / EUR / USD -> Stripe (or MockBank)
        - Default -> MockBank
        """
        if settings.MOCK_PROVIDER_ENABLED and ("mock" in settings.PAYSTACK_SECRET_KEY):
            return mock_bank_adapter

        if currency == Currency.NGN:
            return paystack_adapter
        elif currency in (Currency.GBP, Currency.EUR, Currency.USD):
            return stripe_adapter
        return mock_bank_adapter

    def calculate_platform_fee(self, amount: int, currency: Currency) -> int:
        """
        Calculates platform processing fee:
        - NGN: 1.5% capped at 200,000 kobo (2,000 NGN)
        - GBP/EUR/USD: 1.2% + 20 minor units
        """
        if currency == Currency.NGN:
            fee = int(amount * 0.015)
            return min(fee, 200_000)
        else:
            fee = int(amount * 0.012) + 20
            return fee

    async def initialize_payment(
        self,
        session: AsyncSession,
        merchant_id: str,
        idempotency_key: str,
        amount: int,
        currency: Currency,
        customer_email: str,
        payment_method: PaymentMethod = PaymentMethod.CARD,
        customer_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentTransaction:
        """
        Initializes a payment intent, invokes the external rail, and writes an Outbox record atomically.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        # Check for existing transaction under this idempotency key
        stmt = select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idempotency_key)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        reference = f"cpay_{secrets.token_hex(12)}"
        fee = self.calculate_platform_fee(amount, currency)

        provider = self.select_provider(currency, payment_method)

        # Call upstream provider adapter
        provider_resp = await provider.initialize_payment(
            reference=reference,
            amount=amount,
            currency=currency.value,
            customer_email=customer_email,
            metadata=metadata,
        )

        provider_ref = provider_resp.get("provider_reference")

        # Persist transaction
        tx = PaymentTransaction(
            reference=reference,
            idempotency_key=idempotency_key,
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PROCESSING,
            payment_method=payment_method,
            provider=PaymentProvider(provider.provider_name),
            provider_reference=provider_ref,
            customer_email=customer_email,
            customer_name=customer_name,
            fee=fee,
            metadata_json=json.dumps(metadata or {}),
        )
        session.add(tx)
        await session.flush()

        # Write Transactional Outbox Event within the same ACID boundary
        outbox = OutboxEvent(
            event_type="payment.initiated",
            aggregate_type="PAYMENT",
            aggregate_id=tx.id,
            payload_json=json.dumps({
                "transaction_id": tx.id,
                "reference": tx.reference,
                "amount": tx.amount,
                "currency": tx.currency.value,
                "customer_email": tx.customer_email,
                "checkout_url": provider_resp.get("checkout_url"),
            }),
            status=OutboxStatus.PENDING,
        )
        session.add(outbox)
        await session.flush()

        logger.info(
            f"Initialized payment transaction '{reference}' [{currency.value} {amount/100:.2f}] on {provider.provider_name}"
        )
        return tx

    async def settle_successful_payment(
        self,
        session: AsyncSession,
        transaction_id: str,
    ) -> PaymentTransaction:
        """
        Settles a payment transaction and executes the double-entry general ledger posting.
        Debit: Platform Clearing Asset Account (+Total Amount)
        Credit: Merchant Wallet Liability Account (+Net Amount)
        Credit: Platform Fee Revenue Account (+Platform Fee)
        """
        stmt = select(PaymentTransaction).where(PaymentTransaction.id == transaction_id).with_for_update()
        tx = (await session.execute(stmt)).scalar_one_or_none()
        if not tx:
            raise PaymentGatewayException(f"Transaction '{transaction_id}' not found", code="TX_NOT_FOUND", status_code=404)

        if tx.status == PaymentStatus.SUCCEEDED:
            return tx  # Already settled idempotently

        # Ensure accounts exist in the ledger
        clearing_account = await ledger_service.get_or_create_platform_clearing(session, tx.currency)
        merchant_wallet = await ledger_service.get_or_create_merchant_wallet(session, tx.merchant_id, tx.currency)
        fee_account = await ledger_service.get_or_create_platform_fee_revenue(session, tx.currency)

        net_amount = tx.amount - tx.fee

        # Post balanced Journal Entry (Total Debits == Total Credits)
        journal_lines = [
            {
                "account_id": clearing_account.id,
                "amount": tx.amount,
                "direction": Direction.DEBIT,
                "description": f"Settlement received for {tx.reference}",
            },
            {
                "account_id": merchant_wallet.id,
                "amount": net_amount,
                "direction": Direction.CREDIT,
                "description": f"Net payout for {tx.reference}",
            },
            {
                "account_id": fee_account.id,
                "amount": tx.fee,
                "direction": Direction.CREDIT,
                "description": f"Processing fee for {tx.reference}",
            },
        ]

        await ledger_service.post_journal_entry(
            session=session,
            reference=f"JE-PAY-{tx.reference}",
            description=f"Payment settlement for {tx.reference}",
            currency=tx.currency,
            lines=journal_lines,
        )

        tx.status = PaymentStatus.SUCCEEDED

        # Emit Outbox Event for downstream SQS consumers & merchant webhook
        outbox = OutboxEvent(
            event_type="payment.succeeded",
            aggregate_type="PAYMENT",
            aggregate_id=tx.id,
            payload_json=json.dumps({
                "transaction_id": tx.id,
                "reference": tx.reference,
                "merchant_id": tx.merchant_id,
                "amount": tx.amount,
                "net_amount": net_amount,
                "fee": tx.fee,
                "currency": tx.currency.value,
                "status": "SUCCEEDED",
            }),
            status=OutboxStatus.PENDING,
        )
        session.add(outbox)
        await session.flush()

        logger.info(f"Payment transaction '{tx.reference}' settled successfully in ledger")
        return tx


orchestration_service = OrchestrationService()
