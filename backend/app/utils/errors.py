from __future__ import annotations
import http
import uuid

from fastapi import HTTPException
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException as FastAPIHTTPException
from starlette import status as http_status

# 에러 처리를 JSON 형태로 통일, 공통 예외 핸들러와 미들웨어 등록


def _trace_id() -> str:
    return str(uuid.uuid4())


def _format_error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message, "trace_id": _trace_id()}}


# 애플리케이션 예외
class AppError(FastAPIHTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
        self.app_code = code
        self.app_message = message

def err(status_code: int, code: str, message: str) -> AppError:
    return AppError(status_code, code, message)


# 도메인 예외
def http_error(code: str, message: str, status: int = 400) -> HTTPException:

    return HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": message, "trace_id": str(uuid4())}}
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_format_error(exc.app_code, exc.app_message),
        )

    @app.exception_handler(FastAPIHTTPException)
    async def handle_http_exc(request: Request, exc: FastAPIHTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            code = exc.detail.get("code", "ERROR")
            message = exc.detail.get("message", "unexpected error")
        else:
            code = "ERROR"
            message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_format_error(code, message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):

        # 기본 동작: 상세 내용 없이 BAD_REQUEST 응답
        # return JSONResponse(
        #     status_code=http_status.HTTP_400_BAD_REQUEST,
        #     content=_format_error("BAD_REQUEST", "invalid request"),
        # )

        # 개발 편의용: 상세 내용 포함
        return JSONResponse(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Invalid request",
                    "details": exc.errors(),
                    "trace_id": _trace_id(),
                }
            }
        )

    @app.middleware("http")
    async def too_large_guard(request: Request, call_next):
        try:
            return await call_next(request)
        except ValueError as e:
            if str(e) == "too_large":
                return JSONResponse(
                    status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content=_format_error("PAYLOAD_TOO_LARGE", "file too large"),
                )
            raise

