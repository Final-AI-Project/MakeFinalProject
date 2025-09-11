# 커서 페이지네이션 유틸리티 (ID 기반), (불필요시 삭제)

from __future__ import annotations

import base64
import json
from typing import Any, Tuple, Optional


def _b64encode(d: dict) -> str:
    raw = json.dumps(d, separators=(",", ":")).encode("utf-8")
    s = base64.urlsafe_b64encode(raw).decode("ascii")
    return s.rstrip("=")


def _b64decode(s: str) -> dict:
    pad = "=" * (-len(s) % 4)
    raw = base64.urlsafe_b64decode(s + pad)
    return json.loads(raw.decode("utf-8"))


def encode_id_cursor(last_id: int | None) -> str | None:
    if last_id is None:
        return None
    return _b64encode({"last_id": last_id})


def decode_id_cursor(cursor: str | None) -> Optional[int]:
    if not cursor:
        return None
    try:
        data = _b64decode(cursor)
        v = data.get("last_id")
        return int(v) if v is not None else None
    except Exception:
        return None


def page_window(items: list[Any], limit: int) -> Tuple[list[Any], bool]:
    """쿼리는 limit+1개를 가져오고, 여기서 has_more/next_cursor 결정을 보조."""
    has_more = len(items) > limit
    return (items[:limit], has_more)
