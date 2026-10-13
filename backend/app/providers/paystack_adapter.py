from typing import Any
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import PaymentProviderInterface
from app.providers.mock_bank_adapter import mock_bank_adapter


class PaystackAdapter(PaymentProviderInterface):
    """
    Paystack Rail Adapter for Nigerian card payments, USSD, and dedicated NUBAN virtual accounts.
    """

    BASE_URL = "https://api.paystack.co"

    @property
    def provider_name(self) -> str:
        return "PAYSTACK"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def initialize_payment(
        self,
        reference: str,
        amount: int,
        currency: str,
        customer_email: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # If in sandbox or mock mode with mock key, delegate to high-fidelity simulator
        if "mock" in settings.PAYSTACK_SECRET_KEY:
            res = await mock_bank_adapter.initialize_payment(reference, amount, currency, customer_email, metadata)
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/transaction/initialize",
                headers=self._headers(),
                json={
                    "reference": reference,
                    "amount": amount,
                    "email": customer_email,
                    "currency": currency,
                    "metadata": metadata or {},
                },
            )
            data = resp.json()
            if not resp.is_success or not data.get("status"):
                raise ValueError(f"Paystack initialization error: {data.get('message')}")

            return {
                "provider": self.provider_name,
                "provider_reference": data["data"]["reference"],
                "checkout_url": data["data"]["authorization_url"],
                "status": "PENDING",
                "amount": amount,
                "currency": currency,
            }

    async def verify_payment(self, provider_reference: str) -> dict[str, Any]:
        if "mock" in settings.PAYSTACK_SECRET_KEY:
            res = await mock_bank_adapter.verify_payment(provider_reference)
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/transaction/verify/{provider_reference}",
                headers=self._headers(),
            )
            data = resp.json()
            status = "SUCCEEDED" if data.get("data", {}).get("status") == "success" else "FAILED"
            return {
                "provider": self.provider_name,
                "provider_reference": provider_reference,
                "status": status,
                "settled_at": data.get("data", {}).get("paid_at"),
            }

    async def create_virtual_account(
        self,
        customer_name: str,
        customer_email: str,
        currency: str,
        merchant_customer_id: str,
        bvn: str | None = None,
    ) -> dict[str, Any]:
        if "mock" in settings.PAYSTACK_SECRET_KEY:
            res = await mock_bank_adapter.create_virtual_account(
                customer_name, customer_email, currency, merchant_customer_id, bvn
            )
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/dedicated_account/assign",
                headers=self._headers(),
                json={
                    "email": customer_email,
                    "first_name": customer_name.split()[0] if " " in customer_name else customer_name,
                    "last_name": customer_name.split()[-1] if " " in customer_name else "Customer",
                    "bvn": bvn or "22222222222",
                    "preferred_bank": "wema-bank",
                },
            )
            data = resp.json()
            account_data = data.get("data", {}).get("dedicated_account", {})
            return {
                "provider": self.provider_name,
                "account_number": account_data.get("account_number"),
                "account_name": account_data.get("account_name"),
                "bank_name": account_data.get("bank", {}).get("name", "Wema Bank"),
                "currency": "NGN",
                "merchant_customer_id": merchant_customer_id,
            }

    async def fetch_settlement_report(self, statement_date: str) -> list[dict[str, Any]]:
        return await mock_bank_adapter.fetch_settlement_report(statement_date)


paystack_adapter = PaystackAdapter()
