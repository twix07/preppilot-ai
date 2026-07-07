"""Integration tests for Resume Intelligence (E1), Job Intelligence (E2), feedback thumbs."""
from __future__ import annotations

RESUME = (
    "Product enthusiast. Led a 300-member club. Skilled in SQL, product management, "
    "stakeholder management, and data analysis. Ran A/B testing on onboarding."
)
JD = (
    "Seeking an APM with product management, prioritization, A/B testing, SQL, and "
    "machine learning experience. Strong communication required."
)


async def _seed_resume_and_jd(auth_client):
    r = await auth_client.post("/resume/upload", json={"raw_text": RESUME})
    assert r.status_code == 201, r.text
    j = await auth_client.post("/jd/upload", json={"raw_text": JD, "company_notes": "Fast-paced fintech."})
    assert j.status_code == 201, j.text
    return r.json()["id"], j.json()["id"]


async def test_resume_analyze(auth_client):
    resume_id, jd_id = await _seed_resume_and_jd(auth_client)
    res = await auth_client.post("/resume/analyze", json={"resume_id": resume_id, "jd_id": jd_id})
    assert res.status_code == 200, res.text
    body = res.json()
    assert "sql" in body["extracted_skills"]
    assert body["summary"]
    assert 0 <= body["jd_match"]["percent"] <= 100
    assert "machine learning" in body["jd_match"]["missing"]  # in JD, not resume
    assert "ATS" in body["jd_match"]["caveat"]
    assert len(body["suggestions"]) >= 2


async def test_jd_analyze_with_company_tips(auth_client):
    resume_id, jd_id = await _seed_resume_and_jd(auth_client)
    res = await auth_client.post("/jd/analyze", json={"jd_id": jd_id, "resume_id": resume_id})
    assert res.status_code == 200, res.text
    body = res.json()
    assert "product management" in body["required_skills"]
    assert body["ai_generated_from_your_inputs"] is True
    assert len(body["company_tips"]) >= 2
    assert body["comparison"]["percent"] is not None


async def test_feedback_thumbs_recorded(auth_client):
    # need a session id — start one
    start = (await auth_client.post("/interview/start", json={"track": "pm"})).json()
    res = await auth_client.post(
        "/interview/feedback/thumbs",
        json={"session_id": start["session_id"], "helpful": True},
    )
    assert res.status_code == 202
    assert res.json()["recorded"] is True


async def test_analyze_rejects_other_users_resume(auth_client):
    resume_id, _ = await _seed_resume_and_jd(auth_client)
    # A different user (fresh token) must not be able to analyze user 1's resume.
    other = await auth_client.post("/auth/dev-login", json={"email": "other@test.io", "name": "Other"})
    other_token = other.json()["access_token"]
    r = await auth_client.post(
        "/resume/analyze",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert r.status_code == 403


async def test_analyze_requires_auth(client):
    r = await client.post("/resume/analyze", json={"resume_id": "x"}, headers={"Authorization": "Bearer bad"})
    assert r.status_code == 401
