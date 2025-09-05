import base64
import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


def encode_cursor(last_id: Optional[str], extra: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if not last_id:
        return None
    data = {"last_id": last_id}
    if extra:
        # 타입 불일치 추론 오류 (추후 수정 예정)
        data["extra"] = extra
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: Optional[str]) -> Dict[str, Any]:
    if not cursor:
        return {}
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def paginate(
    items: List[Any],
    limit: int,
    cursor_input: Optional[str],
    id_getter: Callable[[Any], str],
) -> Tuple[List[Any], Optional[str], bool]:
    """
    커서 기반 페이지네이션
    - items: 이미 정렬된 항목 (예: 최신 항목 먼저)
    - limit: 반환할 최대 항목 수 (cap >=1)
    - cursor_input: 인코딩된 커서 문자열 또는 None
    - id_getter: 항목에서 고유 ID를 가져오는 함수
    """
    limit = max(1, min(int(limit or 10), 100))
    decoded = decode_cursor(cursor_input)
    last_id = decoded.get("last_id")

    start_idx = 0
    if last_id:
        for i, it in enumerate(items):
            if id_getter(it) == last_id:
                start_idx = i + 1
                break

    slice_ = items[start_idx : start_idx + limit]
    has_more = (start_idx + limit) < len(items)
    next_cursor = encode_cursor(id_getter(slice_[-1]) if slice_ and has_more else None, None)
    return slice_, next_cursor, has_more
