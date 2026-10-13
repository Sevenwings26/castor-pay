from typing import Any
import httpx
from app.core.config import settings
from app.providers.base import PaymentProviderInterface
from app.providers.mock_bank_adapter import mock_bank_adapter


class StripeAdapter(PaymentProviderInterface):
    """
    Stripe Rail Adapter for UK Faster Payments, SEPA transfers, and international card checkouts.
    """

    BASE_URL = "https://api.stripe.com/v1"

    @property
    def provider_name(self) -> str:
        return "STRIPE"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def initialize_payment(
        self,
        reference: str,
        amount: int,
        currency: str,
        customer_email: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if "mock" in settings.STRIPE_SECRET_KEY:
            res = await mock_bank_adapter.initialize_payment(reference, amount, currency, customer_email, metadata)
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/checkout/sessions",
                headers=self._headers(),
                data={
                    "client_reference_id": reference,
                    "customer_email": customer_email,
                    "payment_method_types[0]": "card",
                    "line_items[0][price_data][currency]": currency.lower(),
                    "line_items[0][price_data][unit_amount]": amount,
                    "line_items[0][price_data][product_data][name]": f"CastorPay Order {reference}",
                    "line_items[0][quantity]": 1,
                    "mode": "payment",
                    "success_url": "https://castorpay.dev/success?ref=" + reference,
                    "cancel_url": "https://castorpay.dev/cancel?ref=" + reference,
                },
            )
            data = resp.json()
            return {
                "provider": self.provider_name,
                "provider_reference": data.get("id"),
                "checkout_url": data.get("url"),
                "status": "PENDING",
                "amount": amount,
                "currency": currency,
            }

    async def verify_payment(self, provider_reference: str) -> dict[str, Any]:
        if "mock" in settings.STRIPE_SECRET_KEY:
            res = await mock_bank_adapter.verify_payment(provider_reference)
            res["provider"] = self.provider_name
            return res

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/checkout/sessions/{provider_reference}",
                headers=self._headers(),
            )
            data = resp.json()
            status = "SUCCEEDED" if data.get("payment_status") == "paid" else "FAILED"
            return {
                "provider": self.provider_name,
                "provider_reference": provider_reference,
                "status": status,
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


stripe_adapter = StripeAdapter()
