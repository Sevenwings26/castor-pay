from typing import Any
import httpx
from app.core.config import settings
from app.providers.base import PaymentProviderInterface
from app.providers.mock_bank_adapter import mock_bank_adapter


class FlutterwaveAdapter(PaymentProviderInterface):
    """
    Flutterwave Rail Adapter for Pan-African cross-border collections (Ghana, Kenya, Rwanda, Nigeria).
    """

    BASE_URL = "https://api.flutterwave.com/v3"

    @property
    def provider_name(self) -> str:
        return "FLUTTERWAVE"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
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
        if "mock" in settings.FLUTTERWAVE_SECRET_KEY:
            res = await mock_bank_adapter.initialize_payment(reference, amount, currency, customer_email, metadata)
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments",
                headers=self._headers(),
                json={
                    "tx_ref": reference,
                    "amount": amount / 100.0,
                    "currency": currency,
                    "customer": {"email": customer_email},
                    "meta": metadata or {},
                },
            )
            data = resp.json()
            return {
                "provider": self.provider_name,
                "provider_reference": str(data.get("data", {}).get("id")),
                "checkout_url": data.get("data", {}).get("link"),
                "status": "PENDING",
                "amount": amount,
                "currency": currency,
            }

    async def verify_payment(self, provider_reference: str) -> dict[str, Any]:
        if "mock" in settings.FLUTTERWAVE_SECRET_KEY:
            res = await mock_bank_adapter.verify_payment(provider_reference)
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/transactions/{provider_reference}/verify",
                headers=self._headers(),
            )
            data = resp.json()
            status = "SUCCEEDED" if data.get("data", {}).get("status") == "successful" else "FAILED"
            return {
                "provider": self.provider_name,
                "provider_reference": provider_reference,
                "status": status,
                "settled_at": data.get("data", {}).get("created_at"),
            }

    async def create_virtual_account(
        self,
        customer_name: str,
        customer_email: str,
        currency: str,
        merchant_customer_id: str,
        bvn: str | None = None,
    ) -> dict[str, Any]:
        res = await mock_bank_adapter.create_virtual_account(
            customer_name, customer_email, currency, merchant_customer_id, bvn
        )
        res["provider"] = self.provider_name
        return res

    async def fetch_settlement_report(self, statement_date: str) -> list[dict[str, Any]]:
        return await mock_bank_adapter.fetch_settlement_report(statement_date)


flutterwave_adapter = FlutterwaveAdapter()
