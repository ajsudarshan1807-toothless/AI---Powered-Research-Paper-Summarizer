import os

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM   # ✅ New Ollama import
from langchain_openai import ChatOpenAI


# --- CHOOSE YOUR LLM HERE ---
USE_LOCAL_LLM = True 

# --- CONFIGURATION ---
INPUT_FOLDER = r'C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_json_format'
DB_FAISS_PATH = os.path.join(INPUT_FOLDER, 'faiss_index')


def get_llm():
    """
    Returns the LLM object based on configuration.
    """
    if USE_LOCAL_LLM:
        print("Initializing Local LLM (Ollama)...")
        return OllamaLLM(model="llama3")
    else:
        print("Initializing Cloud LLM (OpenAI)...")
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


def rag_pipeline(query):
    # 1️⃣ Load the Vector Database
    print("Loading Knowledge Base...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    try:
        db = FAISS.load_local(
            DB_FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"Error loading FAISS DB: {e}")
        return

    # 2️⃣ Create Retriever
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    # 3️⃣ Prompt Template
    prompt_template = """
You are a research assistant. Use the following context to answer the question.
If the answer is not in the context, say you don't know.

Context:
{context}

Question:
{question}

Summarized Answer:
"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
    )

    # 4️⃣ Initialize LLM
    llm = get_llm()

    # 5️⃣ Build Modern RAG Chain (LCEL)
    rag_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # 6️⃣ Run Query
    print(f"\nProcessing Query: '{query}'...")
    response = rag_chain.invoke(query)

    # 7️⃣ Print Answer
    print("\n" + "=" * 50)
    print("FINAL LLM ANSWER:")
    print("=" * 50)
    print(response)

    # 8️⃣ (Optional) Show Sources Manually
    print("\n" + "-" * 50)
    print("Sources Used:")
    docs = retriever.invoke(query)
    for doc in docs:
        print(f"- {doc.metadata.get('source', 'Unknown')}")


if __name__ == "__main__":
    user_question = "tell me what is MasterNet Backbone?"

    rag_pipeline(user_question)
