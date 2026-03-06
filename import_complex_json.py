import json
import os
import glob
import shutil
from neo4j import GraphDatabase

# --- 1. CONFIGURATION ---
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405")

# The folder containing your multiple JSON files
SOURCE_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_json_format\extracted_output\processed_files"
OUTPUT_FOLDER_NAME = "processed_files"

# --- 2. CYPHER QUERIES ---

# A. Create the Document Node (The source file)
query_create_document = """
MERGE (d:Document {name: $filename})
"""

# B. Import Entities
# We create a generic :Entity node, but we save the specific Label (ORG, PERSON) as a property.
# We also link the Entity to the Document.
query_import_entities = """
MATCH (d:Document {name: $filename})
UNWIND $data AS row
MERGE (e:Entity {name: row.text})
ON CREATE SET e.type = row.label
MERGE (d)-[:CONTAINS]->(e)
"""

# C. Import Triples (The Relationships)
# We find the Subject and Object, then connect them.
# The 'relation' text (e.g. "outperform") becomes a property of the relationship.
query_import_triples = """
UNWIND $data AS row
MATCH (s:Entity {name: row.subject})
MATCH (o:Entity {name: row.object})
MERGE (s)-[r:RELATED_TO]->(o)
SET r.type = row.relation
"""

# --- 3. MAIN SCRIPT ---
def main():
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Error: Source folder not found: {SOURCE_FOLDER}")
        return

    # Create 'processed_files' folder
    processed_dir = os.path.join(SOURCE_FOLDER, OUTPUT_FOLDER_NAME)
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    # Get all JSON files
    files = glob.glob(os.path.join(SOURCE_FOLDER, "*.json"))
    
    if not files:
        print("No JSON files found to process.")
        return

    print(f"Found {len(files)} files. Starting Neo4j import...")

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            
            for file_path in files:
                file_name = os.path.basename(file_path)
                print(f"Processing: {file_name}...")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 1. Create Document Node
                    # Use the 'source_file' key if it exists, otherwise use the actual filename
                    doc_name = data.get("source_file", file_name)
                    session.run(query_create_document, filename=doc_name)

                    # 2. Import Entities
                    entities = data.get("entities", [])
                    if entities:
                        # Clean data: ensure text isn't None
                        clean_entities = [e for e in entities if e.get("text")]
                        session.run(query_import_entities, data=clean_entities, filename=doc_name)
                        print(f"  -> Loaded {len(clean_entities)} entities.")

                    # 3. Import Triples
                    triples = data.get("triples", [])
                    if triples:
                        # Clean data: ensure subject and object exist
                        clean_triples = [t for t in triples if t.get("subject") and t.get("object")]
                        session.run(query_import_triples, data=clean_triples)
                        print(f"  -> Loaded {len(clean_triples)} relationships.")

                    # 4. Move file to 'processed_files' so we don't process it again
                    shutil.move(file_path, os.path.join(processed_dir, file_name))
                    print("  -> [DONE] File moved to processed folder.")

                except Exception as e:
                    print(f"  -> [ERROR] Could not process {file_name}: {e}")

    print("------------------------------------------------")
    print("Batch Import Complete!")

if __name__ == "__main__":
    main()