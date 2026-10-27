from typing import List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from labs.lab03 import repository

app = FastAPI(
    title="Lab 03 REST API",
    description="API для управління категоріями та записами (SQLite + FastAPI)",
)


# ==========================================
# Pydantic Моделі (Schemas)
# ==========================================
class CategoryCreate(BaseModel):
  name: str = Field(..., example="logs")


class CategoryResponse(BaseModel):
  id: int
  name: str


class RecordCreate(BaseModel):
  code: str = Field(..., example="V12-01")
  title: str = Field(..., example="Вимірювання сховища 01")
  category_id: int = Field(..., example=1)
  value: float = Field(..., example=90.0)
  status: str = Field(..., example="new")


class RecordResponse(BaseModel):
  id: int
  code: str
  title: str
  category_id: int
  category_name: str
  value: float
  status: str


# ==========================================
# Endpoints: Categories
# ==========================================
@app.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="Отримати всі категорії",
)
def read_categories():
  return repository.get_all_categories()


@app.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Отримати категорію за ID",
)
def read_category(category_id: int):
  category = repository.get_category_by_id(category_id)
  if not category:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено"
    )
  return category


@app.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову категорію",
)
def create_category(category: CategoryCreate):
  return repository.create_category(category.name)


@app.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити категорію за ID",
)
def delete_category(category_id: int):
  try:
    success = repository.delete_category(category_id)
    if not success:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено"
      )
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# Endpoints: Records
# ==========================================
@app.get(
    "/records", response_model=List[RecordResponse], summary="Отримати всі записи"
)
def read_records():
  return repository.get_all_records()


@app.get(
    "/records/{record_id}",
    response_model=RecordResponse,
    summary="Отримати запис за ID",
)
def read_record(record_id: int):
  record = repository.get_record_by_id(record_id)
  if not record:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено"
    )
  return record


@app.post(
    "/records",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий запис",
)
def create_record(record: RecordCreate):
  return repository.create_record(
      code=record.code,
      title=record.title,
      category_id=record.category_id,
      value=record.value,
      status=record.status,
  )


@app.put(
    "/records/{record_id}",
    response_model=RecordResponse,
    summary="Оновити запис за ID",
)
def update_record(record_id: int, record: RecordCreate):
  updated_record = repository.update_record(
      record_id=record_id,
      code=record.code,
      title=record.title,
      category_id=record.category_id,
      value=record.value,
      status=record.status,
  )
  if not updated_record:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено"
    )
  return updated_record


@app.delete(
    "/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис за ID",
)
def delete_record(record_id: int):
  success = repository.delete_record(record_id)
  if not success:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено"
    )