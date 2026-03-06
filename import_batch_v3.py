import json
import os
from neo4j import GraphDatabase

# --- CONFIGURATION ---
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405")

# Path to your new references file
# Update the filename if it is different
JSON_FILE_PATH = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\for_xlsx\output_referencedata.json"

# --- CYPHER QUERY ---
query_import_references = """
UNWIND $data AS row

// 1. Find the Source Paper (The one citing)
// We use the ID (e.g., "RESEARCH PAPER_1")
MERGE (source:Paper {id: row.source_id})

// 2. Find or Create the Referenced Paper
// We match by Title. If it's new, we set the year and source.
MERGE (target:Paper {title: row.ref_title})
ON CREATE SET target.year = row.ref_year, 
              target.source_publication = row.ref_source

// 3. Create the CITATION relationship
// We store the Ref ID (e.g., R01) on the relationship itself
MERGE (source)-[:CITES {id: row.ref_id}]->(target)
"""

def main():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: File not found at {JSON_FILE_PATH}")
        return

    print(f"Reading file: {JSON_FILE_PATH}...")

    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            content = json.load(f)

        # 1. Get the list from Sheet1
        raw_list = content.get("Sheet1", [])
        
        if not raw_list:
            print("Error: 'Sheet1' is empty or missing.")
            return

        # 2. Process and Clean Data
        # We need to convert "P01" -> "RESEARCH PAPER_1" to match your previous nodes
        processed_data = []
        
        for item in raw_list:
            p_id = item.get("PAPER_ID", "")
            
            # Logic to convert P01 -> RESEARCH PAPER_1, P10 -> RESEARCH PAPER_10
            # This ensures it links to the Metadata you imported earlier
            if p_id.startswith("P"):
                try:
                    num = int(p_id[1:]) # Turns "01" into 1, "10" into 10
                    source_id = f"RESEARCH PAPER_{num}"
                except ValueError:
                    source_id = p_id # Fallback if format is weird
            else:
                source_id = p_id

            processed_data.append({
                "source_id": source_id,
                "ref_id": item.get("REF_ID"),
                "ref_title": item.get("REFERENCED_PAPER_TITLE"),
                "ref_year": item.get("YEAR"),
                "ref_source": item.get("SOURCE")
            })

        print(f"Found {len(processed_data)} references. Importing...")

        # 3. Run Import
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                session.run(query_import_references, data=processed_data)
                
        print(f"Success! {len(processed_data)} citation links created.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()