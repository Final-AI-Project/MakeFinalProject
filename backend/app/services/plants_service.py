from typing import Any, Optional

from ..utils.errors import http_error
from ..utils.pagination import paginate
from .storage import plants, new_uuid, utcnow_iso


def create(user_id: str, data: Any) -> dict:
    plant = {
        "id": new_uuid(),
        "user_id": user_id,
        "nickname": data.nickname,
        "species_hint": getattr(data, "species_hint", None),
        "species": None,
        "planted_at": getattr(data, "planted_at", None),
        "location": getattr(data, "location", None),
        "created_at": utcnow_iso(),
    }
    plants.append(plant)
    return plant


def list(user_id: str, limit: int, cursor: Optional[str]) -> dict:
    user_plants = [p for p in plants if p["user_id"] == user_id]
    slice_items, next_cursor, has_more = paginate(user_plants, limit, cursor, lambda x: x["id"])
    return {"items": slice_items, "next_cursor": next_cursor, "has_more": has_more}


def get(user_id: str, plant_id: str) -> dict:
    for p in plants:
        if p["id"] == plant_id and p["user_id"] == user_id:
            return p
    raise http_error("RESOURCE_NOT_FOUND", "plant not found", 404)


def patch(user_id: str, plant_id: str, data: Any) -> dict:
    plant = None
    for p in plants:
        if p["id"] == plant_id and p["user_id"] == user_id:
            plant = p
            break
    if not plant:
        raise http_error("RESOURCE_NOT_FOUND", "plant not found", 404)
    if getattr(data, "nickname", None) is not None:
        plant["nickname"] = data.nickname
    if getattr(data, "location", None) is not None:
        plant["location"] = data.location
    return plant
