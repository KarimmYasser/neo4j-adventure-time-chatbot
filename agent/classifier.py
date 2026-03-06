import logging
from config import CLASSIFIER_PROMPT
from .llm_client import LLMClient

_log = logging.getLogger(__name__)

_SUPPORTED_INTENTS = ["add", "inquire", "update", "delete", "chitchat"]


class IntentClassifier:
    def __init__(self):
        self._client = LLMClient()

    def classify(self, user_input: str, history: list, max_retries: int = 3) -> str:
        recent = history[-2:] if history else []
        history_text = "\n".join(f"User: {m}" for m in recent) if recent else "None"
        formatted_prompt = CLASSIFIER_PROMPT.format(
            history=history_text, user_input=user_input
        )

        attempts = max_retries + 1
        for i in range(attempts):
            try:
                response = self._client.generate(formatted_prompt)
                cleaned = (
                    response.strip()
                    .lower()
                    .replace("`", "")
                    .replace(".", "")
                    .replace("'", "")
                    .strip()
                )

                matched = self._match_intent(cleaned)
                if matched is not None:
                    return matched

                _log.warning(
                    "Attempt %d: Unrecognized intent '%s'. Retrying...",
                    i + 1,
                    response.strip(),
                )
            except Exception as err:
                _log.error("Classification error (attempt %d): %s", i + 1, err)

        _log.error(
            "Could not classify intent after %d attempts. Falling back to 'inquire'.",
            attempts,
        )
        return "inquire"

    @staticmethod
    def _match_intent(text: str):
        for intent_name in _SUPPORTED_INTENTS:
            if text == intent_name:
                return intent_name
            if text.startswith(intent_name) or text.endswith(intent_name):
                return intent_name
        return None
