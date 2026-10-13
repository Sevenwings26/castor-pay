import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Dynamically locate the .env file from the project root or backend folder
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
ROOT_DIR = BACKEND_DIR.parent                               # castor_pay/

ENV_FILE = ROOT_DIR / ".env" if (ROOT_DIR / ".env").exists() else BACKEND_DIR / ".env"

# Load environment variables into process env if .env exists
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """
    Application Settings dynamically loaded from the .env file.
    Default values serve as development fallbacks only when the variable is omitted from .env.
    """
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application
    PROJECT_NAME: str = "CastorPay"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "castor-secret-key-change-in-production-32-chars-min"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # Database Configuration (PostgreSQL 16)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://castor_user:castor_password@localhost:5432/castor_db",
        description="Async PostgreSQL connection string loaded from .env",
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql://castor_user:castor_password@localhost:5432/castor_db",
        description="Synchronous PostgreSQL connection string loaded from .env",
    )

    # Redis Cache & Locking
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string loaded from .env",
    )
    IDEMPOTENCY_TTL_SECONDS: int = 86400
    FX_QUOTE_LOCK_SECONDS: int = 60

    # AWS / LocalStack Messaging (SQS & EventBridge)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_ENDPOINT_URL: Optional[str] = "http://localhost:4566"
    SQS_PAYMENT_QUEUE_NAME: str = "castor-payment-events"
    SQS_PAYMENT_QUEUE_URL: str = "http://localhost:4566/000000000000/castor-payment-events"
    SQS_DLQ_NAME: str = "castor-payment-events-dlq"
    SQS_DLQ_URL: str = "http://localhost:4566/000000000000/castor-payment-events-dlq"
    SQS_MAX_RECEIVE_COUNT: int = 3

    # Webhooks & Security
    WEBHOOK_HMAC_SECRET: str = "castor_whsec_dev_982347198273"
    WEBHOOK_MAX_RETRIES: int = 5

    # Provider API Keys
    PAYSTACK_SECRET_KEY: str = "sk_test_mock_paystack"
    FLUTTERWAVE_SECRET_KEY: str = "flw_sec_test_mock"
    STRIPE_SECRET_KEY: str = "sk_test_mock_stripe"

    # Mock Rail & Chaos Simulator Settings
    MOCK_PROVIDER_ENABLED: bool = True
    CHAOS_FAILURE_RATE: float = 0.0
    CHAOS_LATENCY_MS: int = 100


settings = Settings()
