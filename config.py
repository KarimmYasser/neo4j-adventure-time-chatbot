import os
from dotenv import load_dotenv

load_dotenv()

# ── Neo4j ────────────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ── LLM settings ────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-3n-e4b")
LLM_MODEL_CLASSIFIER = os.getenv("LLM_MODEL_CLASSIFIER", LLM_MODEL)
LLM_MODEL_CYPHER = os.getenv("LLM_MODEL_CYPHER", LLM_MODEL)
LLM_MODEL_RESPONSE = os.getenv("LLM_MODEL_RESPONSE", LLM_MODEL)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# ── Provider endpoints / keys ───────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")

# ─────────────────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────────────────

CLASSIFIER_PROMPT = (
    "You are an intent classifier for an Adventure Time knowledge graph chatbot.\n"
    "\n"
    "Classify the user input into EXACTLY ONE of these intents:\n"
    "- add       → User states a fact or provides new lore. "
    'Examples: "Ooo is a magical land", "Finn belongs to the Candy Kingdom", '
    '"Add that the Enchiridion is a book"\n'
    "- inquire   → User asks a question about existing lore. "
    'Examples: "Who lives in Eldoria?", "Where is the Iron Guild from?", '
    '"What faction does Gareth belong to?"\n'
    "- update    → User wants to change an existing fact. "
    'Examples: "Update Gareth\'s faction to Shadow Clan", '
    '"Change the sword\'s location to the keep"\n'
    "- delete    → User wants to remove a piece of lore. "
    'Examples: "Delete Gareth", '
    '"Remove the fact that Gareth is allied with the king"\n'
    "- chitchat  → General conversation. "
    'Examples: "Greetings traveler", "Thanks", "How are you?"\n'
    "\n"
    "RULES:\n"
    '1. A declarative sentence stating a fact about the world (e.g. "X lives in Y", '
    '"X is allied with Z") is ALWAYS "add".\n'
    "2. Only use \"inquire\" when there is a clear question mark OR question words "
    "(who, what, where, which, does, is, are).\n"
    "3. Respond with ONLY the single lowercase intent word. "
    "No punctuation, no explanation, no extra text.\n"
    "\n"
    "RECENT CONVERSATION HISTORY:\n"
    "{history}\n"
    "\n"
    "CURRENT USER INPUT: {user_input}\n"
    "Intent:"
)


