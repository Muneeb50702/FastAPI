"""FastAPI task service with durable SQLite storage."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response, status

from .db import connection, initialize
from .schemas import Status, Task, TaskCreate, TaskPage, TaskUpdate


def create_app(db_path: Path | None = None) -> FastAPI:
    path = db_path or Path(os.environ.get("TASK_DB_PATH", "data/tasks.db"))
    initialize(path)
    app = FastAPI(title="Task Ledger API", version="0.1.0",
                  description="A small persistent task service with filtering and pagination.")

    def get_task(task_id: int) -> dict:
        with connection(path) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(row)

    @app.get("/health")
    def health() -> dict[str, str]:
        with connection(path) as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}

    @app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
    def create_task(payload: TaskCreate, response: Response) -> dict:
        values = payload.model_dump(mode="json")
        with connection(path) as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, status, priority, due_date) VALUES (?, ?, ?, ?, ?)",
                (values["title"], values["description"], values["status"],
                 values["priority"], values["due_date"]),
            )
            task_id = cursor.lastrowid
        response.headers["Location"] = f"/tasks/{task_id}"
        return get_task(task_id)

    @app.get("/tasks", response_model=TaskPage)
    def list_tasks(task_status: Status | None = Query(default=None, alias="status"),
                   limit: int = Query(default=20, ge=1, le=100),
                   offset: int = Query(default=0, ge=0)) -> dict:
        where = "WHERE status = ?" if task_status else ""
        params = (task_status,) if task_status else ()
        with connection(path) as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM tasks {where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM tasks {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
        return {"items": [dict(row) for row in rows], "total": total,
                "limit": limit, "offset": offset}

    @app.get("/tasks/{task_id}", response_model=Task)
    def read_task(task_id: int) -> dict:
        return get_task(task_id)

    @app.patch("/tasks/{task_id}", response_model=Task)
    def update_task(task_id: int, payload: TaskUpdate) -> dict:
        get_task(task_id)
        values = payload.model_dump(exclude_unset=True, mode="json")
        for key in ("title", "status", "priority"):
            if key in values and values[key] is None:
                raise HTTPException(status_code=422, detail=f"{key} cannot be null")
        if values:
            assignments = ", ".join(f"{key} = ?" for key in values)
            with connection(path) as conn:
                conn.execute(
                    f"UPDATE tasks SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
                    (*values.values(), task_id),
                )
        return get_task(task_id)

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(task_id: int) -> Response:
        with connection(path) as conn:
            result = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
