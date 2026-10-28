"""Маршрути ресурсу /records."""

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Body, Path, Query

from labs.lab03 import config, repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, Status

router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]

NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Запис із таким code вже існує"}}


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
    operation_id="list_records",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status: Annotated[
        Status | None, Query(description="Лише записи з цим статусом")
    ] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=config.VALUE_MIN,
            le=config.VALUE_MAX,
            allow_inf_nan=False,
            description="Мінімальне значення value (у відсотках)",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title (з урахуванням регістру)",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимум записів")] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки записів пропустити")] = 0,
) -> list[dict]:
    """Фільтри поєднуються через AND, сортування за id."""
    return repository.list_records(category_id, status, min_value, q, limit, offset)


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=HTTPStatus.CREATED,
    summary="Пакетне створення записів",
    operation_id="create_records_bulk",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(
    records: Annotated[
        list[RecordCreate],
        Body(min_length=1, max_length=config.MAX_BATCH_SIZE),
    ],
) -> list[dict]:
    """Усі записи зберігаються в одній транзакції або не зберігається жоден."""
    return repository.create_records_bulk([r.model_dump() for r in records])


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Один запис",
    operation_id="get_record",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId) -> dict:
    """Запис за id разом із назвою категорії."""
    return repository.get_record(record_id)


@router.post(
    "",
    response_model=RecordRead,
    status_code=HTTPStatus.CREATED,
    summary="Створити запис",
    operation_id="create_record",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(record: RecordCreate) -> dict:
    """Створити запис; id задає база."""
    return repository.create_record(record.model_dump())


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Замінити запис",
    operation_id="replace_record",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_record(record_id: RecordId, record: RecordReplace) -> dict:
    """Повна заміна всіх змінюваних полів."""
    return repository.replace_record(record_id, record.model_dump())


@router.delete(
    "/{record_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Видалити запис",
    operation_id="delete_record",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId) -> None:
    """Видалити запис за id."""
    repository.delete_record(record_id)
