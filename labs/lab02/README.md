# Лабораторна робота № 2 — Розробка консольних утиліт для задач кібербезпеки

**Дисципліна:** Програмування скриптовими мовами
**Студент:** Диблюк Сергій Віталійович, група КБ-207
**Варіант 12:** Аналізатор заголовків електронної пошти та фішингових індикаторів

## Встановлення залежностей

Усі команди виконуються з кореня репозиторію з активованим віртуальним середовищем.

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

## Структура файлів

```text
labs/
├── __init__.py
└── lab02/
    ├── __init__.py
    ├── main.py          # команди demo та analyze
    ├── task1.py         # Завдання 1: User, Admin, Session, AuditLog, UserAccount
    ├── task2.py         # Завдання 2: аналізатор заголовків пошти (варіант 12)
    ├── README.md
    └── data/
        ├── mail_headers.log          # вхідний дамп заголовків листів (6 листів)
        └── suspicious_keywords.txt   # словник стоп-слів
```

## Запуск

### Завдання 1 — демонстрація ООП

```powershell
python -m labs.lab02.main demo
```

Демо показує: створення користувача, валідацію email, невдалий і успішний вхід,
доступ через `__getitem__` (хеш пароля недоступний), права адміністратора,
завершення сеансу за таймаутом (900 с), вихід із системи та записи `AuditLog`.

### Завдання 2 — аналіз заголовків листів

```powershell
python -m labs.lab02.main analyze `
    --mail-log labs/lab02/data/mail_headers.log `
    --suspicious-keywords labs/lab02/data/suspicious_keywords.txt `
    --out-csv labs/lab02/data/phishing_report.csv
```

Режим налагодження та запуск без `main.py`:

```powershell
python -m labs.lab02.main analyze --mail-log labs/lab02/data/mail_headers.log --debug
python -m labs.lab02.task2 --mail-log labs/lab02/data/mail_headers.log
```

## Параметри CLI (analyze)

| Параметр | Обов'язковий | Опис |
|---|---|---|
| `--mail-log` | так | Файл із дампом заголовків листів (текст або JSON) |
| `--suspicious-keywords` | ні | Файл зі стоп-словами (по одному в рядку) |
| `--out-csv` | ні | Шлях до CSV-звіту |
| `--out-json` | ні | Шлях до JSON-звіту (за замовчуванням `labs/lab02/data/phishing_report.json`) |
| `--debug` | ні | Детальне логування (рівень DEBUG) |

## Вхідні дані

- `mail_headers.log` — текстовий файл, листи розділені рядком `--- MESSAGE ---`;
  поля: `From`, `Return-Path`, `Reply-To`, `Received`, `Subject`.
  Також підтримується JSON (список об'єктів з тими самими ключами).
- `suspicious_keywords.txt` — стоп-слова для теми листа, по одному в рядку.

## Оцінка ризику

| Індикатор | Бали |
|---|---|
| Домен `From` ≠ домен `Return-Path` | +35 |
| Домен `From` ≠ домен `Reply-To` (якщо немає розбіжності з `Return-Path`) | +25 |
| Кожне стоп-слово в темі | +15 |
| Кількість `Received` ≥ 4 | +20 |

Максимум — 100. Статус: ≥ 70 — `HIGH RISK`, 40–69 — `MEDIUM RISK`, інакше `LOW RISK`.
У консоль виводяться листи з оцінкою ≥ 40; у звіт — усі.

## Поведінка при помилках

- Немає файлу `--mail-log` → повідомлення `ERROR`, код завершення 1.
- Немає файлу зі словником → попередження `WARNING`, аналіз без стоп-слів.
- Жодного листа не розпізнано → попередження `WARNING`, код завершення 1.
- Помилка читання/запису файлів → повідомлення `ERROR`, код завершення 1.
- Без обов'язкового `--mail-log` argparse виводить довідку.

## Перевірка якості коду

```powershell
ruff check labs/lab02
ruff format --check labs/lab02
```
