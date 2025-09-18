import json
import hashlib
from typing import Optional, Dict, Any
from .db import fetchrow, init_db_pool, _pool

def _hash(q: str) -> str:
    return hashlib.sha256(q.encode("utf-8")).hexdigest()

async def geocode_cache_get(query: str) -> Optional[Dict[str, Any]]:
    row = await fetchrow("SELECT payload_json FROM geocode_cache WHERE qhash=%s", (_hash(query),))
    if not row:
        return None
    raw = row["payload_json"]
    if isinstance(raw, (bytes, bytearray)): raw = raw.decode("utf-8")
    return json.loads(raw) if isinstance(raw, str) else raw

async def geocode_cache_put(query: str, payload: Dict[str, Any]):
    await init_db_pool()
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO geocode_cache(qhash, query, payload_json) VALUES(%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE payload_json=VALUES(payload_json)",
                (_hash(query), query, json.dumps(payload, ensure_ascii=False))
            )
