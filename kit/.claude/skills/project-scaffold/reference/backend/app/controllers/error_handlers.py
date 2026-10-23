from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import ConflictError, DomainError, NotFoundError, ValidationError

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    ValidationError: 422,
    NotFoundError: 404,
    ConflictError: 409,
}


def _status_for(error: DomainError) -> int:
    for error_type, status in STATUS_BY_ERROR.items():
        if isinstance(error, error_type):
            return status
    return 400


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(status_code=_status_for(error),
                            content={"error": {"code": error.code, "message": error.message}})
