"""Маршрути ресурсу /categories."""

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])

CategoryId = Annotated[int, Path(gt=0, description="Ідентифікатор категорії")]


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
    operation_id="list_categories",
)
def list_categories() -> list[dict]:
    """Усі категорії за зростанням id."""
    return repository.list_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=HTTPStatus.CREATED,
    summary="Створити категорію",
    operation_id="create_category",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(category: CategoryCreate) -> dict:
    """Створити нову категорію."""
    return repository.create_category(category.name)


@router.delete(
    "/{category_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Видалити порожню категорію",
    operation_id="delete_category",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(category_id: CategoryId) -> None:
    """Видалити категорію, якщо в ній немає записів."""
    repository.delete_category(category_id)
