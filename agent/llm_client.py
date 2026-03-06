import requests
import logging
from config import LLM_PROVIDER, OLLAMA_URL, LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY, GROQ_API_KEY

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider client singletons (initialized at import time)
# ---------------------------------------------------------------------------
_openai = None
_groq = None
_lmstudio = None

_provider = LLM_PROVIDER.lower()

if _provider == "openai":
    try:
        from openai import OpenAI

        _openai = OpenAI(api_key=OPENAI_API_KEY)
        _log.info("OpenAI client ready.")
    except ImportError:
        _log.error("Missing openai package. Install with: pip install openai")

elif _provider == "groq":
    try:
        from openai import OpenAI

        _groq = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        _log.info("Groq client ready.")
    except ImportError:
        _log.error("Missing openai package (needed for Groq). Install: pip install openai")

elif _provider == "lmstudio":
    try:
        from openai import OpenAI
        from config import LMSTUDIO_BASE_URL

        _lmstudio = OpenAI(api_key="lm-studio", base_url=LMSTUDIO_BASE_URL)
        _log.info("LM Studio client ready.")
    except ImportError:
        _log.error("Missing openai package (needed for LM Studio). Install: pip install openai")


# ---------------------------------------------------------------------------
# Unified LLM interface
# ---------------------------------------------------------------------------
class LLMClient:
    def __init__(self):
        self._provider = _provider
        self._model = LLM_MODEL
        self._temp = LLM_TEMPERATURE
        self._ollama_endpoint = OLLAMA_URL

    def generate(self, prompt: str) -> str:
        """Return a text completion from the active LLM provider."""

        handler = {
            "openai": self._call_openai,
            "groq": self._call_groq,
            "lmstudio": self._call_lmstudio,
            "ollama": self._call_ollama,
        }.get(self._provider)

        if handler is None:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{self._provider}'. "
                "Supported: 'openai', 'groq', 'lmstudio', 'ollama'"
            )
        return handler(prompt)

    # -- provider-specific helpers -----------------------------------------

    def _chat_completion(self, client, prompt: str) -> str:
        resp = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temp,
        )
        return resp.choices[0].message.content.strip()

    def _call_openai(self, prompt: str) -> str:
        if _openai is None:
            raise ValueError("OpenAI client unavailable. Verify OPENAI_API_KEY and package.")
        return self._chat_completion(_openai, prompt)

    def _call_groq(self, prompt: str) -> str:
        if _groq is None:
            raise ValueError("Groq client unavailable. Verify GROQ_API_KEY and package.")
        return self._chat_completion(_groq, prompt)

    def _call_lmstudio(self, prompt: str) -> str:
        if _lmstudio is None:
            raise ValueError("LM Studio client unavailable. Verify package installation.")
        return self._chat_completion(_lmstudio, prompt)

    def _call_ollama(self, prompt: str) -> str:
        body = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self._temp},
        }
        try:
            resp = requests.post(self._ollama_endpoint, json=body, timeout=120)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot reach Ollama at {self._ollama_endpoint}. Is it running?"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama request exceeded 120-second timeout.")
