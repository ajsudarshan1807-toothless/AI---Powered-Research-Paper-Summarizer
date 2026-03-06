from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAPERS_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\research_papers"
INPUT_FOLDER = r"C:\Users\sudarshan\.vscode\AIML_for_infosys\research_paper_json_format"
DB_FAISS_PATH = os.path.join(INPUT_FOLDER, "faiss_index")

# Use a lightweight default model for low-RAM systems.
LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
TOP_K = 3
SUMMARY_MAX_CHARS = 32000
LOW_TRUST_THRESHOLD = 60


def get_llm():
    return OllamaLLM(model=LLM_MODEL)


def score_from_text(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return 0
    value = int(match.group(1))
    return max(0, min(100, value))


def extract_score(label, text):
    cleaned = (text or "").replace("**", "").replace("__", "")
    patterns = [
        rf"\b{label}\b\s*(?:score)?\s*[:=\-]\s*(\d{{1,3}})(?!\d)",
        rf"\b{label}\b\s*(?:score)?\s*\(\s*0\s*[-–]\s*100\s*\)\s*[:=\-]?\s*(\d{{1,3}})(?!\d)",
        rf"\b{label}\b\s*(?:score)?\s*[:=\-]?\s*(\d{{1,3}})\s*%",
        rf"\b{label}\b\s*(?:score)?\s*[:=\-]?\s*(\d{{1,3}})\s*/\s*100",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            return max(0, min(100, int(match.group(1))))
    return None


def fallback_score_list(text):
    values = []
    cleaned = (text or "").replace("**", "").replace("__", "")
    for match in re.finditer(r"(\d{1,3})\s*(?:%|/\s*100)", cleaned):
        values.append(max(0, min(100, int(match.group(1)))))
    return values


def force_extract_scores(evaluation_text):
    extractor_prompt = f"""
Extract the two scores from the evaluation text.
Return exactly:
Faithfulness: <integer 0-100>
Confidence: <integer 0-100>

Evaluation text:
{evaluation_text}
"""
    extracted = get_llm().invoke(extractor_prompt).strip()
    return (
        extract_score("Faithfulness", extracted),
        extract_score("Confidence", extracted),
    )


def natural_sort_key(text):
    parts = re.split(r"(\d+)", text.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def load_available_json_sources(folder):
    try:
        sources = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        return {name.lower(): name for name in sources}
    except Exception:
        return {}


def resolve_source_from_selected_file(selected_file):
    name = os.path.basename((selected_file or "").strip())
    if not name:
        return None

    # Allow direct JSON source selection if ever needed.
    if name.lower().endswith(".json"):
        return AVAILABLE_JSON_SOURCES.get(name.lower())

    # Map PDF names like "research paper_3.pdf" -> "output3.json".
    number_match = re.search(r"(\d+)(?!.*\d)", name)
    if not number_match:
        return None

    candidate = f"output{int(number_match.group(1))}.json"
    return AVAILABLE_JSON_SOURCES.get(candidate.lower())


def get_docs_for_source(selected_source):
    total = max(int(getattr(db.index, "ntotal", TOP_K)), TOP_K)

    # Explicitly query FAISS with source filter and wide fetch window.
    filtered_docs = db.similarity_search(
        "full paper summary",
        k=total,
        fetch_k=total,
        filter={"source": selected_source},
    )
    if not filtered_docs:
        return []

    # Return chunks in index insertion order for coherent summarization.
    ordered_docs = []
    index_map = getattr(db, "index_to_docstore_id", {})
    if isinstance(index_map, dict):
        for idx in sorted(index_map.keys()):
            doc_id = index_map[idx]
            doc = db.docstore.search(doc_id)
            if hasattr(doc, "metadata") and doc.metadata.get("source") == selected_source:
                ordered_docs.append(doc)

    return ordered_docs or filtered_docs


def truncate_for_summary(text, max_chars=SUMMARY_MAX_CHARS):
    if len(text) <= max_chars:
        return text

    # Keep representative sections from beginning, middle, and end.
    segment = max_chars // 3
    mid_start = max((len(text) // 2) - (segment // 2), 0)
    middle = text[mid_start : mid_start + segment]
    return (
        f"{text[:segment].rstrip()}\n\n"
        "[...middle excerpt...]\n\n"
        f"{middle.strip()}\n\n"
        "[...final excerpt...]\n\n"
        f"{text[-segment:].lstrip()}"
    )


def normalize_history(history):
    if not isinstance(history, list):
        return []

    normalized = []
    for turn in history[-3:]:
        if not isinstance(turn, dict):
            continue
        question = (turn.get("question") or "").strip()
        answer = (turn.get("answer") or "").strip()
        if question or answer:
            normalized.append({"question": question, "answer": answer})
    return normalized


def format_history(history):
    if not history:
        return "No previous conversation turns."

    lines = []
    for idx, turn in enumerate(history[-3:], start=1):
        lines.append(f"Turn {idx} Question: {turn['question'] or 'N/A'}")
        lines.append(f"Turn {idx} Answer: {turn['answer'] or 'N/A'}")
    return "\n".join(lines)


print("Loading FAISS index...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
AVAILABLE_JSON_SOURCES = load_available_json_sources(INPUT_FOLDER)


@app.route("/", methods=["GET"])
@app.route("/rag_dashboard.html", methods=["GET"])
def dashboard():
    return send_from_directory(BASE_DIR, "rag_dashboard.html")


@app.route("/files", methods=["GET"])
def list_files():
    try:
        files = [f for f in os.listdir(PAPERS_FOLDER) if f.lower().endswith(".pdf")]
        files.sort(key=natural_sort_key)
        return jsonify(files)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        data = request.get_json(silent=True) or {}
        selected_file = (data.get("file") or "").strip()

        if not selected_file:
            return jsonify({"error": "No document selected"}), 400

        selected_source = resolve_source_from_selected_file(selected_file)
        if not selected_source:
            return (
                jsonify(
                    {
                        "error": (
                            f"Unable to map selected file '{selected_file}' "
                            "to indexed JSON source."
                        )
                    }
                ),
                400,
            )

        source_docs = get_docs_for_source(selected_source)
        if not source_docs:
            return (
                jsonify(
                    {
                        "error": (
                            f"No indexed chunks found for '{selected_file}'. "
                            "Please rebuild FAISS index."
                        )
                    }
                ),
                404,
            )

        source_text = "\n\n".join(
            doc.page_content.strip() for doc in source_docs if doc.page_content.strip()
        )
        if not source_text:
            return (
                jsonify({"error": f"No text content found for '{selected_file}'."}),
                404,
            )

        context_for_summary = truncate_for_summary(source_text)
        summary_prompt = f"""
Return structured output in clean markdown format:

Title (if available)

Research Objective

Methodology

Key Findings

Conclusion

Important Technical Terms

Use ONLY the provided context.
Do NOT hallucinate.
If information missing, state "Not specified in paper."

Context:
{context_for_summary}
"""
        summary = get_llm().invoke(summary_prompt).strip()

        return jsonify(
            {
                "summary": summary,
                "selected_file": selected_file,
                "selected_source": selected_source,
            }
        )
    except Exception as exc:
        return jsonify({"error": "Summary generation failed", "details": str(exc)}), 500


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        selected_file = (data.get("file") or "").strip()
        summary = (data.get("summary") or "").strip()
        raw_history = data.get("history", [])
        if not isinstance(raw_history, list):
            raw_history = []
        raw_history = raw_history[-6:]

        history = []
        for msg in raw_history:
            if not isinstance(msg, dict):
                continue

            role = (msg.get("role") or "").strip().lower()
            content = (msg.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                history.append({"role": role, "content": content})
                continue

            # Backward compatibility for existing UI history format.
            prev_question = (msg.get("question") or "").strip()
            prev_answer = (msg.get("answer") or "").strip()
            if prev_question:
                history.append({"role": "user", "content": prev_question})
            if prev_answer:
                history.append({"role": "assistant", "content": prev_answer})

        history = history[-6:]
        conversation_context = ""
        for msg in history:
            if msg["role"] == "user":
                conversation_context += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation_context += f"Assistant: {msg['content']}\n"

        if not question:
            return jsonify({"error": "No question provided"}), 400
        if not selected_file:
            return jsonify({"error": "No document selected"}), 400
        if not summary:
            return jsonify({"error": "Summary is required. Generate summary first."}), 400

        selected_source = resolve_source_from_selected_file(selected_file)
        if not selected_source:
            return (
                jsonify(
                    {
                        "error": (
                            f"Unable to map selected file '{selected_file}' "
                            "to indexed JSON source."
                        )
                    }
                ),
                400,
            )

        rewritten_question = question
        if conversation_context.strip():
            rewrite_prompt = f"""
Rewrite the follow-up question into a standalone question.

If the question already makes sense alone, return it unchanged.
Return ONLY the standalone question text.

Conversation History:
{conversation_context}

User Question:
{question}

Standalone Question:
"""
            rewritten_question = get_llm().invoke(rewrite_prompt).strip()
            rewritten_question = rewritten_question.splitlines()[0].strip()
            rewritten_question = re.sub(
                r"^(?:Standalone Question|Rewritten Question)\s*:\s*",
                "",
                rewritten_question,
                flags=re.IGNORECASE,
            ).strip().strip("\"'")
            if not rewritten_question:
                rewritten_question = question

        print(f"[ASK] Selected file: {selected_file} -> source: {selected_source}")
        print(f"[CHAT MEMORY] Using {len(history)} history messages")
        print(f"[QUERY REWRITE] Original: {question}")
        print(f"[QUERY REWRITE] Rewritten: {rewritten_question}")

        fetch_k = max(int(getattr(db.index, "ntotal", TOP_K)), TOP_K)
        docs = db.similarity_search(
            rewritten_question,
            k=TOP_K,
            fetch_k=fetch_k,
            filter={"source": selected_source},
        )
        if not docs and rewritten_question != question:
            docs = db.similarity_search(
                question,
                k=TOP_K,
                fetch_k=fetch_k,
                filter={"source": selected_source},
            )
            print("[QUERY REWRITE] Fallback to original question for retrieval.")

        print(f"[RETRIEVAL] fetch_k={fetch_k}, docs={len(docs)}")
        if docs:
            retrieved_sources = sorted(
                {str(doc.metadata.get("source", "")) for doc in docs if hasattr(doc, "metadata")}
            )
            print(f"[RETRIEVAL] Sources: {retrieved_sources}")

        meaningful_docs = [
            doc for doc in docs if len((doc.page_content or "").strip()) >= 80
        ]
        if meaningful_docs:
            docs = meaningful_docs[:TOP_K]

        if not docs:
            return (
                jsonify(
                    {
                        "error": (
                            f"No indexed chunks found for '{selected_file}'. "
                            "Please rebuild FAISS index."
                        )
                    }
                ),
                404,
            )
        context = "\n\n".join(doc.page_content for doc in docs)

        answer_prompt = f"""
You are a research assistant.

Answer ONLY using the provided paper summary and retrieved context.
Use previous conversation only to resolve references like "it", "they", or "this method".
For broad questions (for example "what is this paper about?" or "summarize this paper"),
prioritize the paper summary.

Paper Summary:
{summary}

Previous Conversation:
{conversation_context}

Retrieved Context:
{context}

Question:
{question}

If the answer is not found in both the summary and retrieved context, respond:
"I don't know."
"""
        answer = get_llm().invoke(answer_prompt).strip()

        eval_prompt = f"""
You are an impartial judge.

Question: {question}
Answer: {answer}
Paper Summary: {summary}
Retrieved Context: {context}

Return exactly these 3 lines in plain text (no markdown, no extra fields):
Faithfulness: <integer 0-100>
Confidence: <integer 0-100>
Reasoning: <short explanation>
Always provide integer values for both Faithfulness and Confidence.
If the answer is exactly "I don't know.", confidence should be low unless both summary and context clearly lack the answer.
"""
        evaluation = get_llm().invoke(eval_prompt).strip()

        faith = extract_score("Faithfulness", evaluation)
        conf = extract_score("Confidence", evaluation)

        # Fallback: some models still emit free-form percentages like "70%" or "85/100".
        if faith is None or conf is None:
            overall = extract_score("Overall Assessment", evaluation)
            values = fallback_score_list(evaluation)
            if faith is None:
                faith = values[0] if values else overall
            if conf is None:
                conf = values[1] if len(values) > 1 else overall

        # Last resort: ask model to extract numeric fields from its own evaluation text.
        if faith is None or conf is None:
            forced_faith, forced_conf = force_extract_scores(evaluation)
            if faith is None:
                faith = forced_faith
            if conf is None:
                conf = forced_conf

        faith = 0 if faith is None else faith
        conf = 0 if conf is None else conf

        # --- Low Trust Safety Override ---
        faithfulness = faith
        confidence = conf
        if (
            isinstance(faithfulness, (int, float))
            and isinstance(confidence, (int, float))
            and (
                faithfulness < LOW_TRUST_THRESHOLD
                or confidence < LOW_TRUST_THRESHOLD
            )
        ):
            print(
                f"[LOW TRUST] Faithfulness: {faithfulness}, "
                f"Confidence: {confidence}"
            )
            answer = "I don't know."

        cleaned_eval = evaluation.replace("**", "").replace("__", "")
        reason = re.search(r"Reasoning:\s*(.*)", cleaned_eval, re.IGNORECASE | re.S)

        return jsonify(
            {
                "answer": answer,
                "context": context,
                "faithfulness": faith,
                "confidence": conf,
                "reasoning": reason.group(1).strip() if reason else evaluation,
                "selected_file": selected_file,
                "selected_source": selected_source,
            }
        )
    except Exception as exc:
        return jsonify({"error": "Request failed", "details": str(exc)}), 500


if __name__ == "__main__":
    print(f"Using model: {LLM_MODEL}")
    print("Open dashboard: http://127.0.0.1:5000/")
    app.run(host="127.0.0.1", port=5000, debug=False)
