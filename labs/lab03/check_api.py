"""Перевірка API за сценаріями завдання 3.

Запуск (сервер уже працює на 127.0.0.1:8000):
    python -m labs.lab03.check_api
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://127.0.0.1:8000"
SUFFIX = str(int(time.time()))[-6:]


def call(method: str, path: str, body: object | None = None) -> tuple[int, object]:
    """Виконати HTTP-запит і повернути (код, тіло відповіді)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


def show(
    number: str, title: str, method: str, path: str, body: object = None
) -> object:
    """Виконати запит і надрукувати його та результат."""
    code, answer = call(method, path, body)
    print(f"\n[{number}] {title}")
    print(f"  {method} {path}")
    if body is not None:
        print(f"  тіло: {json.dumps(body, ensure_ascii=False)}")
    print(f"  -> HTTP {code}")
    if answer is not None:
        print(f"  відповідь: {json.dumps(answer, ensure_ascii=False)}")
    return answer


def count_records() -> int:
    """Кількість записів у базі."""
    return len(call("GET", "/records?limit=100")[1])  # type: ignore[arg-type]


def record(code: str, **changes: object) -> dict:
    """Коректне тіло запису з можливістю зіпсувати окремі поля."""
    base = {
        "code": code,
        "title": "Тестове вимірювання",
        "category_id": 1,
        "value": 72.5,
        "status": "new",
    }
    return {**base, **changes}


def main() -> None:
    print(f"=== Перевірка API (префікс кодів: {SUFFIX}) ===")

    show("2", "Перевірка доступності", "GET", "/ping")
    show("2", "Дані студента", "GET", "/student")
    show("2", "Список категорій", "GET", "/categories")

    created = show(
        "3", "Створення запису", "POST", "/records", record(f"V12-C{SUFFIX}")
    )
    rid = created["id"]  # type: ignore[index]
    show("3", "Читання запису", "GET", f"/records/{rid}")
    show(
        "3",
        "Повна заміна (PUT)",
        "PUT",
        f"/records/{rid}",
        record(
            f"V12-C{SUFFIX}", title="Оновлене вимірювання", value=91.0, status="done"
        ),
    )
    show("3", "Видалення запису", "DELETE", f"/records/{rid}")
    show("3", "Читання після видалення", "GET", f"/records/{rid}")

    show(
        "4",
        "Фільтр за категорією і статусом",
        "GET",
        "/records?category_id=1&status=new",
    )
    show(
        "4",
        "Фільтр min_value=85 + сторінка",
        "GET",
        "/records?min_value=85&limit=2&offset=1",
    )

    before = count_records()
    print(f"\n[5-6] Записів до некоректних запитів: {before}")
    bad_cases = {
        "від'ємне value": record(f"V12-A{SUFFIX}", value=-5),
        "value більше 100": record(f"V12-B{SUFFIX}", value=101),
        "порожній title": record(f"V12-D{SUFFIX}", title="   "),
        "недозволений status": record(f"V12-E{SUFFIX}", status="bad"),
        "value не число": record(f"V12-F{SUFFIX}", value="abc"),
    }
    for title, body in bad_cases.items():
        show("5-6", title, "POST", "/records", body)
    show("5", "limit=0", "GET", "/records?limit=0")
    print(f"  Записів після: {count_records()}")

    show("7", "Неіснуючий record_id", "GET", "/records/999999")
    show(
        "7",
        "Запис із неіснуючим category_id",
        "POST",
        "/records",
        record(f"V12-G{SUFFIX}", category_id=99),
    )

    show("8", "Повторний code", "POST", "/records", record("V12-01"))
    show("8", "Повторна назва категорії", "POST", "/categories", {"name": "logs"})

    show("9", "Видалення непорожньої категорії", "DELETE", "/categories/1")
    new_category = show(
        "9", "Нова порожня категорія", "POST", "/categories", {"name": f"tmp{SUFFIX}"}
    )
    show(
        "9",
        "Видалення порожньої категорії",
        "DELETE",
        f"/categories/{new_category['id']}",
    )  # type: ignore[index]

    show(
        "10",
        "Коректний пакет із двох записів",
        "POST",
        "/records/bulk",
        [record(f"V12-H{SUFFIX}"), record(f"V12-I{SUFFIX}", category_id=2)],
    )

    before = count_records()
    print(f"\n[11] Записів до пакета: {before}")
    show(
        "11",
        "Пакет: другий запис має code із бази",
        "POST",
        "/records/bulk",
        [record(f"V12-ROLLBACK{SUFFIX}"), record("V12-01", category_id=2)],
    )
    print(f"  Записів після: {count_records()}")
    found = call("GET", f"/records?q=ROLLBACK{SUFFIX}")[1]
    print(f"  Пошук коду першого елемента: {found}")

    before = count_records()
    print(f"\n[12] Записів до пакета: {before}")
    show(
        "12",
        "Пакет: другий запис має неіснуючу категорію",
        "POST",
        "/records/bulk",
        [record(f"V12-ROLLBACK{SUFFIX}"), record(f"V12-J{SUFFIX}", category_id=99)],
    )
    print(f"  Записів після: {count_records()}")
    found = call("GET", f"/records?q=ROLLBACK{SUFFIX}")[1]
    print(f"  Пошук коду першого елемента: {found}")

    injection = urllib.parse.quote("' OR 1=1 --")
    show("13", "Пошук із SQL-ін'єкцією", "GET", f"/records?q={injection}")
    print(f"  Записів у базі після: {count_records()}")


if __name__ == "__main__":
    main()
