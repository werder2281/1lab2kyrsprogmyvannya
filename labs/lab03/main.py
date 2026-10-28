"""FastAPI-застосунок: облік вимірювань заповнення сховищ (варіант 12)."""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from labs.lab03 import config, repository
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared import student

logger = logging.getLogger(__name__)

DESCRIPTION = (
    f"{config.DOMAIN}. Категорії: тип сховища (logs, backups, archive). "
    f"Поле value — {config.UNIT_DESCRIPTION} (одиниця: {config.UNIT}, "
    f"від {config.VALUE_MIN:g} до {config.VALUE_MAX:g}). "
    f"Поріг: {config.THRESHOLD:g}%."
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Під час запуску створити відсутні таблиці, не чіпаючи дані."""
    initialize_database()
    yield


app = FastAPI(
    title="Lab 03: облік використання сховищ",
    description=DESCRIPTION,
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(repository.NotFoundError)
async def not_found_handler(
    _: Request, error: repository.NotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND, content={"detail": error.message}
    )


@app.exception_handler(repository.ConflictError)
async def conflict_handler(_: Request, error: repository.ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.CONFLICT, content={"detail": error.message}
    )


@app.exception_handler(sqlite3.Error)
async def database_error_handler(_: Request, error: sqlite3.Error) -> JSONResponse:
    """Технічні деталі лише в журнал, клієнту — загальне повідомлення."""
    logger.error("Помилка бази даних", exc_info=error)
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": "Внутрішня помилка сервера"},
    )


@app.get("/ping", summary="Перевірка доступності", operation_id="ping")
def ping() -> dict[str, str]:
    """Повертає {"status": "ok"}."""
    return {"status": "ok"}


@app.get("/student", summary="Дані студента", operation_id="get_student")
def get_student() -> dict[str, str | int]:
    """ПІБ, група та номер варіанта з shared/student.py."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
