import asyncio
import json
import random
import boto3

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.services.webhook_service import webhook_service


def get_sqs_client():
    return boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
    )


async def process_event(event_data: dict) -> None:
    """
    Handles payment events, dispatching outbound merchant webhooks.
    """
    event_type = event_data.get("event_type")
    payload = event_data.get("payload", {})
    merchant_id = payload.get("merchant_id")

    logger.info(f"[Worker] Processing event '{event_type}' for aggregate '{event_data.get('aggregate_id')}'")

    if merchant_id:
        async with AsyncSessionLocal() as session:
            await webhook_service.dispatch_merchant_event(
                session=session,
                merchant_id=merchant_id,
                event_type=event_type,
                payload=payload,
            )


async def consume_messages_loop():
    """
    Main SQS event consumer loop.
    Implements exponential backoff, retry management, and poison-pill DLQ handling.
    """
    sqs = get_sqs_client()
    logger.info(f"Starting CastorPay SQS Event Consumer (Queue: {settings.SQS_PAYMENT_QUEUE_NAME})...")

    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl=settings.SQS_PAYMENT_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5,  # Long-polling
                AttributeNames=["All"],
            )

            messages = resp.get("Messages", [])
            for msg in messages:
                receipt_handle = msg["ReceiptHandle"]
                body_raw = msg["Body"]
                receive_count = int(msg.get("Attributes", {}).get("ApproximateReceiveCount", 1))

                try:
                    event_data = json.loads(body_raw)
                    await process_event(event_data)

                    # Delete message from queue upon successful processing
                    sqs.delete_message(
                        QueueUrl=settings.SQS_PAYMENT_QUEUE_URL,
                        ReceiptHandle=receipt_handle,
                    )
                except Exception as exc:
                    logger.error(
                        f"Error processing message (Attempt {receive_count}/{settings.SQS_MAX_RECEIVE_COUNT}): {exc}"
                    )
                    # If maximum retries exceeded, route to Dead-Letter Queue (DLQ)
                    if receive_count >= settings.SQS_MAX_RECEIVE_COUNT:
                        logger.critical(f"Message exceeded max retries. Isolating to DLQ: {body_raw[:200]}")
                        try:
                            sqs.send_message(
                                QueueUrl=settings.SQS_DLQ_URL,
                                MessageBody=body_raw,
                            )
                            sqs.delete_message(
                                QueueUrl=settings.SQS_PAYMENT_QUEUE_URL,
                                ReceiptHandle=receipt_handle,
                            )
                        except Exception as dlq_err:
                            logger.error(f"Failed to route message to DLQ: {dlq_err}")
                    else:
                        # Exponential backoff with jitter before next visibility
                        backoff_seconds = (2 ** receive_count) + random.uniform(0.5, 2.0)
                        sqs.change_message_visibility(
                            QueueUrl=settings.SQS_PAYMENT_QUEUE_URL,
                            ReceiptHandle=receipt_handle,
                            VisibilityTimeout=int(backoff_seconds),
                        )

        except Exception as exc:
            logger.warning(f"Consumer queue connection error: {exc}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(consume_messages_loop())
