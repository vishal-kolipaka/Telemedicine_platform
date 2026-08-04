"""
LLM Fallback Matching Engine — stub implementation (Section 8).

This is a stub/mock that follows the MatchingEngine interface but
returns None (unresolved) for all match attempts.  A real LLM
provider (Gemini, OpenAI, etc.) gets plugged in later behind the
same interface — no orchestrator changes needed (Open/Closed).

When a real implementation replaces this stub, it MUST:
  - Return ONLY valid JSON, no markdown/explanation.
  - Provide only the relevant field schema + relevant text slice —
    never the full document or full patient identifiers.
  - Run privacy.redact_pii() BEFORE constructing the prompt.
  - Instruct: "If the value is not present, return null.
    Never invent or guess."
  - Use temperature = 0, retry once on invalid JSON, then degrade
    to unresolved (not a crash).
  - Set mapping_method = "llm_fallback" on resolved fields.
  - Generally assign lower confidence than an equivalent regex match.
"""

from __future__ import annotations

from src.preprocessing.mapper.interfaces import MatchingEngine
from src.preprocessing.mapper.models import Candidate, MappedFeature
from src.preprocessing.mapper.config import MapperConfig


class LLMFallbackMatchingEngine(MatchingEngine):
    """Stub LLM fallback — returns None for all match attempts.

    Constructor-injected into the orchestrator alongside the
    RegexMatchingEngine.  When enabled, the orchestrator calls
    this after a regex match falls between the accept and
    LLM-trigger thresholds.

    To plug in a real LLM:
    1. Subclass MatchingEngine (or replace this class).
    2. Inject an LLM API client via the constructor.
    3. Implement match() with the requirements listed in the
       module docstring above.
    """

    VERSION = "LLMFallbackMatchingEngine 1.0 (stub)"

    def __init__(self, config: MapperConfig) -> None:
        self._config = config

    def match(
        self,
        candidates: list[Candidate],
        field_name: str,
        field_schema: dict,
    ) -> MappedFeature | None:
        """Stub: always returns None (unresolved).

        A real implementation would:
        1. Build a minimal text slice from the relevant candidates.
        2. Redact PII via privacy.redact_pii().
        3. Send a structured prompt to the LLM API.
        4. Parse the JSON response.
        5. Return a MappedFeature with mapping_method="llm_fallback"
           and generally lower confidence.
        """
        return None
