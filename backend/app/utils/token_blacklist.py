from typing import Set

# 블랙리스트 토큰 저장소
_BLACKLIST: Set[str] = set()

def add(jti: str) -> None:
    # 토큰을 블랙리스트에 추가
    _BLACKLIST.add(jti)

def contains(jti: str) -> bool:
    # 토큰이 블랙리스트에 있는지 확인
    return jti in _BLACKLIST
