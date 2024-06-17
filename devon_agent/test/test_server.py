# client = TestClient(app)
import threading

import httpx
import uvicorn
from fastapi.testclient import TestClient

from devon_agent.server import app

app.persist = False

threading.Thread(target=lambda: uvicorn.run(app), daemon=True).start()

client = httpx.Client(base_url="http://127.0.0.1:8000")


def test_server_start():
    response = client.get("/")
    assert response.status_code == 200


def test_session_CRUD():
    name = "test_session"
    response = client.get("/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 0

    response = client.post(
        f"/sessions/{name}?path=.",
        json={"model": "claude-opus"},
    )
    assert response.status_code == 200
    print(response.json())
    print("created")
    response = client.patch(f"/sessions/{name}/start")
    print(response.json())
    assert response.status_code == 200

    print("started")

    events_pre = client.get(f"/sessions/{name}/events").json()

    # pause
    response = client.patch(f"/sessions/{name}/pause")
    assert response.status_code == 200

    status = client.get(f"/sessions/{name}/status").json()
    assert status == "paused"

    events = client.get(f"/sessions/{name}/events").json()

    assert response.status_code == 200

    assert events == events_pre

    # resume
    response = client.patch(f"/sessions/{name}/start")
    assert response.status_code == 200

    status = client.get(f"/sessions/{name}/status").json()
    assert status == "running"

    response = client.post(
        f"sessions/{name}/event",
        json={
            "type": "git",
            "content": "commit",
            "producer": "git",
            "consumer": "devon",
        },
    )

    assert response.status_code == 200

    pre_reset_events = client.get(f"/sessions/{name}/events").json()

    assert len(pre_reset_events) == len(events) + 1

    response = client.patch(f"/sessions/{name}/reset")
    assert response.status_code == 200

    events_post_reset = client.get(f"/sessions/{name}/events").json()

    # accomodate git events upon setup
    assert len(events_post_reset) == len(events)

    status = client.get(f"/sessions/{name}/status").json()
    assert status == "paused"

    response = client.patch(f"/sessions/{name}/start")
    assert response.status_code == 200

    status = client.get(f"/sessions/{name}/status").json()
    assert status == "running"

    print("test ended")
