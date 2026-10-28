"""Початкове заповнення бази даними з data/seed.json."""

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.database import get_connection, initialize_database
from labs.lab03.schemas import RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


class SeedCategory(BaseModel):
    """Категорія з JSON (id задається в файлі)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=40)


class SeedData(BaseModel):
    """Весь файл seed.json."""

    model_config = ConfigDict(extra="forbid")

    categories: list[SeedCategory]
    records: list[RecordCreate]


def load_seed(path: Path = SEED_PATH) -> SeedData:
    """Прочитати JSON і перевірити його ще до запису в базу."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    seed = SeedData.model_validate(raw)
    known_ids = {category.id for category in seed.categories}
    for record in seed.records:
        if record.category_id not in known_ids:
            raise ValueError(
                f"Запис {record.code}: категорії {record.category_id} немає в JSON"
            )
    return seed


def is_database_empty(connection: sqlite3.Connection) -> bool:
    """База порожня, якщо в обох таблицях немає рядків."""
    categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def seed_database() -> int:
    """Заповнити порожню базу. Повертає код завершення (0 — успіх)."""
    try:
        seed = load_seed()
    except (OSError, ValueError) as error:
        print(f"Початкові дані некоректні, базу не змінено: {error}")
        return 1

    initialize_database()
    with closing(get_connection()) as connection:
        if not is_database_empty(connection):
            print("База вже містить дані: заповнення пропущено, дублікатів немає.")
            return 0
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c.id, c.name) for c in seed.categories],
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status)"
                    " VALUES (?, ?, ?, ?, ?)",
                    [
                        (r.code, r.title, r.category_id, r.value, r.status)
                        for r in seed.records
                    ],
                )
        except sqlite3.Error as error:
            print(f"Помилка запису, усі зміни скасовано: {error}")
            return 1

    print(f"Додано категорій: {len(seed.categories)}, записів: {len(seed.records)}.")
    return 0


if __name__ == "__main__":
    sys.exit(seed_database())
