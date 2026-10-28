"""Параметризовані SQL-запити до таблиць categories і records."""

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection

Row = dict[str, Any]

RECORD_SELECT = """
    SELECT r.id, r.code, r.title, r.category_id,
           c.name AS category_name, r.value, r.status
    FROM records AS r
    JOIN categories AS c ON c.id = r.category_id
"""

INSERT_RECORD = """
    INSERT INTO records (code, title, category_id, value, status)
    VALUES (:code, :title, :category_id, :value, :status)
"""

UPDATE_RECORD = """
    UPDATE records
    SET code = :code, title = :title, category_id = :category_id,
        value = :value, status = :status
    WHERE id = :id
"""


class RepositoryError(Exception):
    """Базова помилка шару даних (не залежить від FastAPI)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(RepositoryError):
    """Запис або категорія не існує."""


class ConflictError(RepositoryError):
    """Порушення унікальності або спроба видалити непорожню категорію."""


def _connect() -> sqlite3.Connection:
    """З'єднання, де рядки доступні за назвами стовпців."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def _is_unique_violation(error: sqlite3.IntegrityError) -> bool:
    return "UNIQUE constraint failed" in str(error)


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _ensure_category(connection: sqlite3.Connection, category_id: int) -> None:
    if not _category_exists(connection, category_id):
        raise NotFoundError("Категорію не знайдено")


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> Row | None:
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    return dict(row) if row else None


# ---------- Категорії ----------


def list_categories() -> list[Row]:
    """Усі категорії за зростанням id."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def create_category(name: str) -> Row:
    """Створити категорію; дублікат назви дає ConflictError."""
    with closing(_connect()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
                return {"id": cursor.lastrowid, "name": name}
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Категорія з такою назвою вже існує") from error
            raise


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with closing(_connect()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
                deleted = cursor.rowcount > 0
        except sqlite3.IntegrityError as error:
            raise ConflictError(
                "Категорія містить записи, видалити її не можна"
            ) from error
    if not deleted:
        raise NotFoundError("Категорію не знайдено")


# ---------- Записи ----------


def get_record(record_id: int) -> Row:
    """Один запис разом із назвою категорії."""
    with closing(_connect()) as connection:
        record = _fetch_record(connection, record_id)
    if record is None:
        raise NotFoundError("Запис не знайдено")
    return record


def list_records(
    category_id: int | None,
    status: str | None,
    min_value: float | None,
    q: str | None,
    limit: int,
    offset: int,
) -> list[Row]:
    """Список записів: фільтри через AND, сортування за id, сторінки."""
    conditions: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    sql = RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(_connect()) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def _insert_record(connection: sqlite3.Connection, item: Row) -> int:
    _ensure_category(connection, item["category_id"])
    cursor = connection.execute(INSERT_RECORD, item)
    return int(cursor.lastrowid)


def create_record(item: Row) -> Row:
    """Створити один запис."""
    return create_records_bulk([item])[0]


def create_records_bulk(items: list[Row]) -> list[Row]:
    """Додати всі записи в одній транзакції: або всі, або жоден."""
    with closing(_connect()) as connection:
        try:
            with connection:
                new_ids = [_insert_record(connection, item) for item in items]
                records = [_fetch_record(connection, new_id) for new_id in new_ids]
            return [record for record in records if record is not None]
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Запис із таким code вже існує") from error
            raise


def replace_record(record_id: int, item: Row) -> Row:
    """Повністю замінити змінювані поля; id не змінюється."""
    with closing(_connect()) as connection:
        try:
            with connection:
                if _fetch_record(connection, record_id) is None:
                    raise NotFoundError("Запис не знайдено")
                _ensure_category(connection, item["category_id"])
                connection.execute(UPDATE_RECORD, {**item, "id": record_id})
                record = _fetch_record(connection, record_id)
        except sqlite3.IntegrityError as error:
            if _is_unique_violation(error):
                raise ConflictError("Запис із таким code вже існує") from error
            raise
    return record  # type: ignore[return-value]


def delete_record(record_id: int) -> None:
    """Видалити запис за id."""
    with closing(_connect()) as connection, connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        deleted = cursor.rowcount > 0
    if not deleted:
        raise NotFoundError("Запис не знайдено")
