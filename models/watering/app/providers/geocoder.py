from typing import Optional, Tuple, Dict, Any
import httpx
from ..config import settings

class GeocodeResult(Dict[str, Any]):
    """lat, lon, address, provider 필드를 갖는 dict"""

class Geocoder:
    async def geocode(self, query: str) -> Optional[GeocodeResult]:
        raise NotImplementedError

# ---------------- Google Maps ----------------
class GoogleGeocoder(Geocoder):
    async def geocode(self, query: str) -> Optional[GeocodeResult]:
        if not settings.google_maps_api_key:
            return None
        params = {
            "address": query,
            "key": settings.google_maps_api_key,
            "language": settings.geocoder_language,
            "region": settings.geocoder_region,
            "components": f"country:{settings.geocoder_region}",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
            r.raise_for_status()
            data = r.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
        res = data["results"][0]
        loc = res["geometry"]["location"]
        return GeocodeResult(
            lat=float(loc["lat"]),
            lon=float(loc["lng"]),
            address=res.get("formatted_address", query),
            provider="GOOGLE",
            raw=res
        )

# ---------------- Kakao Local ----------------
class KakaoGeocoder(Geocoder):
    async def geocode(self, query: str) -> Optional[GeocodeResult]:
        if not settings.kakao_rest_api_key:
            return None
        headers = { "Authorization": f"KakaoAK {settings.kakao_rest_api_key}" }
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            # 1) 주소검색
            r = await client.get("https://dapi.kakao.com/v2/local/search/address.json", params={"query": query})
            if r.status_code == 200 and r.json().get("documents"):
                doc = r.json()["documents"][0]
                y, x = float(doc["y"]), float(doc["x"])
                addr = doc.get("address_name") or query
                return GeocodeResult(lat=y, lon=x, address=addr, provider="KAKAO", raw=doc)

            # 2) 키워드(POI) 검색 fallback
            r = await client.get("https://dapi.kakao.com/v2/local/search/keyword.json", params={"query": query})
            if r.status_code == 200 and r.json().get("documents"):
                doc = r.json()["documents"][0]
                y, x = float(doc["y"]), float(doc["x"])
                addr = doc.get("place_name") or query
                return GeocodeResult(lat=y, lon=x, address=addr, provider="KAKAO", raw=doc)

        return None

# ---------------- Nominatim (OpenStreetMap) ----------------
class NominatimGeocoder(Geocoder):
    async def geocode(self, query: str) -> Optional[GeocodeResult]:
        base = settings.nominatim_base.rstrip("/")
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "accept-language": settings.geocoder_language,
            "limit": 1
        }
        headers = {"User-Agent": "plant-care-eta/1.0 (contact: dev@example.com)"}  # Nominatim 정책 상 UA 필수
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            r = await client.get(f"{base}/search", params=params)
            if r.status_code != 200:
                return None
            arr = r.json()
        if not arr:
            return None
        res = arr[0]
        return GeocodeResult(
            lat=float(res["lat"]),
            lon=float(res["lon"]),
            address=res.get("display_name", query),
            provider="NOMINATIM",
            raw=res
        )

# ---------------- Factory ----------------
def get_geocoder() -> Geocoder:
    p = settings.geocoder_primary.upper()
    if p == "GOOGLE":
        return GoogleGeocoder()
    if p == "KAKAO":
        return KakaoGeocoder()
    return NominatimGeocoder()
