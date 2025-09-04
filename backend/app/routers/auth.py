from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from ..services import auth_service


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    nickname: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(data: RegisterIn):
    return auth_service.register(data.email, data.password, data.nickname)


@router.post("/login")
async def login(data: LoginIn):
    return auth_service.login(data.email, data.password)


@router.post("/refresh")
async def refresh(data: TokenRefreshIn):
    return auth_service.refresh(data.refresh_token)


@router.post("/logout")
async def logout(data: LogoutIn):
    auth_service.logout(data.refresh_token)
    return {"success": True}
