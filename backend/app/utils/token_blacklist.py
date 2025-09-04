_blacklist: set[str] = set()


def add(jti: str) -> None:
    _blacklist.add(jti)


def contains(jti: str | None) -> bool:
    if jti is None:
        return False
    return jti in _blacklist
