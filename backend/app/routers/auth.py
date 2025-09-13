from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.schemas.user import UserCreate, UserOut

from services import auth_service  

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db=db, payload=payload)


@router.post("/login")
async def login(form: dict, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(
        db,
        user_id_or_email=form["id_or_email"],
        password=form["password"],
    )

@router.post("/refresh")
async def refresh(body: dict, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_tokens(db, refresh_token=body["refresh_token"])


@router.post("/logout")
async def logout(body: dict):
    await auth_service.logout(refresh_token=body["refresh_token"])
    return {"ok": True}
