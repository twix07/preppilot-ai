"""Integration test: the full core loop over the real API (mock LLM)."""
from __future__ import annotations

GOOD_ANSWER = (
    "Situation: our club had low attendance. Task: I owned the fix. Action: I redesigned "
    "the format and recruited 4 speakers. Result: attendance rose 60% because we matched "
    "topics to demand, which was the key tradeoff."
)


async def _play_full_session(auth_client, track: str) -> dict:
    start = await auth_client.post("/interview/start", json={"track": track})
    assert start.status_code == 201, start.text
    data = start.json()
    session_id = data["session_id"]
    qid = data["question"]["id"]
    last = None
    for _ in range(6):  # 3 questions x (main + follow-up)
        r = await auth_client.post(
            "/interview/answer",
            json={"session_id": session_id, "question_id": qid, "text": GOOD_ANSWER},
        )
        assert r.status_code == 200, r.text
        last = r.json()
        if last.get("state") == "completed":
            break
        qid = last["question"]["id"]
    return last


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["llm_mode"] == "mock"


async def test_requires_auth(client):
    r = await client.post("/interview/start", json={"track": "pm"})
    assert r.status_code == 401


async def test_full_interview_and_dashboard(auth_client):
    final = await _play_full_session(auth_client, "behavioral")
    assert final["state"] == "completed"
    assert "readiness" in final
    # feedback quotes the student's own words (core requirement)
    improvements = " ".join(final["feedback"]["improvements"]).lower()
    assert "situation" in improvements or "attendance" in improvements or '"' in improvements

    dash = await auth_client.get("/dashboard")
    assert dash.status_code == 200
    body = dash.json()
    assert body["readiness"]["session_count"] >= 1
    assert len(body["competencies"]) == 5
    assert len(body["trend"]) >= 1


async def test_answer_length_cap(auth_client):
    start = (await auth_client.post("/interview/start", json={"track": "pm"})).json()
    r = await auth_client.post(
        "/interview/answer",
        json={"session_id": start["session_id"], "question_id": start["question"]["id"],
              "text": "x" * 5000},
    )
    assert r.status_code in (400, 413, 422)


async def test_delete_my_data(auth_client):
    await _play_full_session(auth_client, "pm")
    r = await auth_client.delete("/user/data")
    assert r.status_code == 204
    # token now points at a deleted user
    r2 = await auth_client.get("/auth/me")
    assert r2.status_code == 401
