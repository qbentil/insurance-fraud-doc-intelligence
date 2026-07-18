# Bonus — Investigator Chat

> Optional. Only open this folder **if time remains** after Phase 4.

Chat with the fraud graph in natural language. The app turns your question into
read-only Cypher, runs it on Neo4j, and answers like a fraud investigator —
confirming the same rings you found by hand in `starter/03_query.py`.

## Prerequisites

1. `.env` configured (`LLM_PROVIDER`, API key, Neo4j)
2. Graph already loaded (`python starter/02_graph.py` succeeded)
3. Dependencies installed (`pip install -r requirements.txt`)

## Run

From the **repo root** (with your virtualenv activated):

```bash
source .venv/bin/activate   # or: source venv/bin/activate
streamlit run bonus/app.py

# If `streamlit` is not found:
python -m streamlit run bonus/app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

If the process dies with `zsh: segmentation fault` after a question (macOS):

1. Restart with: `streamlit run bonus/app.py` (config sets `fileWatcherType = none`)
2. The app runs each investigation in a **subprocess** so a gRPC crash should not kill the UI
3. Ensure the graph is loaded (`python final/02_graph.py`)

## What to demo

Click the template chips in order:

1. Doctors across the most claims  
2. Same doctor **and** provider (Ring A)  
3. Witness on multiple claims (Ring B)  
4. Same phone, different names (Ring C)  
5. Providers billing above average  
6. Claimant network via shared doctors  

Expand **Cypher used** on each answer — that is the same investigation pattern
as the hand-written Phase 4 queries.

## Code walkthrough (facilitator)

| File | Role |
|------|------|
| [`nl2cypher.py`](nl2cypher.py) | NL → Cypher → read-only guard → Neo4j → summary |
| [`llm.py`](llm.py) | OpenAI / Gemini via `LLM_PROVIDER` |
| [`schema_context.py`](schema_context.py) | Graph schema injected into the prompt |
| [`app.py`](app.py) | Streamlit Investigator Chat UI |

Start with `nl2cypher.py` — that is the entire bonus architecture in one file.
