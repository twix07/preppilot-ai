"""Job Intelligence (E2): required-skill extraction, resume comparison, company tips.

Company tips are generated ONLY from the JD text and optional user-pasted company
notes — never from external/scraped data — and are labeled as AI-generated from the
provided inputs.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import get_llm
from app.ai.prompts.analysis import company_tips_prompt
from app.ai.skills import compute_jd_match, extract_skills, jd_required_skills
from app.ai.state import parse_json_object
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.repositories.repositories import JDRepository
from app.services.resume_service import ResumeService

logger = get_logger("job_intelligence")


class JobIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jd_repo = JDRepository(db)
        self.resumes = ResumeService(db)

    async def analyze(self, user_id: str, jd_id: str, resume_id: str | None) -> dict:
        jd = await self.jd_repo.get(jd_id)
        if jd is None:
            raise NotFoundError("Job description not found.")
        if jd.user_id != user_id:
            raise ForbiddenError("You do not have access to that job description.")

        required = jd_required_skills(jd.raw_text)
        _, resume_text = await self.resumes.get_owned_text(user_id, resume_id)
        comparison = compute_jd_match(resume_text, jd.raw_text) if resume_text else None

        tips = await self._company_tips(jd.raw_text, jd.company_notes or "")

        jd.required_skills = required
        await self.db.commit()

        return {
            "jd_id": jd.id,
            "required_skills": required,
            "comparison": comparison,          # None if no resume provided
            "company_tips": tips,
            "ai_generated_from_your_inputs": True,
            "source_note": "Tips are generated only from your JD text and pasted notes — "
                           "no external company data is fetched or stored.",
        }

    async def _company_tips(self, jd_text: str, company_notes: str) -> list[str]:
        if not settings.llm_mock_mode:
            try:
                res = await get_llm().complete(
                    system="You generate interview prep tips ONLY from provided inputs. "
                           "Return strict JSON only.",
                    user=company_tips_prompt(jd_text, company_notes),
                    json_mode=True,
                    max_tokens=400,
                )
                parsed = parse_json_object(res.text)
                tips = [str(t) for t in parsed.get("tips", []) if t][:5]
                if tips:
                    return tips
            except Exception as exc:  # noqa: BLE001
                logger.warning("Company tips LLM failed, using template: %s", exc)
        return self._template_tips(jd_text, company_notes)

    @staticmethod
    def _template_tips(jd_text: str, company_notes: str) -> list[str]:
        skills = extract_skills(jd_text)
        tips: list[str] = []
        for skill in skills[:3]:
            tips.append(f"The JD emphasizes \"{skill}\" — prepare a specific story demonstrating it.")
        if company_notes.strip():
            snippet = company_notes.strip()[:80]
            tips.append(f"From your notes (\"{snippet}\"), prepare to connect your experience to it.")
        tips += [
            "Map each of your top projects to a requirement in this JD.",
            "Prepare one thoughtful question about the team's priorities based on the JD.",
        ]
        return tips[:5]
