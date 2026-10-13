from pydantic import BaseModel, EmailStr
from app.models.user import RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    merchant_id: str | None = None
    email: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: RoleEnum = RoleEnum.MERCHANT_ADMIN
    merchant_name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: RoleEnum
    merchant_id: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    name: str = "Secret API Key"


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    raw_key: str | None = None  # Only populated once upon creation
    created_at: str

    class Config:
        from_attributes = True
