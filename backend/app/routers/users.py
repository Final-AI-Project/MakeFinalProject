from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from backend.app.utils.security import get_current_user
from backend.app.services import users_service

router = APIRouter(prefix="/users", tags=["users"])


# ====== Schemas ======
class UserOut(BaseModel):
    id: str
    email: EmailStr
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserPatchIn(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


# ====== Routes ======
@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return users_service.get_me(current_user["id"])


@router.patch("/me", response_model=UserOut)
async def patch_me(body: UserPatchIn, current_user=Depends(get_current_user)):
    return users_service.patch_me(
        current_user["id"], nickname=body.nickname, avatar_url=body.avatar_url
    )
