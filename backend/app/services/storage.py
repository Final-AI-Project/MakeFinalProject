from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import BinaryIO, Tuple

from ..core.config import settings

# In-memory stores
_USERS_BY_ID: Dict[str, Dict[str, Any]] = {}
_USERS_BY_EMAIL: Dict[str, Dict[str, Any]] = {}
_PLANTS_BY_USER: Dict[str, List[Dict[str, Any]]] = {}


def new_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Users ---
def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    return _USERS_BY_ID.get(user_id)  # type: ignore[no-any-return]


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return _USERS_BY_EMAIL.get(email)  # type: ignore[no-any-return]


def add_user(user: Dict[str, Any]) -> Dict[str, Any]:
    _USERS_BY_ID[user["id"]] = user
    _USERS_BY_EMAIL[user["email"]] = user
    return user


def update_user(user_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    user = _USERS_BY_ID.get(user_id)
    if not user:
        return None
    user.update(fields)
    return user


# --- Plants ---
def list_plants(user_id: str) -> List[Dict[str, Any]]:
    return _PLANTS_BY_USER.get(user_id, [])


def add_plant(user_id: str, plant: Dict[str, Any]) -> Dict[str, Any]:
    _PLANTS_BY_USER.setdefault(user_id, [])
    _PLANTS_BY_USER[user_id].append(plant)
    # Keep newest first by created_at
    _PLANTS_BY_USER[user_id].sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return plant


def get_plant(user_id: str, plant_id: str) -> Optional[Dict[str, Any]]:
    for p in _PLANTS_BY_USER.get(user_id, []):
        if p["id"] == plant_id:
            return p
    return None


def update_plant(user_id: str, plant_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    plants = _PLANTS_BY_USER.get(user_id, [])
    for p in plants:
        if p["id"] == plant_id:
            p.update(fields)
            return p
    return None


def safe_ext(filename: str) -> str:
    name = (filename or "").lower()
    ext = Path(name).suffix
    if ext == ".jpeg":
        ext = ".jpg"
    return ext


def sniff_mime(header: bytes) -> str:
    # 간단 시그니처 검사
    if header.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "application/octet-stream"


def media_root_abs() -> Path:
    root = Path(settings.MEDIA_ROOT)
    if not root.is_absolute():
        # 프로젝트 루트(pland/) 기준 상대경로
        root = settings.ROOT_DIR / settings.MEDIA_ROOT
    return root


def build_rel_path(dt: datetime, uuid_str: str, ext: str) -> str:
    y = f"{dt.year:04d}"
    m = f"{dt.month:02d}"
    d = f"{dt.day:02d}"
    return f"{y}/{m}/{d}/{uuid_str}{ext}"


def ensure_dirs(rel_path: str) -> Path:
    base = media_root_abs()
    full = base / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    return full


def build_url(rel_path: str) -> str:
    prefix = settings.MEDIA_URL.rstrip("/")
    return f"{prefix}/{rel_path}".replace("\\", "/")


def rel_from_url(url: str) -> str:
    prefix = settings.MEDIA_URL.rstrip("/") + "/"
    if url.startswith(prefix):
        return url[len(prefix):]
    if url.startswith("/" + prefix):
        return url[len(prefix) + 1 :]
    return url.lstrip("/")


# ---------- I/O ----------
def save_file(fileobj: BinaryIO, rel_path: str, *, max_bytes: int) -> Tuple[Path, str]:
    """
    스트리밍 저장 + 용량 가드.
    초과 시 ValueError("too_large") → 전역 미들웨어가 413 변환.
    """
    full = ensure_dirs(rel_path)
    written = 0
    chunk_size = 1024 * 1024  # 1MB
    with open(full, "wb") as out:
        while True:
            chunk = fileobj.read(chunk_size)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                out.close()
                try:
                    os.remove(full)
                except FileNotFoundError:
                    pass
                raise ValueError("too_large")
            out.write(chunk)
    return full, build_url(rel_path)


def delete_file(rel_path: str) -> None:
    full = media_root_abs() / rel_path
    try:
        full.unlink()
    except FileNotFoundError:
        pass



### ========= CRUD까지 완전 구현 이후 아래 코드로 교체 (위는 DB 임시 대체용 storage)  ======== ###


# from __future__ import annotations

# from typing import BinaryIO, Tuple
# import os
# from pathlib import Path
# from datetime import datetime, timezone

# from core.config import settings


# # ---------- Small utils ----------
# def new_uuid() -> str:
#     import uuid
#     return str(uuid.uuid4())

# def utcnow_iso() -> str:
#     return datetime.now(timezone.utc).isoformat()

# def safe_ext(filename: str) -> str:
#     name = (filename or "").lower()
#     ext = Path(name).suffix
#     if ext == ".jpeg":
#         ext = ".jpg"
#     return ext

# def sniff_mime(header: bytes) -> str:
#     if header.startswith(b"\xFF\xD8\xFF"):
#         return "image/jpeg"
#     if header.startswith(b"\x89PNG\r\n\x1a\n"):
#         return "image/png"
#     return "application/octet-stream"


# # ---------- Path helpers ----------
# def media_root_abs() -> Path:
#     root = Path(settings.MEDIA_ROOT)
#     if not root.is_absolute():
#         root = settings.ROOT_DIR / settings.MEDIA_ROOT
#     return root

# def build_rel_path(dt: datetime, uuid_str: str, ext: str) -> str:
#     y = f"{dt.year:04d}"
#     m = f"{dt.month:02d}"
#     d = f"{dt.day:02d}"
#     return f"{y}/{m}/{d}/{uuid_str}{ext}"

# def ensure_dirs(rel_path: str) -> Path:
#     full = media_root_abs() / rel_path
#     full.parent.mkdir(parents=True, exist_ok=True)
#     return full

# def build_url(rel_path: str) -> str:
#     prefix = settings.MEDIA_URL.rstrip("/")
#     return f"{prefix}/{rel_path}".replace("\\", "/")

# def rel_from_url(url: str) -> str:
#     prefix = settings.MEDIA_URL.rstrip("/") + "/"
#     if url.startswith(prefix):
#         return url[len(prefix):]
#     if url.startswith("/" + prefix):
#         return url[len(prefix) + 1:]
#     return url.lstrip("/")


# # ---------- File I/O ----------
# def save_file(fileobj: BinaryIO, rel_path: str, *, max_bytes: int) -> Tuple[Path, str]:
#     """
#     스트리밍 저장 + 용량 가드.
#     초과 시 ValueError("too_large") 발생 → 상위에서 413으로 매핑.
#     """
#     full = ensure_dirs(rel_path)
#     written = 0
#     chunk_size = 1024 * 1024  # 1MB
#     with open(full, "wb") as out:
#         while True:
#             chunk = fileobj.read(chunk_size)
#             if not chunk:
#                 break
#             written += len(chunk)
#             if written > max_bytes:
#                 out.close()
#                 try:
#                     os.remove(full)
#                 except FileNotFoundError:
#                     pass
#                 raise ValueError("too_large")
#             out.write(chunk)
#     return full, build_url(rel_path)

# def delete_file(rel_path: str) -> None:
#     full = media_root_abs() / rel_path
#     try:
#         full.unlink()
#     except FileNotFoundError:
#         pass
