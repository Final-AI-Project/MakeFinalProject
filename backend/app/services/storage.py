# path: backend/app/services/storage.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

# In-memory stores
_USERS_BY_ID: Dict[str, Dict[str, Any]] = {}
_USERS_BY_EMAIL: Dict[str, Dict[str, Any]] = {}
_PLANTS_BY_USER: Dict[str, List[Dict[str, Any]]] = {}


def utcnow_iso() -> str:
    """ISO8601 with UTC offset, e.g., '2025-09-04T03:12:34.567890+00:00'"""
    return datetime.now(timezone.utc).isoformat()


def new_uuid() -> str:
    return str(uuid4())


# --- Users ---
def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    return _USERS_BY_ID.get(user_id)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return _USERS_BY_EMAIL.get(email)


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
    # Keep newest first by created_at (ISO8601 lexicographic works)
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
