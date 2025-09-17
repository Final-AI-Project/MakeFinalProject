from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import UploadFile, status

# from backend.app.utils.errors import err
# from backend.app.utils.pagination import paginate
from .storage import (
    ensure_dirs,
    new_uuid,
    utcnow_iso,
    save_file,
    build_rel_path,
    build_url,
    rel_from_url,
    delete_file,
    safe_ext,
)

# In-memory registries (DB 교체 예정)
_images: Dict[str, Dict[str, Any]] = {}  # image_id -> meta
_plant_owners: Dict[str, str] = {}       # plant_id -> owner_user_id


def assert_plant_owned(user_id: str, plant_id: str) -> None:
    """
    최초 접근 사용자를 소유자로 등록, 이후에는 동일 사용자만 접근 허용.
    """
    owner = _plant_owners.get(plant_id)
    if owner is None:
        _plant_owners[plant_id] = user_id
        return
    if owner != user_id:
        # raise err(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "not your plant")
        raise Exception("not your plant")  


async def create_image(
    plant_id: str,
    user_id: str,  # 예약: 소유권 확인용
    upload: UploadFile,
    image_type: str,
    note: Optional[str],
    max_mb: int,
) -> Dict[str, Any]:
    uid = new_uuid()
    now = datetime.now(timezone.utc)
    ext = safe_ext(upload.filename or "")
    if ext == ".jpeg":
        ext = ".jpg"

    rel_path = build_rel_path(now, uid, ext)
    ensure_dirs(rel_path)

    max_bytes = max_mb * 1024 * 1024
    await upload.seek(0)
    # save_file 내부에서 용량 초과 시 ValueError("too_large") 발생 (전역 미들웨어가 413 리턴)
    save_file(upload.file, rel_path, max_bytes=max_bytes)

    url = build_url(rel_path)
    meta = {
        "image_id": uid,
        "plant_id": plant_id,
        "url": url,
        "type": image_type,
        "note": note,
        "uploaded_at": utcnow_iso(),  # ISO8601 UTC
    }
    _images[uid] = meta
    return meta


async def list_images(plant_id: str, limit: int, cursor: Optional[str]) -> Dict[str, Any]:
    # Filter by plant
    items = [v for v in _images.values() if v["plant_id"] == plant_id]
    # 정렬: uploaded_at desc, image_id desc (ISO8601 문자열은 역순 정렬 시 최신이 먼저)
    items.sort(key=lambda x: (x["uploaded_at"], x["image_id"]), reverse=True)

    def key_fn(x):
        return (x["uploaded_at"], x["image_id"])

    # page_items, next_cursor, has_more = paginate(items, limit, cursor, key_fn=key_fn, desc=True)
    # return {
    #     "items": page_items,
    #     "next_cursor": next_cursor,
    #     "has_more": has_more,
    # }

# 임시
    return {
        "items": items[:limit],
        "next_cursor": None,
        "has_more": False,
    }


async def get_image(plant_id: str, image_id: str) -> Optional[Dict[str, Any]]:
    meta = _images.get(image_id)
    if meta and meta["plant_id"] == plant_id:
        return meta
    return None


async def delete_image(plant_id: str, image_id: str) -> bool:
    meta = _images.get(image_id)
    if not meta or meta["plant_id"] != plant_id:
        return False
    # 파일 제거
    rel = rel_from_url(meta["url"])
    delete_file(rel)
    # 메타 제거
    _images.pop(image_id, None)
    return True
