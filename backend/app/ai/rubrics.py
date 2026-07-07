"""The reusable core: competencies, per-track rubrics, question banks, and weights.

Everything about a track is data in this one file. Adding a new track (V2) is a
single dict entry — no flow, prompt, or scoring code changes. Both the prompt
builder and the scoring service read from here (single source of truth).

Readiness formula weights are documented in docs/01-PRD.md §6 and README.
"""
from __future__ import annotations

from dataclasses import dataclass

# ---- Tracks ----
TRACK_BEHAVIORAL = "behavioral"
TRACK_PM = "pm"
TRACKS = (TRACK_BEHAVIORAL, TRACK_PM)

# ---- Shared competencies (stable ids used as competencies.id) ----
COMPETENCIES: list[dict] = [
    {"id": 1, "key": "communication", "name": "Communication",
     "description": "Clear, concise, well-organized delivery; easy to follow."},
    {"id": 2, "key": "structure", "name": "Structure",
     "description": "Uses a logical framework (STAR / SCQA / MECE); no rambling."},
    {"id": 3, "key": "depth", "name": "Depth / Role-Knowledge",
     "description": "Specific, role-relevant detail; demonstrates real understanding."},
    {"id": 4, "key": "problem_solving", "name": "Problem-Solving",
     "description": "Sound reasoning, tradeoffs, and justified decisions."},
    {"id": 5, "key": "behavioral_star", "name": "Behavioral / STAR",
     "description": "Situation, Task, Action, Result — with ownership and impact."},
]
COMPETENCY_KEYS = [c["key"] for c in COMPETENCIES]
COMPETENCY_ID_BY_KEY = {c["key"]: c["id"] for c in COMPETENCIES}
COMPETENCY_NAME_BY_KEY = {c["key"]: c["name"] for c in COMPETENCIES}


@dataclass(frozen=True)
class TrackRubric:
    key: str
    label: str
    persona: str                       # who the interviewer is, for the system prompt
    weights: dict[str, float]          # competency_key -> weight (sums to 1.0)
    anchors: dict[str, str]            # competency_key -> "what a 5 looks like" for THIS track
    question_bank: list[str]


BEHAVIORAL = TrackRubric(
    key=TRACK_BEHAVIORAL,
    label="Behavioral",
    persona="a warm but rigorous behavioral interviewer at a top company",
    weights={
        "communication": 0.20,
        "structure": 0.20,
        "depth": 0.15,
        "problem_solving": 0.15,
        "behavioral_star": 0.30,
    },
    anchors={
        "communication": "Concise and confident; no filler; the story is easy to follow.",
        "structure": "Clean STAR arc — sets context, then task, action, result, in order.",
        "depth": "Concrete, first-person detail ('I did X'), not vague team-level generalities.",
        "problem_solving": "Shows judgement under constraints and reflects on what they'd change.",
        "behavioral_star": "Complete STAR with a quantified Result and clear personal ownership.",
    },
    question_bank=[
        "Tell me about a time you led a team without formal authority.",
        "Describe a situation where you had to resolve a conflict within a group.",
        "Tell me about a time you failed and what you learned.",
        "Describe a time you had to persuade someone who disagreed with you.",
        "Tell me about a time you had to deliver under a tight deadline.",
        "Describe a moment you took ownership of a problem no one else would.",
    ],
)

PM = TrackRubric(
    key=TRACK_PM,
    label="Product Management",
    persona="a senior product manager running a product-sense interview",
    weights={
        "communication": 0.20,
        "structure": 0.25,
        "depth": 0.20,
        "problem_solving": 0.25,
        "behavioral_star": 0.10,
    },
    anchors={
        "communication": "Crisp articulation of the problem, approach, and recommendation.",
        "structure": "Explicit framework: user segments, needs, solutions, prioritization, metrics.",
        "depth": "Real user empathy and product/domain knowledge, not surface-level ideas.",
        "problem_solving": "Prioritizes with a defensible rationale; names tradeoffs and metrics.",
        "behavioral_star": "When relevant, grounds claims in a concrete past example.",
    },
    question_bank=[
        "How would you improve the onboarding experience for a food-delivery app?",
        "Design a feature to help first-generation students find internships.",
        "Our daily active users dropped 15% last week. How do you investigate?",
        "How would you decide which of three features to build next quarter?",
        "Pick a product you love and tell me one thing you would change and why.",
        "How would you measure the success of a new 'saved for later' feature?",
    ],
)

RUBRICS: dict[str, TrackRubric] = {
    TRACK_BEHAVIORAL: BEHAVIORAL,
    TRACK_PM: PM,
}


def get_rubric(track: str) -> TrackRubric:
    if track not in RUBRICS:
        raise ValueError(f"Unknown track: {track!r}. Valid: {list(RUBRICS)}")
    return RUBRICS[track]
