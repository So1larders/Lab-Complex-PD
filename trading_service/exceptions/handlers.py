"""
Глобальна обробка винятків — аналог @ControllerAdvice у Spring.
Єдиний формат відповіді про помилку: timestamp, status, message, path.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone


# ─── Custom exception classes ────────────────────────────────────────────────

class NotFoundError(Exception):
    """404 — ресурс не знайдено."""
    def __init__(self, entity: str, id: int):
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} з id={id} не знайдено")


class ConflictError(Exception):
    """409 — конфлікт (наприклад, дублювання унікального поля)."""
    def __init__(self, message: str):
        super().__init__(message)


class BusinessLogicError(Exception):
    """422 — порушення бізнес-правил (наприклад, продаж більше ніж є)."""
    def __init__(self, message: str):
        super().__init__(message)


# ─── Єдиний формат помилки ───────────────────────────────────────────────────

def _error_body(request: Request, status: int, message: str, errors: list = None) -> dict:
    """
    Стандартний формат відповіді про помилку.
    Відповідає вимозі лаб. роботи: timestamp, status, message, path.
    """
    body = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status":    status,
        "message":   message,
        "path":      str(request.url.path),
    }
    if errors:
        body["errors"] = errors
    return body


# ─── Реєстрація обробників ────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """
    Реєструє всі обробники винятків.
    Аналог методів, анотованих @ExceptionHandler всередині @ControllerAdvice.
    """

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content=_error_body(request, 404, str(exc)),
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=409,
            content=_error_body(request, 409, str(exc)),
        )

    @app.exception_handler(BusinessLogicError)
    async def business_error_handler(request: Request, exc: BusinessLogicError):
        return JSONResponse(
            status_code=422,
            content=_error_body(request, 422, str(exc)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        return JSONResponse(
            status_code=422,
            content=_error_body(
                request, 422,
                "Помилка валідації вхідних даних",
                errors,
            ),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_body(request, 500, "Внутрішня помилка сервера"),
        )
