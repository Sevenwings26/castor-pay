from collections.abc import AsyncGenerator
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import IdempotencyConflictError
from app.core.idempotency import idempotency_manager
from app.core.security import decode_access_token, hash_api_key
from app.db.session import get_db
from app.models.user import ApiKey, Merchant, RoleEnum, User

security = HTTPBearer(auto_error=False)


async def get_current_user_or_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_header: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
) -> tuple[Optional[User], Optional[Merchant]]:
    """
    Authenticates requests via either:
    1. JWT Bearer token (Frontend UI user session)
    2. API Key (Developer API server-to-server: sk_test_... or sk_live_...)
    """
    token_str = None
    if auth_header:
        token_str = auth_header.credentials
    elif x_api_key:
        token_str = x_api_key

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token or X-API-Key",
        )

    # Check if API Key format (sk_test_... or sk_live_...)
    if token_str.startswith("sk_"):
        key_hash = hash_api_key(token_str)
        stmt = (
            select(ApiKey, Merchant)
            .join(Merchant, ApiKey.merchant_id == Merchant.id)
            .where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        )
        result = (await db.execute(stmt)).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API Key",
            )
        api_key, merchant = result
        return None, merchant

    # Otherwise validate as JWT
    try:
        payload = decode_access_token(token_str)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    merchant = None
    if user.merchant_id:
        m_stmt = select(Merchant).where(Merchant.id == user.merchant_id)
        merchant = (await db.execute(m_stmt)).scalar_one_or_none()

    return user, merchant


async def get_current_merchant(
    auth_data: Annotated[tuple[Optional[User], Optional[Merchant]], Depends(get_current_user_or_api_key)],
) -> Merchant:
    """Ensures request is authenticated as a valid merchant."""
    user, merchant = auth_data
    if merchant:
        return merchant
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Merchant context required")


def require_role(allowed_roles: list[RoleEnum]):
    """Role-Based Access Control (RBAC) dependency factory."""
    async def role_checker(
        auth_data: Annotated[tuple[Optional[User], Optional[Merchant]], Depends(get_current_user_or_api_key)],
    ) -> User:
        user, _ = auth_data
        if not user or user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return user
    return role_checker


async def verify_idempotency_key(
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
) -> Optional[str]:
    """Validates presence and format of Idempotency-Key header on mutating requests."""
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required 'Idempotency-Key' HTTP header",
        )
    return idempotency_key
