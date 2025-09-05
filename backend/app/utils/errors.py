from fastapi import HTTPException
from uuid import uuid4

def http_error(code: str, message: str, status: int = 400) -> HTTPException:

    return HTTPException(
        status_code=status,
        detail={"에러": {"code": code, "message": message, "trace_id": str(uuid4())}}
    )