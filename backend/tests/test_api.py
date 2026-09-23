import pytest
from fastapi.testclient import TestClient

import api.interviews as routes
from main import app


@pytest.fixture
def client(engine, monkeypatch):
    monkeypatch.setattr(routes, "get_engine", lambda: engine)
    monkeypatch.setattr(routes, "_samples_ready", False)
    return TestClient(app, raise_server_exceptions=False)


def test_demo_flow_end_to_end(client, llm):
    llm.scores = [9, 8, 7, 5, 8]
    created = client.post("/api/interviews/demo")
    assert created.status_code == 201
    iid = created.json()["id"]

    session = client.post(f"/api/interviews/{iid}/start").json()
    assert session["status"] == "in_progress"
    assert "evaluation" not in str(session) and "score" not in str(session)

    while session["status"] == "in_progress":
        q = session["current_question"]
        assert q["text"] == "How would you explain this concept to a teammate?"
        r = client.post(f"/api/interviews/{iid}/answer", json={"question_index": q["index"], "answer": "An answer"})
        assert r.status_code == 200, r.text
        session = r.json()

    report = client.get(f"/api/interviews/{iid}/report").json()
    assert report["report"]["questions_answered"] == 5
    assert len(report["turns"]) == 5
    assert report["turns"][0]["evaluation"]["score"] == 9


def test_dashboard_lists_samples(client):
    rows = client.get("/api/interviews").json()["interviews"]
    assert sum(1 for r in rows if r["is_sample"]) == 4
    assert {r["status"] for r in rows} == {"completed", "in_progress"}


def test_errors_are_safe_json(client, llm):
    assert client.get("/api/interviews/nope").json()["error"]["code"] == "not_found"

    bad = client.post("/api/interviews", json={"candidate_name": "", "role": "x"})
    assert bad.status_code == 422 and "candidate_name" in bad.json()["error"]["message"]

    unknown = client.post("/api/interviews", json={"candidate_name": "a", "role": "b", "focus_areas": ["frontend"]})
    assert unknown.status_code == 422

    iid = client.post("/api/interviews/demo").json()["id"]
    client.post(f"/api/interviews/{iid}/start")
    llm.fail_next = RuntimeError("secret internal detail")
    r = client.post(f"/api/interviews/{iid}/answer", json={"question_index": 0, "answer": "a"})
    assert r.status_code == 500
    assert "secret" not in r.text and r.json()["error"]["retryable"]


def test_report_requires_completion(client):
    iid = client.post("/api/interviews/demo").json()["id"]
    assert client.get(f"/api/interviews/{iid}/report").status_code == 422


def test_resume_rejects_non_pdf(client):
    r = client.post("/api/resume", files={"file": ("cv.txt", b"hello", "text/plain")})
    assert r.status_code == 422
