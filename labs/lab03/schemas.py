"""Pydantic-моделі запитів і відповідей."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03 import config

Status = Literal["new", "in_progress", "done"]


class CategoryCreate(BaseModel):
    """Тіло запиту для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=40, examples=["logs"])


class CategoryRead(BaseModel):
    """Категорія у відповіді."""

    id: int
    name: str


class RecordCreate(BaseModel):
    """Тіло запиту для створення запису (без id)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=3, max_length=40, examples=["V12-09"])
    title: str = Field(
        min_length=3, max_length=120, examples=["Вимірювання сховища 09"]
    )
    category_id: int = Field(gt=0, examples=[1])
    value: float = Field(
        ge=config.VALUE_MIN,
        le=config.VALUE_MAX,
        allow_inf_nan=False,
        description="Зайнятий простір, %",
        examples=[72.5],
    )
    status: Status = Field(examples=["new"])


class RecordReplace(RecordCreate):
    """Тіло PUT: усі змінювані поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис у відповіді: змінювані поля, id та назва категорії."""

    id: int
    category_name: str
