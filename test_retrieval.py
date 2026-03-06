import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# --- CONFIGURATION ---
# Use the exact same path where you saved the DB
INPUT_FOLDER = r'C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_json_format' 
DB_FAISS_PATH = os.path.join(INPUT_FOLDER, 'faiss_index')

def test_rag_retrieval():
    print("Loading Vector Database...")
    
    # 1. Load the Embedding Model (Must be the same one used in chunking)
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    
    # 2. Load the Database
    # We allow dangerous deserialization because we created the file ourselves
    try:
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"Error loading database: {e}")
        return

    # 3. Ask a Test Question
    # (Try changing this to something specific to your research papers)
    query = "What is the proposed system for smart agriculture?"
    
    print(f"\nQuerying: '{query}'")
    print("-" * 50)

    # 4. Retrieve Top 3 Matches
    results = db.similarity_search(query, k=3)

    if not results:
        print("No results found.")
    else:
        for i, doc in enumerate(results):
            print(f"\n[Result {i+1}]")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Content snippet: {doc.page_content[:300]}...") # Show first 300 chars
            print("-" * 50)

if __name__ == "__main__":
    test_rag_retrieval()