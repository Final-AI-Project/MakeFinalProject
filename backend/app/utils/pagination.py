from __future__ import annotations

import base64
import json
from typing import Any, Callable, List, Optional, Tuple


def _b64encode(data: dict) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    s = base64.urlsafe_b64encode(raw).decode("ascii")
    return s.rstrip("=")


def _b64decode(s: str) -> dict:
    pad = "=" * (-len(s) % 4)
    raw = base64.urlsafe_b64decode(s + pad)
    return json.loads(raw.decode("utf-8"))


def encode_cursor(value: dict) -> str:
    return _b64encode(value)


def decode_cursor(cursor: Optional[str]) -> Optional[dict]:
    if not cursor:
        return None
    try:
        return _b64decode(cursor)
    except Exception:
        return None


def paginate(
    items: List[Any],
    limit: int,
    cursor: Optional[str],
    *,
    key_fn: Callable[[Any], Any] | None = None,   # ← 기본 None
    id_getter: Callable[[Any], Any] | None = None,
    desc: bool = True,
) -> Tuple[List[Any], Optional[str], bool]:
    ...

    """
    이미 정렬된 items 에 대해 커서 기반 페이지네이션.
    cursor 형식: {"k": [uploaded_at, image_id]}
    """
    # items 는 이미 desc 정렬 가정
    seek = decode_cursor(cursor)
    start_idx = 0

    if seek is not None and "k" in seek:
        sk = seek["k"]
        # tuple 비교 통일
        if not isinstance(sk, (list, tuple)):
            sk = [sk]
        sk = tuple(sk)

        def cmp_tuple(a, b):
            # a, b 둘 다 tuple
            return (a > b) - (a < b)

        # desc 정렬에서 "sk 바로 다음" 인덱스 찾기
        for i, it in enumerate(items):
            k = key_fn(it)
            if not isinstance(k, (list, tuple)):
                k = (k,)
            k = tuple(k)
            # desc: k < sk 이면, sk 이후(다음 페이지 시작점)
            if cmp_tuple(k, sk) < 0:
                start_idx = i
                break
        else:
            # 끝을 넘어감
            return [], None, False

    page = items[start_idx : start_idx + limit]
    has_more = (start_idx + limit) < len(items)
    next_cursor = None
    if has_more and page:
        last = page[-1]
        lk = key_fn(last)
        if not isinstance(lk, (list, tuple)):
            lk = (lk,)
        next_cursor = encode_cursor({"k": list(lk)})
    return page, next_cursor, has_more