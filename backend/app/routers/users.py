from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..services import users_service
from ..utils.security import get_current_user


class UserPatchIn(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return user


@router.patch("/me")
async def patch_me(data: UserPatchIn, user=Depends(get_current_user)):
    return users_service.patch_me(user["id"], data.nickname, data.avatar_url)
