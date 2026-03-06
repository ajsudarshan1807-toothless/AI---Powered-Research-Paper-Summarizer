import json
from neo4j import GraphDatabase

# 1. Update these to match your working setup
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405") 
JSON_FILE = "triples.json"  # Make sure this matches your actual file name

def import_triples(tx, data):
    query = """
    UNWIND $data AS row
    
    // 1. Create the Head node (Subject)
    MERGE (h:Entity {name: row.head})
    ON CREATE SET h.type = row.head_type
    
    // 2. Create the Tail node (Object)
    MERGE (t:Entity {name: row.tail})
    ON CREATE SET t.type = row.tail_type
    
    // 3. Create the Relationship
    // We use APOC if available, or a specific relationship type if you prefer.
    // This generic version works without plugins:
    MERGE (h)-[r:RELATED_TO {type: row.relation}]->(t)
    """
    tx.run(query, data=data)

# Sample data to test (if you don't have your file ready yet)
sample_data = [
    {"head": "Elon Musk", "head_type": "Person", "relation": "CEO_OF", "tail": "Tesla", "tail_type": "Company"},
    {"head": "Tesla", "head_type": "Company", "relation": "LOCATED_IN", "tail": "Texas", "tail_type": "Location"}
]

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session() as session:
        # If using a real file, uncomment the lines below:
        # with open(JSON_FILE, 'r') as f:
        #     data = json.load(f
        
        # For now, we use the sample data to prove it works
        session.execute_write(import_triples, sample_data)
        print("Imported sample triples successfully!")