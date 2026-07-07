"""LiteLLM single-model wrapper: retry, graceful fallback, token/cost/latency capture.

If ANTHROPIC_API_KEY is unset the client runs in deterministic MOCK mode so the whole
product is demoable and testable for free. The public interface is identical, so nothing
downstream knows or cares which mode is active.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger("ai.llm")

# Rough per-1K-token USD prices for cost tracking (documented in README cost model).
_PRICE_PER_1K = {"input": 0.003, "output": 0.015}
_MAX_RETRIES = 2


@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    mock: bool = False
    meta: dict = field(default_factory=dict)


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return round(
        input_tokens / 1000 * _PRICE_PER_1K["input"]
        + output_tokens / 1000 * _PRICE_PER_1K["output"],
        6,
    )


class LLMClient:
    def __init__(self) -> None:
        self.model = settings.llm_model
        self.mock = settings.llm_mock_mode
        if self.mock:
            logger.info("LLMClient in MOCK mode (no ANTHROPIC_API_KEY) — deterministic, free.")

    async def complete(
        self, *, system: str, user: str, json_mode: bool = False, max_tokens: int = 700
    ) -> LLMResult:
        if self.mock:
            return self._mock_complete(system=system, user=user, json_mode=json_mode)
        return await self._live_complete(
            system=system, user=user, json_mode=json_mode, max_tokens=max_tokens
        )

    # ---------- live ----------
    async def _live_complete(
        self, *, system: str, user: str, json_mode: bool, max_tokens: int
    ) -> LLMResult:
        import litellm

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.llm_temperature,
            "max_tokens": max_tokens,
            "api_key": settings.anthropic_api_key,
        }
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            start = time.perf_counter()
            try:
                resp = await litellm.acompletion(**kwargs)
                latency_ms = int((time.perf_counter() - start) * 1000)
                text = resp["choices"][0]["message"]["content"] or ""
                usage = resp.get("usage", {}) or {}
                in_tok = int(usage.get("prompt_tokens", 0))
                out_tok = int(usage.get("completion_tokens", 0))
                return LLMResult(
                    text=text.strip(),
                    model=self.model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=latency_ms,
                    cost_usd=_estimate_cost(in_tok, out_tok),
                    mock=False,
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("LLM call failed (attempt %s): %s", attempt + 1, exc)
                await asyncio.sleep(0.5 * (attempt + 1))
        raise LLMError("The AI service is temporarily unavailable. Please try again.") from last_exc

    # ---------- mock ----------
    def _mock_complete(self, *, system: str, user: str, json_mode: bool) -> LLMResult:
        start = time.perf_counter()
        text = self._mock_eval(user) if json_mode else self._mock_interview(user)
        latency_ms = int((time.perf_counter() - start) * 1000)
        in_tok = max(1, len(system + user) // 4)
        out_tok = max(1, len(text) // 4)
        return LLMResult(
            text=text,
            model=f"{self.model}-mock",
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency_ms,
            cost_usd=0.0,
            mock=True,
        )

    def _mock_interview(self, user: str) -> str:
        # If instructed to ask a specific main question, echo it (that is the desired behavior).
        m = re.search(r'exactly this question[^"]*"([^"]+)"', user)
        if m:
            return m.group(1).strip()
        # Otherwise it's a follow-up: quote the candidate to prove adaptiveness.
        ans = re.search(r'Candidate answered: "([^"]+)"', user)
        snippet = (ans.group(1)[:80] + "…") if ans else "what you described"
        return (
            f"You mentioned \"{snippet}\" — can you walk me through the specific actions "
            f"you personally took and how you measured the outcome?"
        )

    def _mock_eval(self, user: str) -> str:
        """Deterministic, answer-sensitive scoring so the demo and tests feel real."""
        ans = re.search(r'answer \(including any follow-up answer\):\s*"([^"]*)"', user, re.S)
        answer = (ans.group(1) if ans else "").lower()
        keys = re.findall(r"^- (\w+) \(", user, re.M)  # competency keys in prompt order
        if not keys:
            keys = ["communication", "structure", "depth", "problem_solving", "behavioral_star"]

        has_number = bool(re.search(r"\d", answer))
        words = len(answer.split())
        star = sum(k in answer for k in ("situation", "task", "action", "result", "i led", "i built"))

        def score_for(k: str) -> int:
            base = 3
            if words < 15:
                base = 2
            elif words > 60:
                base = 4
            if k == "behavioral_star":
                base = min(5, 2 + star)
            if k == "depth" and has_number:
                base = min(5, base + 1)
            if k == "problem_solving" and ("because" in answer or "tradeoff" in answer):
                base = min(5, base + 1)
            return max(1, min(5, base))

        scores = {k: score_for(k) for k in keys}
        quote = (answer[:60] + "…") if answer else "your answer"
        payload = {
            "scores": scores,
            "rationales": {k: f"Assessed '{quote}' against the {k} anchor." for k in keys},
            "improvements": [
                f"You said \"{quote}\" — add a concrete metric to show the impact.",
                "Name the single most important decision you made and why.",
            ]
            + (["Tighten the opening so the structure is obvious in the first sentence."]
               if words > 40 else []),
            "recommendations": ["Practice one answer using the STAR/SCQA structure and time yourself."],
        }
        return json.dumps(payload)


_client: LLMClient | None = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
