import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
import bcrypt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generates a bcrypt hash for the password."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


# JWT Tokens
def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None, extra_claims: Optional[dict] = None) -> str:
    """Creates a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a signed JWT access token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# API Keys
def generate_api_key(prefix: str = "sk_test") -> tuple[str, str]:
    """
    Generates a secure API key pair:
    - raw_key: Returned to the user once (e.g. sk_test_7a9f...)
    - key_hash: SHA-256 hashed version stored in the database
    """
    random_token = secrets.token_hex(24)
    raw_key = f"{prefix}_{random_token}"
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_hash


def hash_api_key(raw_key: str) -> str:
    """Computes SHA-256 hash of an API key for safe database lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# HMAC Webhook Signing
def sign_webhook_payload(secret: str, payload_bytes: bytes) -> str:
    """Computes HMAC-SHA256 signature for outgoing webhook payload."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def verify_webhook_signature(secret: str, payload_bytes: bytes, received_signature: str) -> bool:
    """Constant-time verification of HMAC-SHA256 webhook signature."""
    expected_signature = sign_webhook_payload(secret, payload_bytes)
    return hmac.compare_digest(expected_signature, received_signature)
