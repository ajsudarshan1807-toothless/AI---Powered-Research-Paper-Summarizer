import json
import os
import glob
import shutil
import datetime
from neo4j import GraphDatabase

# --- 1. CONFIGURATION ---
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405") 

# Path to your JSON files
SOURCE_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_abstract_json\extracted_output"
OUTPUT_FOLDER_NAME = "processed_files"

# --- 2. NEO4J QUERY ---
def import_triples(tx, data):
    query = """
    UNWIND $data AS row
    MERGE (s:Entity {name: row.subject})
    MERGE (o:Entity {name: row.object})
    MERGE (s)-[r:RELATED_TO {type: row.relation}]->(o)
    """
    tx.run(query, data=data)

# --- 3. MAIN SCRIPT ---
def main():
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Error: Source folder not found: {SOURCE_FOLDER}")
        return

    # Create the output folder if it doesn't exist
    processed_dir = os.path.join(SOURCE_FOLDER, OUTPUT_FOLDER_NAME)
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    # Find all JSON files
    files_to_process = glob.glob(os.path.join(SOURCE_FOLDER, "*.json"))

    if not files_to_process:
        print("No JSON files found to process.")
        return

    print(f"Found {len(files_to_process)} files. Starting import...")

    total_files_moved = 0
    total_triples_imported = 0
    log_messages = []

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            
            for file_path in files_to_process:
                file_name = os.path.basename(file_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = json.load(f)

                    # Get triples safely
                    triples_data = file_content.get("triples", [])

                    # Case A: Triples found -> Import them
                    if isinstance(triples_data, list) and len(triples_data) > 0:
                        session.execute_write(import_triples, triples_data)
                        count = len(triples_data)
                        msg = f"[SUCCESS] Imported {count} triples from {file_name}"
                        total_triples_imported += count

                    # Case B: No triples -> Skip import, but still move file
                    else:
                        msg = f"[SKIPPED] {file_name} (Triples list was empty)"

                    # --- CRITICAL UPDATE: Move file regardless of success or skip ---
                    shutil.move(file_path, os.path.join(processed_dir, file_name))
                    total_files_moved += 1
                    
                    print(msg)
                    log_messages.append(msg)

                except Exception as e:
                    # If there is a crash (e.g., bad JSON format), we DO NOT move the file
                    # so you can fix it manually.
                    msg = f"[ERROR] Failed to process {file_name}: {e}"
                    print(msg)
                    log_messages.append(msg)

    # Write Log
    log_path = os.path.join(processed_dir, "import_log.txt")
    with open(log_path, "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n--- Batch Run: {timestamp} ---\n")
        for line in log_messages:
            log_file.write(line + "\n")
        log_file.write(f"Summary: {total_files_moved} files moved, {total_triples_imported} triples created.\n")

    print("------------------------------------------------")
    print(f"Done! {total_files_moved} files moved to '{OUTPUT_FOLDER_NAME}'.")

if __name__ == "__main__":
    main()