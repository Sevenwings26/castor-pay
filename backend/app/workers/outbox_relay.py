import asyncio
import json
import boto3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.payment import OutboxEvent, OutboxStatus


def get_sqs_client():
    return boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
    )


async def poll_and_dispatch_outbox() -> int:
    """
    Polls pending events from the transactional outbox table and publishes them to AWS SQS.
    Guarantees reliable at-least-once message delivery without distributed dual-write inconsistencies.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .order_by(OutboxEvent.created_at.asc())
            .limit(20)
            .with_for_update(skip_locked=True)
        )
        events = (await session.execute(stmt)).scalars().all()
        if not events:
            return 0

        sqs = get_sqs_client()
        dispatched_count = 0

        for event in events:
            try:
                sqs.send_message(
                    QueueUrl=settings.SQS_PAYMENT_QUEUE_URL,
                    MessageBody=json.dumps({
                        "event_id": event.id,
                        "event_type": event.event_type,
                        "aggregate_type": event.aggregate_type,
                        "aggregate_id": event.aggregate_id,
                        "payload": json.loads(event.payload_json),
                    }),
                    MessageAttributes={
                        "EventType": {
                            "DataType": "String",
                            "StringValue": event.event_type,
                        }
                    },
                )
                event.status = OutboxStatus.PUBLISHED
                dispatched_count += 1
            except Exception as exc:
                event.retry_count += 1
                event.error_message = str(exc)[:500]
                logger.error(f"Failed to publish outbox event '{event.id}' to SQS: {exc}")

        await session.commit()
        if dispatched_count > 0:
            logger.info(f"Outbox relay dispatched {dispatched_count} events to SQS")
        return dispatched_count


async def run_outbox_loop():
    """Continuous polling loop for outbox relay."""
    logger.info("Starting CastorPay Transactional Outbox Relay Loop...")
    while True:
        try:
            count = await poll_and_dispatch_outbox()
            await asyncio.sleep(0.5 if count > 0 else 2.0)
        except Exception as exc:
            logger.error(f"Error in outbox loop: {exc}")
            await asyncio.sleep(3.0)


if __name__ == "__main__":
    asyncio.run(run_outbox_loop())
