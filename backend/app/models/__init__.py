"""SQLAlchemy models. Importing this package registers all tables on the metadata."""
from app.models.analytics import AnalyticsEvent
from app.models.answer import Answer, AnswerScore
from app.models.competency import Competency
from app.models.interview_session import InterviewSession
from app.models.job_description import JobDescription
from app.models.question import Question
from app.models.readiness_score import ReadinessScore
from app.models.resume import Resume
from app.models.usage import UsageCounter
from app.models.user import User

__all__ = [
    "AnalyticsEvent",
    "Answer",
    "AnswerScore",
    "Competency",
    "InterviewSession",
    "JobDescription",
    "Question",
    "ReadinessScore",
    "Resume",
    "UsageCounter",
    "User",
]
