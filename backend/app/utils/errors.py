from fastapi import HTTPException

from ..services.storage import new_uuid


def http_error(code: str, message: str, status: int = 400) -> HTTPException:
    trace_id = new_uuid()
    return HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": message, "trace_id": trace_id}},
    )
