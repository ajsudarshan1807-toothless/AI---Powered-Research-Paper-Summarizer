import json
import os
import glob
import shutil
import datetime
from neo4j import GraphDatabase

# --- 1. CONFIGURATION ---
# Connection details
URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "tN09dj1405") 

# Path to your JSON files
SOURCE_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\for_xlsx\extracted_output"

# Name of the output folder to create (inside the source folder)
OUTPUT_FOLDER_NAME = "processed_files"

# --- 2. NEO4J QUERY ---
def import_triples(tx, data):
    # Note: We updated the keys to match your new JSON: subject, relation, object
    query = """
    UNWIND $data AS row
    
    // 1. Create the Subject Node
    MERGE (s:Entity {name: row.subject})
    
    // 2. Create the Object Node
    MERGE (o:Entity {name: row.object})
    
    // 3. Create the Relationship
    // We store the specific verb (e.g., "utilize", "diminish") as a property 'type'
    MERGE (s)-[r:RELATED_TO {type: row.relation}]->(o)
    """
    tx.run(query, data=data)

# --- 3. MAIN SCRIPT ---
def main():
    # A. Check paths
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Error: Source folder not found: {SOURCE_FOLDER}")
        return

    # B. Create the output/processed folder
    processed_dir = os.path.join(SOURCE_FOLDER, OUTPUT_FOLDER_NAME)
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        print(f"Created output folder: {processed_dir}")

    # C. Find all JSON files
    json_pattern = os.path.join(SOURCE_FOLDER, "*.json")
    files_to_process = glob.glob(json_pattern)

    if not files_to_process:
        print("No JSON files found to process.")
        return

    print(f"Found {len(files_to_process)} files. Starting import...")

    # D. Connect and Process
    total_files = 0
    total_triples = 0
    log_messages = []

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            
            for file_path in files_to_process:
                file_name = os.path.basename(file_path)
                
                try:
                    # 1. Load JSON
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = json.load(f)

                    # 2. Extract the 'triples' list from the JSON object
                    # We use .get() to avoid crashing if 'triples' is missing
                    triples_data = file_content.get("triples", [])

                    # 3. Import if data exists
                    if isinstance(triples_data, list) and len(triples_data) > 0:
                        session.execute_write(import_triples, triples_data)
                        
                        # 4. Move file to 'processed_files' folder
                        shutil.move(file_path, os.path.join(processed_dir, file_name))
                        
                        count = len(triples_data)
                        msg = f"[SUCCESS] Imported {count} triples from {file_name}"
                        print(msg)
                        log_messages.append(msg)
                        
                        total_files += 1
                        total_triples += count
                    else:
                        # If the file has no 'triples' key or is empty
                        msg = f"[SKIPPED] {file_name} (No 'triples' list found)"
                        print(msg)
                        log_messages.append(msg)

                except Exception as e:
                    msg = f"[ERROR] Could not process {file_name}: {e}"
                    print(msg)
                    log_messages.append(msg)

    # E. Create a summary log file
    log_path = os.path.join(processed_dir, "import_log.txt")
    with open(log_path, "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n--- Batch Import: {timestamp} ---\n")
        for line in log_messages:
            log_file.write(line + "\n")
        log_file.write(f"Total: {total_files} files moved, {total_triples} triples created.\n")

    print("------------------------------------------------")
    print(f"Done! {total_files} files moved to '{OUTPUT_FOLDER_NAME}'.")

if __name__ == "__main__":
    main()