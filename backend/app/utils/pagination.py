import base64
import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


def encode_cursor(last_id: Optional[str], extra: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if last_id is None and not extra:
        return None
    payload = {"last_id": last_id, "extra": extra or {}}
    raw = json.dumps(payload).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: Optional[str]) -> Dict[str, Any]:
    if not cursor:
        return {}
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        return json.loads(raw.decode())
    except Exception:
        return {}


def paginate(
    items: List[Any],
    limit: int,
    cursor_input: Optional[str],
    id_getter: Callable[[Any], str],
) -> Tuple[List[Any], Optional[str], bool]:
    data = decode_cursor(cursor_input)
    last_id = data.get("last_id")
    start = 0
    if last_id:
        for idx, item in enumerate(items):
            if id_getter(item) == last_id:
                start = idx + 1
                break
    slice_items = items[start : start + limit + 1]
    has_more = len(slice_items) > limit
    slice_items = slice_items[:limit]
    next_cursor = None
    if has_more and slice_items:
        next_cursor = encode_cursor(id_getter(slice_items[-1]), None)
    return slice_items, next_cursor, has_more
