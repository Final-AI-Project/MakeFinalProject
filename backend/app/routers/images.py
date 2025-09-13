from __future__ import annotations

from typing import Optional, Literal, List, Dict, Any

from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, Path, Header, status
from pydantic import BaseModel
import jwt  # PyJWT
from jwt import InvalidTokenError

from core.config import settings
# from utils.errors import err
from services import image_service
from services.storage import safe_ext, sniff_mime

router = APIRouter(prefix="/plants", tags=["images"])


# -----------------------
# Pydantic I/O Models
# -----------------------
class ImageCreateMetaIn(BaseModel):
    type: Literal["profile", "diary", "general"] = "general"
    note: Optional[str] = None


class ImageOut(BaseModel):
    image_id: str
    plant_id: str
    url: str
    type: Literal["profile", "diary", "general"]
    uploaded_at: str


class ImageListOut(BaseModel):
    items: List[ImageOut]
    next_cursor: Optional[str] = None
    has_more: bool = False


# -----------------------
# Auth (JWT Access required)
# -----------------------
def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    기대 헤더: Authorization: Bearer <token>
    payload 내 'user_id' 필수
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        # raise err(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "missing bearer token")
        raise Exception("missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            options={"require": ["exp"], "verify_exp": True},
        )
    except InvalidTokenError:
        # raise err(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "invalid or expired token")
        raise Exception("invalid or expired token")
    user_id = payload.get("user_id")
    if not user_id:
        # raise err(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "token missing user_id")
        raise Exception("token missing user_id")
    return {"user_id": user_id}


# -----------------------
# Routes
# -----------------------
@router.post(
    "/{plant_id}/images",
    status_code=status.HTTP_201_CREATED,
    response_model=ImageOut,
)
async def upload_image(
    plant_id: str = Path(...),
    file: UploadFile = File(..., description="jpg/png, ≤ MAX_UPLOAD_MB"),
    type: Literal["profile", "diary", "general"] = Form("general"),
    note: Optional[str] = Form(None),
    user=Depends(get_current_user),
):
    # Ownership check (in-memory registry; 나중에 DB로 교체)
    image_service.assert_plant_owned(user["user_id"], plant_id)

    # Validate extension
    ext = safe_ext(file.filename or "")
    if ext not in (".jpg", ".jpeg", ".png"):
        # raise err(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_MEDIA_TYPE", "only jpg/png allowed")
        raise Exception("only jpg/png allowed")

    # Peek header for signature sniff
    await file.seek(0)
    header = await file.read(16)
    await file.seek(0)

    mime = sniff_mime(header)
    if mime not in ("image/jpeg", "image/png"):
        # raise err(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_MEDIA_TYPE", "invalid file type")
        raise Exception("invalid file type")

    # Extension ↔ signature cross check
    if mime == "image/jpeg" and ext not in (".jpg", ".jpeg"):
        # raise err(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_MEDIA_TYPE", "jpeg required")
        raise Exception("jpeg required")
    if mime == "image/png" and ext != ".png":
        # raise err(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_MEDIA_TYPE", "png required")
        raise Exception("png required")

    # Size guard & 저장은 서비스에서 처리 (413 on exceed)
    meta = await image_service.create_image(
        plant_id=plant_id,
        user_id=user["user_id"],
        upload=file,
        image_type=type,
        note=note,
        max_mb=settings.MAX_UPLOAD_MB,
    )
    return ImageOut(**meta)


@router.get(
    "/{plant_id}/images",
    response_model=ImageListOut,
)
async def list_images(
    plant_id: str,
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    image_service.assert_plant_owned(user["user_id"], plant_id)
    return await image_service.list_images(plant_id=plant_id, limit=limit, cursor=cursor)


@router.get(
    "/{plant_id}/images/{image_id}",
    response_model=ImageOut,
)
async def get_image(
    plant_id: str,
    image_id: str,
    user=Depends(get_current_user),
):
    image_service.assert_plant_owned(user["user_id"], plant_id)
    meta = await image_service.get_image(plant_id=plant_id, image_id=image_id)
    if not meta:
        raise Exception("image not found")
    return ImageOut(**meta)


@router.delete(
    "/{plant_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_image(
    plant_id: str,
    image_id: str,
    user=Depends(get_current_user),
):
    image_service.assert_plant_owned(user["user_id"], plant_id)
    deleted = await image_service.delete_image(plant_id=plant_id, image_id=image_id)
    if not deleted:
        raise Exception("image not found")
    return None
