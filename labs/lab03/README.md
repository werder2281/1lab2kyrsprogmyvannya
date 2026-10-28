# Лабораторна робота №3 — FastAPI + SQLite (варіант 12)

Предметна область: облік вимірювань заповнення сховищ.
Категорії: `logs`, `backups`, `archive`. Поле `value` — частка зайнятого
простору у відсотках (0–100), поріг — 85.0.

## Встановлення

```bash
pip install fastapi uvicorn pydantic ruff
pip freeze > requirements.txt   # або вручну додайте перевірені версії
```

## Початкове заповнення

```bash
python -m labs.lab03.seed
```

Повторний запуск не змінює дані й не створює дублікатів.

## Запуск API

```bash
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V12-TEST","title":"Тестове вимірювання","category_id":1,"value":72.5,"status":"new"}'
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V12-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V12-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'
```
