import json
import os
from neo4j import GraphDatabase

# --- CONFIGURATION ---
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405")

# Path to your citation file
JSON_FILE_PATH = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\for_xlsx\output_citation.json"

# --- CYPHER QUERY ---
# This query connects the Citing Paper (Source) to the Cited Paper (Target)
query_import_citations = """
UNWIND $data AS row

// 1. Find or Create the Citing Paper (The one doing the referencing)
// We match by Title (since your JSON uses titles as IDs)
MERGE (source:Paper {title: row.citing_title})

// 2. Find or Create the Cited Paper (The one being referenced)
MERGE (target:Paper {title: row.cited_title})

// 3. Create the CITATION relationship
MERGE (source)-[:CITES]->(target)
"""

def main():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: File not found at {JSON_FILE_PATH}")
        return

    print(f"Reading file: {JSON_FILE_PATH}...")

    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            content = json.load(f)

        # Prepare a single flat list of all citations to send to Neo4j
        all_citations = []

        # Loop through keys like "RESEARCH PAPER 1", "RESEARCH PAPER 2", etc.
        for paper_key, citations_list in content.items():
            
            for item in citations_list:
                # Handle inconsistencies in key names (e.g. "Citing_Paper_ID" vs "Citing_Papers_ID")
                # We use .get() to check both possibilities
                citing = item.get("Citing_Paper_ID") or item.get("Citing_Papers_ID")
                cited = item.get("Cited_Paper_ID") or item.get("Cited_Papers_ID")

                if citing and cited:
                    all_citations.append({
                        "citing_title": citing.strip(),
                        "cited_title": cited.strip()
                    })

        if not all_citations:
            print("No valid citations found in the file.")
            return

        print(f"Found {len(all_citations)} citation relationships. Importing...")

        # Run the import
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                # We process in batches of 1000 to be safe, though one batch is usually fine for small files
                session.run(query_import_citations, data=all_citations)
                
        print(f"Success! {len(all_citations)} citation connections created.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()