"""Rubric config invariants — weights sum to 1, anchors cover all competencies."""
from __future__ import annotations

import math

from app.ai.rubrics import COMPETENCY_KEYS, RUBRICS


def test_weights_sum_to_one_per_track():
    for track, rubric in RUBRICS.items():
        assert math.isclose(sum(rubric.weights.values()), 1.0, abs_tol=1e-6), track


def test_every_competency_has_a_weight_and_anchor():
    for rubric in RUBRICS.values():
        for key in COMPETENCY_KEYS:
            assert key in rubric.weights
            assert key in rubric.anchors and rubric.anchors[key]


def test_question_banks_have_enough_questions():
    for rubric in RUBRICS.values():
        assert len(rubric.question_bank) >= 3
