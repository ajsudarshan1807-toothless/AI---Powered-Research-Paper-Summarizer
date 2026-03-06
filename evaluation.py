import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

# --- CONFIGURATION ---
INPUT_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_json_format"
DB_FAISS_PATH = os.path.join(INPUT_FOLDER, "faiss_index")
TOP_K = 3


def get_llm():
    return OllamaLLM(model="llama3")


def build_retriever(db):
    return db.as_retriever(search_type="similarity", search_kwargs={"k": TOP_K})


def answer_with_context(question, docs):
    llm = get_llm()
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = f"""
You are a research assistant. Use only the provided context to answer the question.
If the answer is not in the context, say "I don't know based on the provided context."

Context:
{context}

Question:
{question}

Answer:
"""
    answer = llm.invoke(prompt).strip()
    return answer, context


def evaluate_answer(query, answer, context):
    """
    Uses the LLM to judge the answer quality against retrieved context.
    """
    eval_llm = get_llm()
    eval_template = f"""
You are an impartial judge. Evaluate the Question and Answer only against the Context.

Question: {query}
Answer Provided: {answer}
Context Used: {context}

Task:
1. Give Faithfulness Score (0-100): How much of the answer is supported by the context.
2. Give Confidence Score (0-100): How confident are you this answers user intent.

Output format:
Faithfulness: [Score]
Confidence: [Score]
Reasoning: [Short explanation]
"""
    return eval_llm.invoke(eval_template).strip()


def run_evaluation_suite():
    print("Loading knowledge base for evaluation...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    try:
        db = FAISS.load_local(
            DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True
        )
    except Exception as exc:
        print(f"Error loading FAISS index: {exc}")
        return

    retriever = build_retriever(db)

    while True:
        try:
            question = input("\nEnter your question: ").strip()
        except EOFError:
            print("\nNo input stream available. Ending evaluation session.")
            break
        except KeyboardInterrupt:
            print("\nEvaluation interrupted by user.")
            break
        if not question:
            print("Please enter a valid question.")
            continue

        docs = retriever.invoke(question)
        if not docs:
            print("\nNo relevant documents were retrieved.")
            continue

        answer, context = answer_with_context(question, docs)

        print(f"\nQuestion: {question}")
        print(f"\nGenerated Answer:\n{answer}\n")

        print("Calculating confidence scores...")
        evaluation = evaluate_answer(question, answer, context)

        print("\n[EVALUATION REPORT]")
        print(evaluation)
        print("-" * 60)

        try:
            cont = input("\nDo you want to ask another question? (yes/no): ").strip().lower()
        except EOFError:
            print("\nNo input stream available. Ending evaluation session.")
            break
        except KeyboardInterrupt:
            print("\nEvaluation interrupted by user.")
            break
        if cont not in {"yes", "y"}:
            print("\nEvaluation session ended.")
            break


if __name__ == "__main__":
    run_evaluation_suite()
