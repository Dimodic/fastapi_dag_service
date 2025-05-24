# FastAPI DAG service

Лёгкий REST‑API для хранения ориентированных ацикличных графов (DAG).

## Общие принципы

* **FastAPI + SQLAlchemy + PostgreSQL** в Docker‑Compose.
* Три таблицы: `graphs`, `nodes`, `edges` (внешние ключи + ON DELETE CASCADE).
* Валидация на уровне API (Pydantic) и БД (уникальные и внешние ключи).
* Обнаружение циклов выполняется в памяти до записи в БД.

## Запуск сервиса

```bash
docker compose up --build        # API: http://localhost:8080
```

| Переменная    | Значение                                         |
| ------------- | ------------------------------------------------ |
| DATABASE\_URL | postgresql://postgres\:postgres\@db:5432/graphdb |

## Запуск тестов

```bash
docker compose run --rm app pytest -q
```

---

### Мини‑API

| Метод  | URL                                      | Действие         |
| ------ | ---------------------------------------- | ---------------- |
| POST   | /api/graph/                              | создать граф     |
| GET    | /api/graph/{id}                          | получить граф    |
| GET    | /api/graph/{id}/adjacency\_list          | список смежности |
| GET    | /api/graph/{id}/reverse\_adjacency\_list | обратный список  |
| DELETE | /api/graph/{id}/node/{name}              | удалить узел     |
