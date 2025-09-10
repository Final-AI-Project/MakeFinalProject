from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from backend.app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


# ====== Schemas ======
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    nickname: str = Field(min_length=1)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str


class UserMini(BaseModel):
    id: str
    email: EmailStr
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoginOut(TokenPairOut):
    user: UserMini


# ====== Routes ======
@router.post("/register", response_model=UserMini)
async def register(body: RegisterIn):
    user = auth_service.register(body.email, body.password, body.nickname)
    return user


@router.post("/login", response_model=LoginOut)
async def login(body: LoginIn):
    result = auth_service.login(body.email, body.password)
    return result


@router.post("/refresh", response_model=dict)
async def refresh(body: RefreshIn):
    result = auth_service.refresh(body.refresh_token)
    return result


@router.post("/logout", response_model=dict)
async def logout(body: LogoutIn):
    result = auth_service.logout(body.refresh_token)
    return result
