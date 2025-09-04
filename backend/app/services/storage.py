from datetime import datetime, timezone
import uuid

users: dict[str, dict] = {}
plants: list[dict] = []


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
