# AIML_for_infosys

Summarize-first Research Paper Assistant built with Flask, FAISS, and Ollama.

## Latest Updates

- Frontend is a light-theme academic copilot UI.
- Left heading updated to: `AI - Powered Research Paper Summarizer`.
- Added `Copy Summary` button in the summary panel.
- Added chat-memory-aware query rewriting in `/ask` for follow-up questions.
- `/ask` now normalizes up to the last 6 history messages (3 turns) and supports:
  - new format: `{ "role": "user|assistant", "content": "..." }`
  - legacy format: `{ "question": "...", "answer": "..." }`
- Source-filtered retrieval in `/ask` now uses wider `fetch_k` and falls back to the original question if rewritten-query retrieval fails.
- `/ask` now prefers meaningful chunks (filters very short heading-only chunks when possible).
- Evaluation prompt now checks answer grounding against both paper summary and retrieved context.
- Added low-trust safety override in backend:
  - if `faithfulness < 60` or `confidence < 60`
  - final returned `answer` is set to `"I don't know."`
  - all other response fields remain unchanged.

## 1. System Workflow

1. User selects a PDF from `research_papers/`.
2. Backend maps PDF to JSON source (for example `research paper_3.pdf` -> `output3.json`).
3. `POST /summarize` generates structured summary using source-filtered FAISS chunks.
4. User asks questions in chat.
5. `POST /ask` answers using:
   - generated summary
   - chat history memory (last 6 messages / 3 turns)
   - query rewriting for follow-up questions
   - source-filtered retrieved chunks (with rewritten query)
6. Backend evaluates answer and returns:
   - faithfulness (0-100)
   - confidence (0-100)
   - reasoning
7. Low-trust rule is applied after scores are parsed:
   - if either score is below `60`, answer is overridden to `"I don't know."`

## 2. Tech Stack

- Backend: Flask, Flask-CORS
- Retrieval: FAISS + sentence-transformers embeddings
- LLM: Ollama via `langchain_ollama`
- Frontend: single-file HTML/CSS/JS (`rag_dashboard.html`)

## 3. Key Files

- `server.py`: API routes, source mapping, retrieval, summary generation, query rewrite + chat-memory ask flow, evaluation parsing, low-trust override.
- `rag_dashboard.html`: light-theme summarize + chat copilot UI; sends role/content history messages for `/ask`.
- `Agile_Document/`: agile + QA documents (see `Agile_Document/README.md`).
- `chunking.py`: builds FAISS index from `research_paper_json_format/*.json`.
- `test_retrieval.py`: retrieval smoke test.
- `evaluation.py`: CLI evaluation loop.

Data folders:
- `research_papers/` (PDF files)
- `research_paper_json_format/` (JSON files + `faiss_index/`)

## 4. Setup (Windows PowerShell)

Recommended Python: `3.12`

```powershell
cd C:\Users\sudarshan\.vscode\AIML_for_infosys
py -3.12 -m venv .venv312_clean
.\.venv312_clean\Scripts\Activate.ps1
python --version
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv312_clean\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install --upgrade pip
pip install flask flask-cors langchain langchain-community langchain-core langchain-huggingface langchain-ollama langchain-openai langchain-text-splitters sentence-transformers faiss-cpu neo4j spacy python-docx pandas openpyxl docling
python -m spacy download en_core_web_sm
```

## 5. Ollama Runtime

```powershell
ollama pull llama3.2:1b
ollama serve
```

Optional model override:

```powershell
$env:OLLAMA_MODEL="llama3.2:1b"
```

## 6. Build/Rebuild FAISS Index

Run when JSON content changes:

```powershell
cd C:\Users\sudarshan\.vscode\AIML_for_infosys
.\.venv312_clean\Scripts\python.exe chunking.py
```

Index output path:
- `research_paper_json_format\faiss_index`

## 7. Run Application

```powershell
cd C:\Users\sudarshan\.vscode\AIML_for_infosys
.\.venv312_clean\Scripts\python.exe server.py
```

Open:
- `http://127.0.0.1:5000/`

Restart:
- `Ctrl + C` then run `server.py` again.

## 8. API Reference

### `GET /files`

Returns naturally sorted PDF list.

Example:

