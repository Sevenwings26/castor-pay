#!/usr/bin/env bash
set -eo pipefail

echo "==> [LocalStack Init] Initializing SQS Queues and Dead Letter Queue for CastorPay..."

# Create Dead Letter Queue (DLQ)
awslocal sqs create-queue \
  --queue-name castor-payment-events-dlq \
  --region us-east-1

DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "http://localhost:4566/000000000000/castor-payment-events-dlq" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

echo "==> [LocalStack Init] DLQ Created with ARN: ${DLQ_ARN}"

# Create Main Payment Events Queue with RedrivePolicy pointing to DLQ
REDRIVE_POLICY="{\"deadLetterTargetArn\":\"${DLQ_ARN}\",\"maxReceiveCount\":\"3\"}"

awslocal sqs create-queue \
  --queue-name castor-payment-events \
  --attributes "{\"RedrivePolicy\": \"$(echo $REDRIVE_POLICY | sed 's/"/\\"/g')\", \"VisibilityTimeout\": \"30\"}" \
  --region us-east-1

echo "==> [LocalStack Init] CastorPay Queues successfully provisioned!"
