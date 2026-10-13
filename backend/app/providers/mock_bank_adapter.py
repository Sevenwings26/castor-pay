import asyncio
import random
import secrets
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import logger
from app.providers.base import PaymentProviderInterface


class MockBankAdapter(PaymentProviderInterface):
    """
    High-fidelity simulation rail replicating Nigerian, UK, and US banking partner APIs.
    Features configurable network latency and chaos failure injection for testing.
    """

    @property
    def provider_name(self) -> str:
        return "MOCK_BANK"

    async def _simulate_network_conditions(self) -> None:
        """Injects artificial latency and random failure for chaos testing."""
        if settings.CHAOS_LATENCY_MS > 0:
            await asyncio.sleep(settings.CHAOS_LATENCY_MS / 1000.0)

        if settings.CHAOS_FAILURE_RATE > 0.0:
            if random.random() < settings.CHAOS_FAILURE_RATE:
                logger.error("Chaos injection triggered synthetic provider outage")
                raise ProviderUnavailableError(
                    provider_name=self.provider_name,
                    reason="Synthetic network timeout / 504 Gateway Error",
                )

    async def initialize_payment(
        self,
        reference: str,
        amount: int,
        currency: str,
        customer_email: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._simulate_network_conditions()

        provider_ref = f"mock_tx_{secrets.token_hex(12)}"
        checkout_url = f"https://checkout.castorpay.dev/mock-pay/{provider_ref}"

        logger.info(
            f"[MockBank] Initialized charge ref '{reference}' -> provider ref '{provider_ref}'"
        )
        return {
            "provider": self.provider_name,
            "provider_reference": provider_ref,
            "checkout_url": checkout_url,
            "status": "PENDING",
            "amount": amount,
            "currency": currency,
        }

    async def verify_payment(self, provider_reference: str) -> dict[str, Any]:
        await self._simulate_network_conditions()

        # In mock mode, transactions are successful unless prefixed with fail_
        status = "FAILED" if "fail" in provider_reference else "SUCCEEDED"
        return {
            "provider": self.provider_name,
            "provider_reference": provider_reference,
            "status": status,
            "settled_at": datetime.now(timezone.utc).isoformat(),
        }

    async def create_virtual_account(
        self,
        customer_name: str,
        customer_email: str,
        currency: str,
        merchant_customer_id: str,
        bvn: str | None = None,
    ) -> dict[str, Any]:
        await self._simulate_network_conditions()

        if currency == "NGN":
            account_number = f"99{random.randint(10000000, 99999999)}"
            bank_name = "Castor / Providus Bank"
            routing_code = "000035"
        elif currency == "GBP":
            account_number = f"{random.randint(10000000, 99999999)}"
            bank_name = "Castor / ClearBank UK"
            routing_code = "04-00-04"  # Sort code
        elif currency == "USD":
            account_number = f"{random.randint(100000000, 999999999)}"
            bank_name = "Castor / Evolve Bank & Trust"
            routing_code = "021000021"  # Fedwire routing
        else:
            account_number = f"EU{random.randint(1000000000, 9999999999)}"
            bank_name = "Castor / Banking Circle EUR"
            routing_code = "CASTOREU2X"

        return {
            "provider": self.provider_name,
            "account_number": account_number,
            "account_name": f"CastorPay - {customer_name}",
            "bank_name": bank_name,
            "routing_code": routing_code,
            "currency": currency,
            "merchant_customer_id": merchant_customer_id,
        }

    async def fetch_settlement_report(self, statement_date: str) -> list[dict[str, Any]]:
        """Generates synthetic daily settlement records for reconciliation testing."""
        await self._simulate_network_conditions()

        return [
            {
                "external_reference": f"mock_settle_{i}",
                "amount": 250000,  # 2,500.00 NGN
                "currency": "NGN",
                "transaction_date": f"{statement_date}T10:00:00Z",
                "status": "SUCCESS",
            }
            for i in range(1, 6)
        ]


mock_bank_adapter = MockBankAdapter()
