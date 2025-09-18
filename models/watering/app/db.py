# app/db.py
import aiomysql
from .config import settings

_pool = None

async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=settings.db_host, port=settings.db_port,
            user=settings.db_user, password=settings.db_pass,
            db=settings.db_name, autocommit=True, minsize=1, maxsize=5
        )

async def close_db_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

async def fetchrow(query: str, params: tuple = ()):
    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()

# 간단 레포 기능
async def get_plant_meta(plant_id: int):
    q = """
        SELECT p.id, p.name, p.theta_min_pct, p.pot_diameter_cm, p.pot_height_cm, p.media_type,
               l.id as location_id, l.name as location_name, l.lat, l.lon, l.is_indoor
        FROM plants p
        JOIN locations l ON l.id = p.location_id
        WHERE p.id = %s
    """
    return await fetchrow(q, (plant_id,))

async def get_latest_indoor_rh(location_id: int):
    q = """
      SELECT rh_pct, ts_ms
      FROM indoor_rh_logs
      WHERE location_id = %s
      ORDER BY ts_ms DESC LIMIT 1
    """
    row = await fetchrow(q, (location_id,))
    return row["rh_pct"] if row else None

async def insert_location(name: str, lat: float, lon: float, is_indoor: bool) -> int:
    await init_db_pool()
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO locations(name,lat,lon,is_indoor) VALUES(%s,%s,%s,%s)",
                (name, lat, lon, 1 if is_indoor else 0)
            )
            return cur.lastrowid

async def get_location_by_id(loc_id: int):
    return await fetchrow("SELECT * FROM locations WHERE id=%s", (loc_id,))