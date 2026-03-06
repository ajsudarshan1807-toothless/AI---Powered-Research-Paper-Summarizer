import spacy
import json
import os
import sys

# --- Configuration ---
# UPDATED PATH: Pointing to the folder you requested
INPUT_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\for_xlsx"
OUTPUT_FOLDER = os.path.join(INPUT_FOLDER, "extracted_output")

# Load the spaCy model
print("Loading NLP model...")
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Error: Model not found. Please run: python -m spacy download en_core_web_sm")
    sys.exit(1)

def extract_text_recursively(data):
    """
    Recursively extracts all strings from a nested JSON (dict or list)
    and joins them into a single string.
    This prevents errors if the JSON structure is complex.
    """
    if isinstance(data, str):
        return data
    elif isinstance(data, list):
        return " ".join([extract_text_recursively(item) for item in data])
    elif isinstance(data, dict):
        return " ".join([extract_text_recursively(value) for value in data.values()])
    return ""

def process_file(file_path, output_path):
    filename = os.path.basename(file_path)
    
    # 1. Load JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Skipping {filename}: Invalid JSON or encoding error ({e})")
        return

    # 2. Extract Text
    text = extract_text_recursively(data)
    
    if not text or not text.strip():
        print(f"Skipping {filename}: No valid text found inside.")
        return

    # Limit text length to avoid memory crashes on massive files
    if len(text) > 1000000:
        text = text[:1000000]

    # 3. Run NLP
    doc = nlp(text)

    # --- Entity Extraction ---
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_
        })

    # --- Relationship Extraction (Triples) ---
    triples = []
    for token in doc:
        if token.pos_ == "VERB":
            subj = []
            obj = []
            
            for child in token.children:
                if "subj" in child.dep_:
                    subj.append(child.text)
                if "obj" in child.dep_:
                    obj.append(child.text)

            if subj and obj:
                for s in subj:
                    for o in obj:
                        triples.append({
                            "subject": s,
                            "relation": token.lemma_,
                            "object": o
                        })

    # 4. Save Output
    output_data = {
        "source_file": filename,
        "entities": entities,
        "triples": triples
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Success: Processed {filename} -> Saved to extracted_output/")

def main():
    # 1. Create Output Directory if it doesn't exist
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output folder: {OUTPUT_FOLDER}")

    # 2. Find all JSON files in the INPUT_FOLDER
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: Input folder not found: {INPUT_FOLDER}")
        return

    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.json')]
    
    if not files:
        print(f"No .json files found in '{INPUT_FOLDER}'.")
        return

    print(f"Found {len(files)} JSON files in '{INPUT_FOLDER}'.\nStarting batch process...\n")

    # 3. Loop through files
    for filename in files:
        input_path = os.path.join(INPUT_FOLDER, filename)
        
        # Create a new filename for the output (e.g., file1.json -> file1_extracted.json)
        output_filename = f"{os.path.splitext(filename)[0]}_extracted.json"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        process_file(input_path, output_path)

    print("\nBatch processing complete.")

if __name__ == "__main__":
    main()