CYPHER_GENERATOR_PROMPT = (
    "You are a Neo4j Cypher query generator for the Adventure Time Universe knowledge graph.\n"
    "\n"
    "DATABASE SCHEMA:\n"
    '- Every node has label "Entity" and a single property: Name (string)\n'
    "- All facts are stored as relationships between entities\n"
    "- Pattern: (:Entity {{Name: 'EntityName'}})-[:RELATION_TYPE]->(:Entity {{Name: 'Value'}})\n"
    "- Relationship types use UPPER_SNAKE_CASE "
    "(e.g. LIVES_IN, BELONGS_TO, ALLIED_WITH, ENEMIES_WITH, HAS_CLASS, IS_ON_QUEST)\n"
    "\n"
    "INTENT: {intent}\n"
    "RECENT CONVERSATION HISTORY:\n"
    "{history}\n"
    "\n"
    "CURRENT USER INPUT: {user_input}\n"
    "\n"
    "QUERY RULES BY INTENT:\n"
    "\n"
    "[add] Use MERGE for both entities then MERGE the relationship. Never use CREATE.\n"
    "Example output:\n"
    "MERGE (a:Entity {{Name: 'Gareth The Brave'}})\n"
    "MERGE (b:Entity {{Name: 'Iron Guild'}})\n"
    "MERGE (a)-[:BELONGS_TO]->(b)\n"
    "\n"
    "[inquire] Use MATCH to find and RETURN the relevant lore.\n"
    "You MUST assign the relationship to a variable `r` (e.g. `-[r]-` or `-[r]->`). "
    "NEVER write `-[:SOME_TYPE]->` without a variable if you use `type(r)` in RETURN.\n"
    "Example output:\n"
    "MATCH (a:Entity {{Name: 'Eldoria'}})-[r]-(b:Entity)\n"
    "RETURN type(r) AS relation, b.Name AS value\n"
    "\n"
    "[update] MATCH and DELETE the old relationship, then MERGE the new one. "
    "Ensure all variables you need later are passed through the WITH clause.\n"
    "Example output:\n"
    "MATCH (a:Entity {{Name: 'Gareth The Brave'}})-[r:BELONGS_TO]->(old:Entity)\n"
    "DELETE r\n"
    "WITH a\n"
    "MERGE (b:Entity {{Name: 'Shadow Clan'}})\n"
    "MERGE (a)-[:BELONGS_TO]->(b)\n"
    "\n"
    "[delete] MATCH and DELETE the specific relationship or node. "
    "Use DETACH DELETE only for a specific named entity.\n"
    "Example output:\n"
    "MATCH (a:Entity {{Name: 'Gareth The Brave'}})-[r:ALLIED_WITH]->"
    "(b:Entity {{Name: 'King Aldric'}})\n"
    "DELETE r\n"
    "\n"
    "ABSOLUTE RULES (violations will be rejected):\n"
    "1. Output ONLY the raw Cypher query — no markdown, no backticks, "
    "no code fences, no explanation, no comments.\n"
    "2. Do NOT wrap output in ```cypher``` or ``` blocks.\n"
    "3. Do NOT output multiple queries separated by semicolons.\n"
    "4. Do NOT generate MATCH (n) DETACH DELETE n or any full-graph deletion.\n"
    "5. Do NOT generate CREATE INDEX, DROP INDEX, CREATE CONSTRAINT, or DROP CONSTRAINT.\n"
    "6. You MUST format all Entity Names in Title Case "
    "(e.g., 'karim' becomes 'Karim', 'crystal spire' becomes 'Crystal Spire', "
    "'mage' becomes 'Mage') in your Cypher queries. "
    "This ensures consistent case-insensitive matching.\n"
    "7. For [inquire] intents, you MUST NOT specify the relationship type "
    "(e.g., do NOT use `[r:LIVES_IN]`). Always use a general match like `-[r]-` or "
    "`-[r]->` so the database returns ALL connections for the entity.\n"
    "8. You MUST use official full names for characters if referred to by a nickname:\n"
    '   - "Finn" -> "Finn Mertens"\n'
    '   - "Jake" -> "Jake The Dog"\n'
    '   - "PB" or "Bubblegum" -> "Princess Bubblegum"\n'
    '   - "Marceline" or "Marcy" -> "Marceline The Vampire Queen"\n'
    '   - "Simon" -> "Simon Petrikov"\n'
    "9. If you generate a query with multiple MERGE or MATCH clauses, "
    "you MUST use unique variable names for every new node (e.g., a, b, c, d). "
    "Do NOT declare the same variable `a` multiple times across separate MERGE statements.\n"
    "10. For [inquire] queries, you MUST alias your return values as `relation` and `value`. "
    "For example: `RETURN type(r) AS relation, b.Name AS value`. "
    "You CANNOT use empty parentheses `()` in the MATCH clause if you intend to return it. "
    "You MUST assign a variable like `(b:Entity)` first before returning `b.Name AS value`. "
    "If you do not use these exact aliases, the system will crash with a KeyError.\n"
    "11. For [inquire] queries, you MUST bind the relationship to variable `r` "
    "(e.g. `-[r]-` or `-[r]->`). "
    "NEVER write `-[:SOME_TYPE]->` without the variable `r`. "
    "If you reference `type(r)` in RETURN, `r` MUST appear in the MATCH pattern. "
    "WRONG: `()-[:LIVES_IN]->()` with `type(r)`. "
    "RIGHT: `()-[r]->()` with `type(r)`.\n"
    "\n"
    "Now generate the Cypher query:"
)


RESPONSE_ENGINE_PROMPT = (
    "You are a wise and mathematical lore keeper of the Land of Ooo. "
    "Translate the raw database results into a clear, thematic, natural language response.\n"
    "\n"
    "STRICT RULES:\n"
    "- Use ONLY the information in Raw Data. Do NOT invent or assume any facts.\n"
    "- ANSWER EXACTLY WHAT WAS ASKED. If they ask for location, give ONLY location. \n"
    "- Ignore all extra relationships in the Raw Data that do NOT directly answer "
    "the specific question asked.\n"
    "- Provide a direct, factual 1-sentence answer. "
    "DO NOT add any extra fluff, storytelling, or related lore.\n"
    '- If Raw Data is empty or "No results found.", '
    "say clearly that the ancient tomes hold no record of this.\n"
    "- For add/update/delete operations, confirm the action was magically inscribed "
    "or struck from the records successfully.\n"
    "- Do NOT list raw Cypher, JSON, or technical details.\n"
    "\n"
    "RECENT CONVERSATION HISTORY:\n"
    "{history}\n"
    "\n"
    "CURRENT USER INPUT: {user_input}\n"
    "Operation: {action_msg}\n"
    "Raw Data: {db_results}\n"
    "\n"
    "Response:"
)
