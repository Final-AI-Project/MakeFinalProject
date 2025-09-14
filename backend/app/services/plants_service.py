from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from ..services import storage
# from backend.app.utils.errors import http_error
# from backend.app.utils.pagination import paginate


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = storage.utcnow_iso()
    plant = {
        "id": storage.new_uuid(),
        "user_id": user_id,
        "nickname": data["nickname"],
        "species_hint": data.get("species_hint"),
        "planted_at": _iso(data.get("planted_at")),
        "location": data.get("location"),
        "created_at": now,
        "updated_at": now,
    }
    storage.add_plant(user_id, plant)
    return plant


# def list(user_id: str, limit: int, cursor: Optional[str]) -> Dict[str, Any]:
#     items = storage.list_plants(user_id)
#     slice_, next_cursor, has_more = paginate(
#         items, 
#         limit, 
#         cursor, 
#         id_getter=lambda p: p["id"]
#     )
#     return {"items": slice_, "next_cursor": next_cursor, "has_more": has_more}


def get(user_id: str, plant_id: str) -> Dict[str, Any]:
    plant = storage.get_plant(user_id, plant_id)
    if not plant:
        # raise http_error("RESOURCE_NOT_FOUND", "plant not found", status=404)
        return {"error": "plant not found"}
    return plant


def patch(user_id: str, plant_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    plant = storage.get_plant(user_id, plant_id)
    if not plant:
        # raise http_error("RESOURCE_NOT_FOUND", "plant not found", status=404)
        return {"error": "plant not found"}

    updates: Dict[str, Any] = {}
    if "nickname" in data and data["nickname"] is not None:
        updates["nickname"] = data["nickname"]
    if "location" in data and data["location"] is not None:
        updates["location"] = data["location"]
    if updates:
        updates["updated_at"] = storage.utcnow_iso()

    updated = storage.update_plant(user_id, plant_id, updates) or plant
    return updated
