import re
import logging
from config import CYPHER_GENERATOR_PROMPT
from .llm_client import LLMClient

_log = logging.getLogger(__name__)

_ALLOWED_PREFIXES = ("MATCH", "MERGE", "CREATE", "CALL", "WITH")
_BLOCKED_OPERATIONS = ("DROPCONSTRAINT", "DROPINDEX", "CREATECONSTRAINT", "CREATEINDEX")


class CypherGenerator:
    def __init__(self):
        self._client = LLMClient()

    def generate(self, user_input: str, intent: str, history: list, max_retries: int = 3) -> str:
        recent = history[-2:] if history else []
        conversation_ctx = "\n".join(f"User: {m}" for m in recent) if recent else "None"
        formatted_prompt = CYPHER_GENERATOR_PROMPT.format(
            intent=intent, history=conversation_ctx, user_input=user_input
        )

        attempts = max_retries + 1
        for i in range(attempts):
            try:
                raw_output = self._client.generate(formatted_prompt)
                cypher = self._sanitize(raw_output)

                if not cypher:
                    _log.warning("Attempt %d: Received empty query.", i + 1)
                    continue

                if not self._passes_safety_check(cypher):
                    _log.warning(
                        "Attempt %d: Blocked unsafe query:\n%s\nRetrying...", i + 1, cypher
                    )
                    continue

                _log.debug("Generated Cypher:\n%s", cypher)
                return cypher

            except Exception as err:
                _log.error("Cypher generation error (attempt %d): %s", i + 1, err)

        raise ValueError(
            f"Unable to produce a safe Cypher query after {attempts} attempts."
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize(raw: str) -> str:
        text = raw.strip()
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        cleaned_lines = [
            line for line in text.strip().splitlines()
            if not line.strip().startswith(("//", "#"))
        ]
        query = "\n".join(cleaned_lines).strip()
        query = CypherGenerator._fix_unbound_relationship(query)
        return query

    @staticmethod
    def _fix_unbound_relationship(query: str) -> str:
        """If `type(r)` appears in RETURN but `r` is not bound in the
        MATCH pattern, rewrite the relationship bracket to include `r`.

        Handles patterns like:
          -[:LIVES_IN]->   →  -[r:LIVES_IN]->
          -[:LIVES_IN]-    →  -[r:LIVES_IN]-
          -[]->            →  -[r]->
        """
        if "type(r)" not in query.lower():
            return query
        # Check if `r` is already bound somewhere in a bracket: [r] or [r:...]
        if re.search(r"\[\s*r\s*[:\]\s]", query):
            return query
        # Replace `[:REL_TYPE]` with `[r:REL_TYPE]`
        fixed = re.sub(r"\[\s*:([A-Z_]+)\s*\]", r"[r:\1]", query)
        if fixed != query:
            _log.info("Auto-fixed unbound relationship variable `r` in Cypher.")
            return fixed
        # Replace `[]` with `[r]`
        fixed = re.sub(r"\[\s*\]", "[r]", query)
        if fixed != query:
            _log.info("Auto-fixed empty relationship bracket to `[r]`.")
            return fixed
        return query

    @staticmethod
    def _passes_safety_check(query: str) -> bool:
        compressed = query.upper().replace(" ", "")

        if "MATCH(N)DETACHDELETE" in compressed or "MATCH(N)DELETE" in compressed:
            return False

        if any(op in compressed for op in _BLOCKED_OPERATIONS):
            return False

        upper_query = query.strip().upper()
        return any(upper_query.startswith(prefix) for prefix in _ALLOWED_PREFIXES)
