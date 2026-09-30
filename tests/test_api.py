from fastapi.testclient import TestClient

from app.main import create_app


def test_task_lifecycle_and_persistence(tmp_path):
    db = tmp_path / "tasks.db"
    with TestClient(create_app(db)) as client:
        created = client.post("/tasks", json={"title": "  Ship API  ", "priority": 5})
        assert created.status_code == 201
        task = created.json()
        assert task["title"] == "Ship API"
        assert created.headers["location"] == f"/tasks/{task['id']}"
        assert client.get(f"/tasks/{task['id']}").json()["status"] == "todo"
        changed = client.patch(f"/tasks/{task['id']}", json={"status": "done", "description": "Released"})
        assert changed.json()["description"] == "Released"
        assert client.get("/tasks", params={"status": "done"}).json()["total"] == 1
    with TestClient(create_app(db)) as client:
        assert client.get(f"/tasks/{task['id']}").json()["status"] == "done"
        assert client.delete(f"/tasks/{task['id']}").status_code == 204
        assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_validation_and_pagination(tmp_path):
    with TestClient(create_app(tmp_path / "tasks.db")) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.post("/tasks", json={"title": "   "}).status_code == 422
        assert client.post("/tasks", json={"title": "x", "priority": 9}).status_code == 422
        first = client.post("/tasks", json={"title": "First"}).json()
        client.post("/tasks", json={"title": "Second"})
        page = client.get("/tasks", params={"limit": 1, "offset": 1}).json()
        assert page["total"] == 2
        assert [item["id"] for item in page["items"]] == [first["id"]]
        assert client.patch(f"/tasks/{first['id']}", json={"title": None}).status_code == 422
        assert client.get("/tasks", params={"limit": 101}).status_code == 422
