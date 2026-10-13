import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_merchant, get_current_user_or_api_key
from app.core.security import create_access_token, generate_api_key, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import ApiKey, Merchant, RoleEnum, User
from app.schemas.auth import ApiKeyCreate, ApiKeyResponse, LoginRequest, TokenResponse, UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(
    req: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Registers a new merchant business and owner account with initial API key."""
    # Check if user already exists
    stmt = select(User).where(User.email == req.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Create Merchant entity
    merchant_name = req.merchant_name or f"{req.full_name}'s Business"
    merchant = Merchant(
        name=merchant_name,
        business_email=req.email,
        webhook_secret=f"whsec_{secrets.token_hex(24)}",
        is_active=True,
    )
    db.add(merchant)
    await db.flush()

    # Create User
    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
        merchant_id=merchant.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create default secret API Key
    raw_key, key_hash = generate_api_key(prefix="sk_test")
    api_key = ApiKey(
        merchant_id=merchant.id,
        key_prefix="sk_test",
        key_hash=key_hash,
        name="Default Test Key",
        is_active=True,
    )
    db.add(api_key)
    await db.commit()

    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "merchant_id": merchant.id, "email": user.email},
    )
    return TokenResponse(
        access_token=token,
        role=user.role,
        merchant_id=merchant.id,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticates dashboard user and returns JWT access token."""
    stmt = select(User).where(User.email == req.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")

    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "merchant_id": user.merchant_id, "email": user.email},
    )
    return TokenResponse(
        access_token=token,
        role=user.role,
        merchant_id=user.merchant_id,
        email=user.email,
    )


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_new_api_key(
    req: ApiKeyCreate,
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generates a new API Key for server-to-server merchant integrations."""
    raw_key, key_hash = generate_api_key(prefix="sk_test")
    api_key = ApiKey(
        merchant_id=merchant.id,
        key_prefix="sk_test",
        key_hash=key_hash,
        name=req.name,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        raw_key=raw_key,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    merchant: Annotated[Merchant, Depends(get_current_merchant)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists existing API keys (secret hashes masked)."""
    stmt = select(ApiKey).where(ApiKey.merchant_id == merchant.id)
    keys = (await db.execute(stmt)).scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            raw_key=f"{k.key_prefix}••••••••••••••••••••",
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]
