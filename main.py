import logging
import sys

# Silence noisy third-party loggers
for _name in ("httpx", "openai", "neo4j", "config",
              "agent.executor", "agent.classifier",
              "agent.cypher_generator", "agent.response_engine"):
    logging.getLogger(_name).setLevel(logging.WARNING)

from agent.classifier import IntentClassifier
from agent.cypher_generator import CypherGenerator
from agent.executor import Neo4jExecutor
from agent.response_engine import ResponseEngine

_ACTION_LABELS = {
    "add": "Mathmatical Fact Recorded",
    "update": "Mathmatical Fact Updated",
    "delete": "Mathmatical Fact Erased",
    "inquire": "Ooo Archives Consulted",
}

_EXIT_COMMANDS = {"exit", "quit", "q", "leave"}
_MAX_HISTORY = 5
_CYPHER_RETRIES = 3

_BANNER = (
    "\n" + "=" * 60 + "\n"
    "  Welcome to the Land of Ooo Lore Keeper Bot\n"
    "  Speak thy mathematical queries or type 'exit' to depart.\n"
    + "=" * 60 + "\n"
)


class RPGOrchestrator:
    def __init__(self):
        print("Gathering arcane energy and connecting to the Astral Graph...")
        try:
            self._classifier = IntentClassifier()
            self._cypher_gen = CypherGenerator()
            self._db = Neo4jExecutor()
            self._responder = ResponseEngine()
            self._history: list[str] = []

            from config import LLM_PROVIDER, LLM_MODEL
            print(f"Mystical Source : {LLM_PROVIDER}")
            print(f"Spell Formula   : {LLM_MODEL}")
            print(_BANNER)
        except Exception as exc:
            print(f"\nMathematical error during setup: {exc}")
            sys.exit(1)

    # ── conversation memory ──────────────────────────────────────────

    def _remember(self, text: str) -> None:
        self._history.append(text)
        if len(self._history) > _MAX_HISTORY:
            self._history.pop(0)

    # ── main processing ──────────────────────────────────────────────

    def process_input(self, user_input: str) -> None:
        try:
            intent = self._classifier.classify(user_input, self._history)
            print(f"[INFO] Detected Intent: {intent}")

            if intent == "chitchat":
                reply = self._responder.generate_chitchat(user_input, self._history)
                print(f"\nLore Keeper: {reply}\n")
                self._remember(user_input)
                return

            db_rows = self._execute_with_retries(user_input, intent)
            if db_rows is None:
                return

            label = _ACTION_LABELS.get(intent, "Spell Cast")
            reply = self._responder.generate_response(
                user_input, db_rows, label, intent, self._history
            )
            print(f"\nLore Keeper: {reply}\n")
            self._remember(user_input)

        except ValueError as err:
            print(
                f"\nLore Keeper: The spell fizzled. "
                f"I couldn't formulate a proper seeking query.\nDetail: {err}\n"
            )
        except Exception as err:
            print(f"\nLore Keeper: An unexpected rift opened. Error: {err}\n")

    def _execute_with_retries(self, user_input: str, intent: str):
        for attempt in range(_CYPHER_RETRIES):
            try:
                cypher = self._cypher_gen.generate(
                    user_input, intent, self._history
                )
                if attempt == 0:
                    print(f"\n  [Debug] Generated Cypher :\n{cypher}")
                else:
                    print(f"  [Debug] Retrying Cypher (Attempt {attempt + 1}) :\n{cypher}")

                rows = self._db.execute_query(cypher)
                print(f"  [Debug] Database Results : {rows}")
                return rows
            except Exception as exc:
                if attempt < _CYPHER_RETRIES - 1:
                    print(f"  [Debug] Cypher failed: {type(exc).__name__}. Retrying...")
                else:
                    print(
                        "\nLore Keeper: *Sighs mathematically* I tried to weave that "
                        "spell 3 times, but the cosmic math just ain't mathing right now. "
                        f"My brain feels like a lumpy space cloud.\nDetail: {exc}\n"
                    )
        return None

    # ── REPL loop ────────────────────────────────────────────────────

    def run(self) -> None:
        while True:
            try:
                text = input("Adventurer: ").strip()
                if not text:
                    continue
                if text.lower() in _EXIT_COMMANDS:
                    print("Farewell, and safe travels in the realm!")
                    break
                self.process_input(text)
            except KeyboardInterrupt:
                print("\nFarewell!")
                break
            except Exception as exc:
                print(f"\nUnexpected disturbance: {exc}")

        self._db.close()


if __name__ == "__main__":
    bot = RPGOrchestrator()
    bot.run()
