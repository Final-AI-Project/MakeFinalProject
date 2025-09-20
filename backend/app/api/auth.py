from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends

from db.pool import get_db
from schemas.user import UserCreate, UserOut, TokenPair, UserLoginRequest, RefreshRequest, LogoutRequest

from services import auth_service  

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register_user(
    payload: UserCreate, 
    db = Depends(get_db)
):
    return await auth_service.register_user(db=db, payload=payload)

@router.post("/signup", response_model=UserOut, status_code=201)
async def signup_user(
    payload: UserCreate, 
    db = Depends(get_db)
):
    """회원가입 엔드포인트 (register와 동일)"""
    return await auth_service.register_user(db=db, payload=payload)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: UserLoginRequest, 
    db = Depends(get_db)
):
    return await auth_service.login(db, user_id_or_email=payload.id_or_email, password=payload.password)

@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest, 
    db = Depends(get_db)
):
    return await auth_service.refresh_tokens(db, refresh_token=payload.refresh_token)

@router.post("/logout")
async def logout(payload: LogoutRequest):
    await auth_service.logout(refresh_token=payload.refresh_token)
    return {"ok": True}
