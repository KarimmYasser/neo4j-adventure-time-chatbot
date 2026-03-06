import os
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

from agent.cypher_generator import CypherGenerator
from agent.executor import Neo4jExecutor

def load_seed_data(file_path: str = "seed_data.txt"):
    if not os.path.exists(file_path):
        print(f"Error: '{file_path}' not found.")
        return

    generator = CypherGenerator()
    executor = Neo4jExecutor()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        print(f"Adding {len(lines)} mathematical facts to the Enchiridion...\n" + "-" * 55)
        success, failed = 0, 0

        for i, line in enumerate(lines, 1):
            print(f"[{i}/{len(lines)}] {line}")
            try:
                cypher_query = generator.generate(line, "add", history=[])
                executor.execute_query(cypher_query)
                print("  ✓ Mathematical Fact Recorded\n")
                success += 1
            except Exception as e:
                print(f"  ✗ Failed to Record Fact: {e}\n")
                failed += 1

        print("-" * 55)
        print(f"Enchiridion Update Complete. Success: {success} | Failed: {failed}")

    finally:
        executor.close()


if __name__ == "__main__":
    load_seed_data()
