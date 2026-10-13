from abc import ABC, abstractmethod
from typing import Any


class PaymentProviderInterface(ABC):
    """
    Abstract Strategy Interface standardizing operations across all banking and payment providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this payment rail."""
        pass

    @abstractmethod
    async def initialize_payment(
        self,
        reference: str,
        amount: int,
        currency: str,
        customer_email: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Initializes a payment intent or checkout session with the external rail.
        Returns provider reference and checkout URL / payment authorization details.
        """
        pass

    @abstractmethod
    async def verify_payment(self, provider_reference: str) -> dict[str, Any]:
        """
        Verifies transaction status directly with the provider.
        """
        pass

    @abstractmethod
    async def create_virtual_account(
        self,
        customer_name: str,
        customer_email: str,
        currency: str,
        merchant_customer_id: str,
        bvn: str | None = None,
    ) -> dict[str, Any]:
        """
        Requests issuance of a Dedicated Virtual Account (DVA).
        Returns account number, account name, bank name, and routing details.
        """
        pass

    @abstractmethod
    async def fetch_settlement_report(self, statement_date: str) -> list[dict[str, Any]]:
        """
        Retrieves daily bank settlement line items for automated 3-way reconciliation.
        """
        pass
