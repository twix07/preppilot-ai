"""Interview orchestration — deterministic turn state machine over the 2-node graph.

Flow: 3 main questions, each followed by exactly one adaptive follow-up. A question is
evaluated once its follow-up is answered. The LLM never decides control flow — this
service does (spec: routing is deterministic code).
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.graph import run_graph
from app.ai.rubrics import COMPETENCY_ID_BY_KEY, COMPETENCY_NAME_BY_KEY, get_rubric
from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, PayloadTooLargeError
from app.models import Answer, AnswerScore, InterviewSession, Question
from app.models.interview_session import SESSION_COMPLETED, SESSION_IN_PROGRESS
from app.repositories.repositories import (
    AnswerRepository,
    QuestionRepository,
    SessionRepository,
)
from app.services.analytics_service import AnalyticsService
from app.services.jd_service import JDService
from app.services.resume_service import ResumeService
from app.services.scoring_service import update_readiness
from app.services.usage_service import UsageService

TOTAL_QUESTIONS = 3


class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sessions = SessionRepository(db)
        self.questions = QuestionRepository(db)
        self.answers = AnswerRepository(db)
        self.usage = UsageService(db)
        self.analytics = AnalyticsService(db)
        self.resumes = ResumeService(db)
        self.jds = JDService(db)

    # ---------- helpers ----------
    async def _load_context(self, user_id: str, session: InterviewSession) -> tuple[str, str]:
        _, resume_text = await self.resumes.get_owned_text(user_id, session.resume_id)
        _, jd_text = await self.jds.get_owned_text(user_id, session.jd_id)
        return resume_text, jd_text

    async def _run_node(self, user_id: str, state: dict) -> dict:
        await self.usage.check_llm_cap(user_id)
        result = await run_graph(state)
        tel = result.get("llm", {})
        await self.usage.record_llm_call(user_id, tel.get("cost_usd", 0.0))
        await self.analytics.log(
            user_id, "llm_call",
            {"mode": state.get("mode"), **{k: tel.get(k) for k in
             ("model", "input_tokens", "output_tokens", "latency_ms", "cost_usd", "mock")}},
        )
        return result

    def _owned_session(self, session: InterviewSession | None, user_id: str) -> InterviewSession:
        if session is None:
            raise NotFoundError("Interview session not found.")
        if session.user_id != user_id:
            raise ForbiddenError("You do not have access to that session.")
        return session

    # ---------- start ----------
    async def start(
        self, user_id: str, track: str, resume_id: str | None, jd_id: str | None
    ) -> dict:
        if track not in ("behavioral", "pm"):
            raise ConflictError("Unknown track.")
        await self.usage.check_interview_cap(user_id)

        rubric = get_rubric(track)
        planned = random.sample(rubric.question_bank, TOTAL_QUESTIONS)

        # Validate ownership of provided context up front.
        r_id, resume_text = await self.resumes.get_owned_text(user_id, resume_id)
        j_id, jd_text = await self.jds.get_owned_text(user_id, jd_id)

        session = InterviewSession(
            user_id=user_id, track=track, resume_id=r_id, jd_id=j_id,
            status=SESSION_IN_PROGRESS, started_at=datetime.now(timezone.utc),
            report={"planned": planned},
        )
        await self.sessions.add(session)

        state = {
            "mode": "interview", "phase": "question", "track": track,
            "resume_text": resume_text, "jd_text": jd_text,
            "question_number": 1, "main_question": planned[0],
        }
        result = await self._run_node(user_id, state)
        question = await self.questions.add(
            Question(session_id=session.id, order_index=1, text=result["interviewer_message"],
                     is_follow_up=False)
        )

        await self.usage.record_interview_start(user_id)
        await self.analytics.log(user_id, "interview_started", {"track": track})
        await self.db.commit()

        return {
            "session_id": session.id, "track": track, "state": "awaiting_answer",
            "question": self._question_dto(question),
            "progress": {"question": 1, "of": TOTAL_QUESTIONS},
        }

    # ---------- answer ----------
    async def submit_answer(
        self, user_id: str, session_id: str, question_id: str, text: str
    ) -> dict:
        text = (text or "").strip()
        if len(text) > settings.answer_char_cap:
            raise PayloadTooLargeError(
                f"Answer exceeds the {settings.answer_char_cap}-character limit."
            )

        session = self._owned_session(await self.sessions.get(session_id), user_id)
        if session.status != SESSION_IN_PROGRESS:
            raise ConflictError("This interview is already complete.")

        question = await self.questions.get(question_id)
        if question is None or question.session_id != session.id:
            raise NotFoundError("Question not found for this session.")
        if await self.answers.get_for_question(question_id) is not None:
            raise ConflictError("That question has already been answered.")

        await self.answers.add(
            Answer(question_id=question.id, session_id=session.id, text=text, char_count=len(text))
        )

        resume_text, jd_text = await self._load_context(user_id, session)

        if not question.is_follow_up:
            return await self._ask_follow_up(user_id, session, question, text, resume_text, jd_text)
        return await self._complete_question(user_id, session, question, resume_text, jd_text)

    async def _ask_follow_up(
        self, user_id: str, session: InterviewSession, main_q: Question,
        answer_text: str, resume_text: str, jd_text: str,
    ) -> dict:
        state = {
            "mode": "interview", "phase": "followup", "track": session.track,
            "resume_text": resume_text, "jd_text": jd_text,
            "main_question": main_q.text, "answer_text": answer_text,
        }
        result = await self._run_node(user_id, state)
        follow = await self.questions.add(
            Question(session_id=session.id, order_index=main_q.order_index,
                     text=result["interviewer_message"], is_follow_up=True,
                     parent_question_id=main_q.id)
        )
        await self.db.commit()
        return {
            "state": "awaiting_answer",
            "question": self._question_dto(follow),
            "progress": {"question": main_q.order_index, "of": TOTAL_QUESTIONS},
        }

    async def _complete_question(
        self, user_id: str, session: InterviewSession, follow_q: Question,
        resume_text: str, jd_text: str,
    ) -> dict:
        main_q = await self.questions.get(follow_q.parent_question_id)  # type: ignore[arg-type]
        main_answer = await self.answers.get_for_question(main_q.id)
        follow_answer = await self.answers.get_for_question(follow_q.id)
        combined = (main_answer.text if main_answer else "")
        if follow_answer:
            combined += f"\n\n[Follow-up] {follow_q.text}\n{follow_answer.text}"

        state = {
            "mode": "evaluate", "track": session.track,
            "resume_text": resume_text, "jd_text": jd_text,
            "eval_question": main_q.text, "eval_answer": combined,
        }
        result = await self._run_node(user_id, state)
        evaluation = result["evaluation"]
        feedback = await self._persist_evaluation(main_q, main_answer, evaluation)

        if main_q.order_index < TOTAL_QUESTIONS:
            return await self._ask_next_main(
                user_id, session, main_q.order_index + 1, resume_text, jd_text, feedback
            )
        return await self._finish_session(user_id, session, feedback)

    async def _persist_evaluation(self, main_q, main_answer, evaluation: dict) -> dict:
        scores = evaluation["scores"]
        rationales = evaluation.get("rationales", {})
        score_list = []
        for key, value in scores.items():
            await self.answers.add_score(
                AnswerScore(
                    answer_id=main_answer.id,
                    competency_id=COMPETENCY_ID_BY_KEY[key],
                    dimension=COMPETENCY_NAME_BY_KEY[key],
                    raw_score=int(value),
                    rationale=rationales.get(key, ""),
                )
            )
            score_list.append(
                {"competency": key, "name": COMPETENCY_NAME_BY_KEY[key],
                 "dimension": COMPETENCY_NAME_BY_KEY[key], "score": int(value)}
            )
        feedback = {
            "for_question_id": main_q.id,
            "scores": score_list,
            "improvements": evaluation.get("improvements", []),
            "recommendations": evaluation.get("recommendations", []),
        }
        main_answer.feedback = feedback
        return feedback

    async def _ask_next_main(
        self, user_id: str, session: InterviewSession, number: int,
        resume_text: str, jd_text: str, feedback: dict,
    ) -> dict:
        planned = (session.report or {}).get("planned", [])
        main_question = planned[number - 1] if number - 1 < len(planned) else \
            get_rubric(session.track).question_bank[number - 1]
        state = {
            "mode": "interview", "phase": "question", "track": session.track,
            "resume_text": resume_text, "jd_text": jd_text,
            "question_number": number, "main_question": main_question,
        }
        result = await self._run_node(user_id, state)
        question = await self.questions.add(
            Question(session_id=session.id, order_index=number,
                     text=result["interviewer_message"], is_follow_up=False)
        )
        await self.db.commit()
        return {
            "state": "awaiting_answer", "feedback": feedback,
            "question": self._question_dto(question),
            "progress": {"question": number, "of": TOTAL_QUESTIONS},
        }

    async def _finish_session(self, user_id: str, session: InterviewSession, feedback: dict) -> dict:
        session.status = SESSION_COMPLETED
        session.completed_at = datetime.now(timezone.utc)

        readiness = await update_readiness(self.db, user_id, session.track, session.id)
        session.report = {
            **(session.report or {}),
            "completed": True,
            "readiness": {
                "overall": readiness.overall, "band": readiness.band,
                "competency_breakdown": readiness.competency_breakdown,
            },
        }
        await self.analytics.log(
            user_id, "interview_completed",
            {"track": session.track, "overall": readiness.overall, "band": readiness.band},
        )
        await self.db.commit()
        return {
            "state": "completed", "feedback": feedback, "session_id": session.id,
            "readiness": {
                "overall": readiness.overall, "band": readiness.band,
                "session_count": readiness.session_count,
            },
        }

    # ---------- feedback trust metric ----------
    async def record_feedback_thumbs(
        self, user_id: str, session_id: str, question_id: str | None, helpful: bool
    ) -> None:
        self._owned_session(await self.sessions.get(session_id), user_id)
        await self.analytics.log(
            user_id, "feedback_thumbs",
            {"session_id": session_id, "question_id": question_id, "helpful": helpful},
        )
        await self.db.commit()

    # ---------- report ----------
    async def get_report(self, user_id: str, session_id: str) -> dict:
        session = self._owned_session(await self.sessions.get(session_id), user_id)
        questions = await self.questions.list_for_session(session.id)
        answers = {a.question_id: a for a in await self.answers.list_for_session(session.id)}
        items = []
        for q in questions:
            ans = answers.get(q.id)
            items.append({
                "question_id": q.id, "order_index": q.order_index,
                "is_follow_up": q.is_follow_up, "text": q.text,
                "answer": ans.text if ans else None,
                "feedback": ans.feedback if ans and ans.feedback else None,
            })
        return {
            "session_id": session.id, "track": session.track, "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "readiness": (session.report or {}).get("readiness"),
            "items": items,
        }

    @staticmethod
    def _question_dto(q: Question) -> dict:
        return {"id": q.id, "order_index": q.order_index, "is_follow_up": q.is_follow_up,
                "text": q.text}
