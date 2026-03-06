from neo4j import GraphDatabase

# 1. Connection details
URI = "neo4j://localhost:7687"  # Use "neo4j+s://..." for AuraDB
AUTH = ("neo4j", "tN09dj1405")

def create_friendship(driver, name1, name2):
    # 2. Define your Cypher query
    query = """
    MERGE (p1:Person {name: $name1})
    MERGE (p2:Person {name: $name2})
    MERGE (p1)-[:KNOWS]->(p2)
    RETURN p1, p2
    """
    
    # 3. Execute the query
    with driver.session() as session:
        result = session.run(query, name1=name1, name2=name2)
        print(f"Friendship created between {name1} and {name2}!")

# Use a context manager to handle the driver connection
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    create_friendship(driver, "Alice", "Bob")