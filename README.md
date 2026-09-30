# Task Ledger API

A compact, persistent REST service built with FastAPI and SQLite. It supports task creation, listing with status filters and pagination, partial updates, deletion, input validation, and automatic OpenAPI documentation. The project is deliberately small enough to inspect end to end while exercising real API design and database behavior.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API reference. The default SQLite file is `data/tasks.db`; set `TASK_DB_PATH` to another path if needed.

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Review pull request","priority":4,"due_date":"2026-10-15"}'
curl 'http://127.0.0.1:8000/tasks?status=todo&limit=10&offset=0'
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H 'Content-Type: application/json' -d '{"status":"done"}'
```

## API

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/health` | Database health check |
| `POST` | `/tasks` | Create a task (`201`, `Location` header) |
| `GET` | `/tasks` | Filter by status; paginate with `limit` and `offset` |
| `GET` | `/tasks/{id}` | Read one task |
| `PATCH` | `/tasks/{id}` | Update supplied fields only |
| `DELETE` | `/tasks/{id}` | Delete (`204`) |

Statuses are `todo`, `doing`, and `done`; priority is 1 to 5. Requests are checked by Pydantic and SQLite constraints. Database queries use parameters for user values. The tests use isolated temporary databases and cover CRUD, persistence across app instances, validation, and pagination:

```bash
pytest -q
```

## Scope

This is a local single-service reference implementation. It has no accounts, authentication, or multi-user authorization, so do not expose it as a public task service without adding those controls. SQLite is a good fit for this demo; a larger deployment would need migration tooling and operational monitoring.
