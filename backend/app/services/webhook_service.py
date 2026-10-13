import json
from typing import Any
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import sign_webhook_payload
from app.models.user import Merchant


class WebhookService:
    """
    Outbound webhook dispatcher for notifying merchant endpoints of payment events.
    Signs payloads with HMAC-SHA256 for integrity verification.
    """

    async def dispatch_merchant_event(
        self,
        session: AsyncSession,
        merchant_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> bool:
        """Dispatches an HTTP POST event notification to the registered merchant webhook URL."""
        stmt = select(Merchant).where(Merchant.id == merchant_id)
        merchant = (await session.execute(stmt)).scalar_one_or_none()

        if not merchant or not merchant.webhook_url:
            logger.info(f"No active webhook endpoint configured for merchant '{merchant_id}'")
            return False

        body_str = json.dumps({"event": event_type, "data": payload}, sort_keys=True)
        body_bytes = body_str.encode("utf-8")
        signature = sign_webhook_payload(merchant.webhook_secret, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Castor-Signature": signature,
            "X-Castor-Event": event_type,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(merchant.webhook_url, content=body_bytes, headers=headers)
                success = resp.is_success
                logger.info(
                    f"Dispatched webhook '{event_type}' to '{merchant.webhook_url}' (HTTP {resp.status_code})"
                )
                return success
        except Exception as exc:
            logger.warning(
                f"Failed to deliver webhook '{event_type}' to '{merchant.webhook_url}': {exc}"
            )
            return False


webhook_service = WebhookService()
