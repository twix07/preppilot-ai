"""Resume Intelligence (E1): skills, summary, JD-match %, improvement suggestions.

Heuristic parts (skills, match %) are deterministic. Generative parts (summary,
suggestions) run live Claude when a key is present and fall back to deterministic
templates in mock mode so the feature works — and tests pass — for free.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import get_llm
from app.ai.prompts.analysis import resume_analysis_prompt
from app.ai.skills import compute_jd_match, extract_skills
from app.ai.state import parse_json_object
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.repositories.repositories import ResumeRepository
from app.services.jd_service import JDService
from app.services.resume_service import ResumeService

logger = get_logger("resume_intelligence")


class ResumeIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resumes = ResumeService(db)
        self.jds = JDService(db)
        self.resume_repo = ResumeRepository(db)

    async def analyze(self, user_id: str, resume_id: str, jd_id: str | None) -> dict:
        rid, resume_text = await self.resumes.get_owned_text(user_id, resume_id)
        if rid is None:
            raise NotFoundError("Resume not found.")
        _, jd_text = await self.jds.get_owned_text(user_id, jd_id)

        skills = extract_skills(resume_text)
        jd_match = compute_jd_match(resume_text, jd_text) if jd_text else None
        missing = jd_match["missing"] if jd_match else []

        summary, suggestions = await self._summary_and_suggestions(
            resume_text, jd_text, skills, missing
        )

        # Persist derived fields onto the resume row (E1 columns).
        resume = await self.resume_repo.get(rid)
        if resume is not None:
            resume.extracted_skills = skills
            resume.summary = summary
        await self.db.commit()

        return {
            "resume_id": rid,
            "summary": summary,
            "extracted_skills": skills,
            "jd_match": jd_match,
            "suggestions": suggestions,
        }

    async def _summary_and_suggestions(
        self, resume_text: str, jd_text: str, skills: list[str], missing: list[str]
    ) -> tuple[str, list[str]]:
        if not settings.llm_mock_mode:
            try:
                res = await get_llm().complete(
                    system="You are a concise, honest resume coach. Return strict JSON only.",
                    user=resume_analysis_prompt(resume_text, jd_text, skills, missing),
                    json_mode=True,
                    max_tokens=500,
                )
                parsed = parse_json_object(res.text)
                summary = str(parsed.get("summary", "")).strip()
                suggestions = [str(s) for s in parsed.get("suggestions", []) if s][:5]
                if summary and suggestions:
                    return summary, suggestions
            except Exception as exc:  # noqa: BLE001
                logger.warning("Resume analysis LLM failed, using template: %s", exc)
        return self._template_summary(skills), self._template_suggestions(missing)

    @staticmethod
    def _template_summary(skills: list[str]) -> str:
        top = ", ".join(skills[:5]) if skills else "a range of transferable skills"
        return (
            f"Candidate with demonstrated strengths in {top}. The resume shows relevant "
            f"project and leadership experience suitable for early-career roles."
        )

    @staticmethod
    def _template_suggestions(missing: list[str]) -> list[str]:
        tips: list[str] = []
        for skill in missing[:2]:
            tips.append(f"Add concrete evidence of \"{skill}\" — the target JD asks for it.")
        tips += [
            "Quantify impact in each bullet (numbers, %, scale) instead of listing duties.",
            "Lead every bullet with a strong action verb and the outcome.",
            "Prioritize role-relevant projects; trim the rest to keep it to one page.",
        ]
        return tips[:5]
