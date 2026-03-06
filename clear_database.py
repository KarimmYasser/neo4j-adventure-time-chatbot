import sys
from agent.executor import Neo4jExecutor

def clear_database():
    print("Connecting to the Neo4j database...")
    try:
        executor = Neo4jExecutor()
        
        confirmation = input("WARNING: This will DESTROY all data in the current Neo4j database. Are you sure? (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Operation aborted.")
            return

        print("Casting the obliteration spell... purging the Astral Graph...")
        
        # Execute the standard Cypher query to detach and delete all nodes
        executor.execute_query("MATCH (n) DETACH DELETE n")
        
        print("Success: The database has been completely wiped clean.")
        
    except Exception as e:
        print(f"Failed to clear the database. Magical disturbance: {e}")
    finally:
        if 'executor' in locals():
            executor.close()

if __name__ == "__main__":
    clear_database()
