import logging
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)


class Neo4jExecutor:
    def __init__(self):
        try:
            self._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            self._driver.verify_connectivity()
            _log.info("Neo4j connection established successfully.")
        except Exception as exc:
            _log.error("Neo4j connection failed: %s", exc)
            raise ConnectionError(
                f"Unable to reach Neo4j at {NEO4J_URI}. "
                "Ensure the server is running and credentials are valid."
            ) from exc

    def close(self):
        try:
            self._driver.close()
        except Exception:
            pass

    def execute_query(self, query: str) -> list:
        """Run a Cypher query and return results as a list of dicts."""
        _log.debug("Running Cypher:\n%s", query)
        try:
            with self._driver.session() as session:
                cursor = session.run(query)
                output = []
                for row in cursor:
                    data = row.data()
                    columns = list(data.keys())

                    if len(columns) == 1:
                        output.append({
                            "relation": "UNKNOWN",
                            "value": data[columns[0]],
                        })
                    elif len(columns) >= 2:
                        output.append({
                            "relation": data.get("relation", data[columns[0]]),
                            "value": data.get("value", data[columns[1]]),
                        })

                _log.debug("Returned %d record(s).", len(output))
                return output
        except Exception as exc:
            _log.error("Query execution failed:\n%s\nError: %s", query, exc)
            raise