```json
[
  "research paper_1.pdf",
  "research paper_2.pdf",
  "research paper_3.pdf"
]
```

### `POST /summarize`

Request:

```json
{
  "file": "research paper_3.pdf"
}
```

Response:

```json
{
  "summary": "## Title ...",
  "selected_file": "research paper_3.pdf",
  "selected_source": "output3.json"
}
```

### `POST /ask`

Request:

```json
{
  "question": "What are the key limitations?",
  "file": "research paper_3.pdf",
  "summary": "## Title ...",
  "history": [
    { "role": "user", "content": "What is osteoporosis?" },
    { "role": "assistant", "content": "Osteoporosis is..." },
    { "role": "user", "content": "What are its symptoms?" }
  ]
}
```

Notes:
- Backend keeps only the latest 6 history messages.
- Backend also accepts legacy history turns:
  - `{ "question": "...", "answer": "..." }`

Response:

```json
{
  "answer": "... or \"I don't know.\" if low trust",
  "context": "...",
  "faithfulness": 82,
  "confidence": 77,
  "reasoning": "...",
  "selected_file": "research paper_3.pdf",
  "selected_source": "output3.json"
}
```

Error shape:

```json
{
  "error": "message",
  "details": "optional details"
}
```

## 9. Frontend Behavior

`rag_dashboard.html` behavior:

- Full-screen split layout (left summary panel, right chat panel).
- Left panel:
  - heading: `AI - Powered Research Paper Summarizer`
  - paper selector + summary generation status
  - animated loader while summary is generating
  - persistent summary display
  - `Copy Summary` button (clipboard copy)
- Right panel:
  - chat-style Q/A bubbles
  - auto-scroll to latest message
  - animated faithfulness/confidence bars
  - collapsible `View Sources` section
  - send button with keyboard support (`Ctrl/Cmd + Enter`)

State behavior:
- selecting a new paper resets chat and regenerates summary
- summary stays visible while chatting
- ask request sends role/content history messages built from the last 3 turns (max 6 messages)

## 10. Validation Commands

Retrieval smoke test:

```powershell
.\.venv312_clean\Scripts\python.exe test_retrieval.py
```

CLI evaluation:

```powershell
.\.venv312_clean\Scripts\python.exe evaluation.py
```

## 11. Troubleshooting

### Summary looks unrelated to selected paper
- Rebuild FAISS index with `chunking.py`.
- Restart backend.
- Confirm selected PDF exists in `research_papers/`.

### Confidence/Faithfulness appears low or answer becomes "I don't know."
- This can be expected due to low-trust safety override (`threshold = 60`).
- Review retrieved context and reasoning.
- Use a clearer question tied to the selected paper.
- For broad prompts like "What is this paper about?", the summary is prioritized, but better results may require a stronger Ollama model than `llama3.2:1b`.

### Answer is irrelevant or reasoning looks off-topic
- Check backend logs:
  - `[ASK] Selected file ... -> source ...`
  - `[QUERY REWRITE] Original / Rewritten`
  - `[RETRIEVAL] Sources: [...]`
- Confirm retrieved source matches the selected file mapping.
- Restart backend after updates to ensure latest `/ask` logic is active.

### View Sources shows heading-only context (for example, `INTRODUCTION.`)
- `/ask` now prefers meaningful chunks and filters very short chunks when possible.
- If issue persists, rebuild FAISS index and restart server.

### Scores show 0 unexpectedly
- Restart backend after updates.
- Ensure Ollama is running and responsive.
- Check backend logs for parsing issues.

### Dropdown order is `1,10,11,...`
- Natural sorting is implemented.
- Hard refresh browser (`Ctrl + F5`) after restart.

### "No indexed chunks found"
- Source mapping missing in index.
- Rebuild FAISS and restart server.

## 12. Contributor Notes

- Keep `chunking.py` stable unless intentionally changing indexing strategy.
- Preserve per-source retrieval filtering in `server.py`.
- Preserve API contracts used by `rag_dashboard.html`.
- Do not change request/response format without updating frontend and docs together.
- Restart backend after `server.py` edits; hard refresh frontend after UI edits.
- When modifying `/ask`, keep query-rewrite, history normalization, and low-trust override behavior aligned with frontend payloads.
