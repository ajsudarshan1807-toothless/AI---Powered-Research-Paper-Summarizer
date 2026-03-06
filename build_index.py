import os
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

INPUT_FOLDER = "C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_json_format"
OUTPUT_FOLDER = os.path.join(INPUT_FOLDER, "faiss_index")

documents = []

# load JSON research papers
for file in os.listdir(INPUT_FOLDER):
    if file.endswith(".json"):
        with open(os.path.join(INPUT_FOLDER, file), "r", encoding="utf-8") as f:
            data = json.load(f)

            # adjust based on your JSON structure
            text = data.get("text", "")
            documents.append(Document(page_content=text))

print("Creating embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Building FAISS index...")
db = FAISS.from_documents(documents, embeddings)

db.save_local(OUTPUT_FOLDER)

print("✅ FAISS index created successfully!")
