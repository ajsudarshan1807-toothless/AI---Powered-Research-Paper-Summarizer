import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- CONFIGURATION ---
# 1. Input Folder (Relative path to where your script runs)
INPUT_FOLDER = 'research_paper_json_format' 

# 2. Output Folder (Created INSIDE the input folder as requested)
# The vector database will be saved at: research_paper_json_format/faiss_index
DB_FAISS_PATH = os.path.join(INPUT_FOLDER, 'faiss_index')

# Chunking settings
CHUNK_SIZE = 1000      
CHUNK_OVERLAP = 200

def extract_text_from_docling_json(json_data):
    """
    Parses complex Docling JSON format.
    Traverses body -> children -> (texts/groups/pictures) to extract readable text.
    """
    full_text_list = []

    # Helper to find the actual object in the JSON using the "$ref" string
    def get_element_by_ref(ref):
        try:
            # Ref format is usually "#/texts/0" or "#/groups/1"
            clean_ref = ref.lstrip('#/')
            parts = clean_ref.split('/')
            collection = parts[0]  # e.g., 'texts', 'groups'
            index = int(parts[1])  # e.g., 0, 1
            return json_data.get(collection, [])[index]
        except (ValueError, IndexError, KeyError):
            return None

    # Recursive function to process any node (body, group, picture)
    def process_node(node):
        # 1. If this node has text content, add it (Skip headers/footers)
        if 'text' in node:
            label = node.get('label', '')
            # Filter out headers and footers to keep data clean
            if label not in ['page_header', 'page_footer']:
                full_text_list.append(node['text'])

        # 2. If this node has children (groups, pictures, or the body itself), process them
        if 'children' in node:
            for child_ref_obj in node['children']:
                ref = child_ref_obj.get('$ref')
                if ref:
                    child_node = get_element_by_ref(ref)
                    if child_node:
                        process_node(child_node)

    # Start processing from the 'body' root
    root_body = json_data.get('body', {})
    if root_body:
        process_node(root_body)
    
    return "\n\n".join(full_text_list)

def load_json_data(folder_path):
    documents = []
    metadatas = []
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        print("Please check if the folder name is correct.")
        return [], []

    print(f"Loading data from: {folder_path}...")
    
    files_found = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            files_found += 1
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # EXTRACT TEXT using the Docling logic
                    text_content = extract_text_from_docling_json(data)
                    
                    if text_content:
                        documents.append(text_content)
                        metadatas.append({"source": filename})
                        print(f"  - Processed: {filename}")
                    else:
                        print(f"  - Warning: No valid text in {filename}")
                        
            except Exception as e:
                print(f"  - Error reading {filename}: {e}")
    
    if files_found == 0:
        print("No .json files found in the directory.")
                
    return documents, metadatas

def create_chunks_and_vector_db():
    # 1. Load Data
    texts, metadatas = load_json_data(INPUT_FOLDER)
    
    if not texts:
        print("No text data found. Stopping.")
        return

    print(f"\nLoaded {len(texts)} documents. Starting chunking...")

    # 2. Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    docs = text_splitter.create_documents(texts, metadatas=metadatas)
    
    print(f"Split into {len(docs)} chunks.")
    if len(docs) > 0:
        print(f"Sample Chunk Preview:\n---\n{docs[0].page_content[:200]}\n---") 

    # 3. Embeddings
    print("Generating embeddings (Downloading model if first time)...")
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

    # 4. Store in FAISS
    print(f"Saving vector database to: {DB_FAISS_PATH}")
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(DB_FAISS_PATH)
    print("Success! RAG Pipeline ready.")

if __name__ == "__main__":
    create_chunks_and_vector_db()