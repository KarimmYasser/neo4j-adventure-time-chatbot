import logging
from config import RESPONSE_ENGINE_PROMPT
from .llm_client import LLMClient

_log = logging.getLogger(__name__)

_EMPTY_RESULT_MSG = "The ancient tomes hold no record of this."
_FALLBACK_RESPONSE = "I encountered a magical disturbance while consulting the archives."
_FALLBACK_CHITCHAT = "Greetings, traveler. How may I weave the tales of the realm for you today?"

_CHITCHAT_SYSTEM = (
    "You are a mystical Lore Keeper of a Fantasy RPG Universe. "
    "The user (an adventurer) is making casual conversation. "
    "Reply warmly but mysteriously in 1-2 sentences."
)


class ResponseEngine:
    def __init__(self):
        self._client = LLMClient()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_history_string(history: list) -> str:
        if not history:
            return "None"
        return "\n".join(f"User: {m}" for m in history[-2:])

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def generate_response(
        self,
        user_input: str,
        db_results: list,
        action_msg: str,
        intent: str,
        history: list,
    ) -> str:
        if intent == "inquire" and not db_results:
            return _EMPTY_RESULT_MSG

        results_text = str(db_results) if db_results else "Operation successful."
        history_text = self._build_history_string(history)

        formatted_prompt = RESPONSE_ENGINE_PROMPT.format(
            history=history_text,
            user_input=user_input,
            db_results=results_text,
            action_msg=action_msg,
            intent=intent,
        )

        try:
            return self._client.generate(formatted_prompt)
        except Exception as err:
            _log.error("Response generation failed: %s", err)
            return _FALLBACK_RESPONSE

    def generate_chitchat(self, user_input: str, history: list) -> str:
        history_text = self._build_history_string(history)
        prompt = (
            f"{_CHITCHAT_SYSTEM}\n\n"
            f"Recent History:\n{history_text}\n\n"
            f"Adventurer: {user_input}\n"
            "Lore Keeper:"
        )
        try:
            return self._client.generate(prompt)
        except Exception as err:
            _log.error("Chitchat generation failed: %s", err)
            return _FALLBACK_CHITCHAT
