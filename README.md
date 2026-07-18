# From Raw Documents to Graph Intelligence
## Catching Insurance Fraud with LangChain, Neo4j & Python

> **PyCon Ghana 2026 Workshop** · August 20–22, 2026  
> **Presenter:** Shadrack Bentil — GitHub Campus Expert  
> **Duration:** 2 Hours · Hands-On · Intermediate Python

---

## What You Will Build

A production-grade document intelligence pipeline that:

1. **Ingests** messy insurance PDFs (claim forms, medical reports, invoices, police reports)
2. **Extracts** structured entities using LangChain + an LLM (OpenAI or Gemini)
3. **Maps** those entities into a Neo4j Knowledge Graph
4. **Queries** the graph with Cypher to **expose hidden fraud rings**

> Graph databases shine across health, education, legal, and insurance — but today we're going to build something that actually catches criminals.

By the end, your graph will catch what flat databases cannot — a ring of colluding doctors, ghost witnesses, and identity fraudsters hiding across 36 documents.

---

## Repository Structure

```
insurance-fraud-doc-intelligence/
│
├── README.md                        ← You are here
├── .env.example                     ← Copy to .env and add your keys
├── requirements.txt                 ← All Python dependencies
│
├── data/
│   └── sample_docs/                 ← 36 synthetic Ghana insurance PDFs
│
├── starter/                         ← YOUR WORKING FILES (workshop)
│   ├── schemas.py                   ← Pydantic output schemas (pre-built)
│   ├── 01_extract.py                ← Phase 2: Extraction skeleton
│   ├── 02_graph.py                  ← Phase 3: Graph population skeleton
│   └── 03_query.py                  ← Phase 4: Fraud detection queries
│
├── final/                           ← REFERENCE SOLUTIONS (don't peek early)
│   ├── README.md
│   ├── 01_extract.py                ← Complete Phase 2
│   ├── 02_graph.py                  ← Complete Phase 3
│   └── 03_query.py                  ← Complete Phase 4
│
├── bonus/                           ← OPTIONAL (if time) Investigator Chat UI
│   ├── README.md
│   ├── app.py                       ← Streamlit NL → Cypher chat
│   └── nl2cypher.py                 ← Fully written agent (walkthrough)
│
├── docs/
│   ├── NEO4J_SETUP.md               ← AuraDB + Desktop setup walkthrough
│   ├── GRAPH_MODEL.md               ← Node/relationship schema explained
│   └── CYPHER_CHEATSHEET.md         ← Quick Cypher reference
│
├── tests/
│   └── test_extraction.py           ← pytest integration checks
│
└── .github/
    └── workflows/
        └── ci.yml                   ← GitHub Actions CI pipeline
```

---

## Quick Start (Do This Before the Workshop)

### 1. Fork & Clone

```bash
# Fork https://github.com/qbentil/insurance-fraud-doc-intelligence on GitHub, then clone YOUR fork:
git clone https://github.com/{YOUR_USERNAME}/insurance-fraud-doc-intelligence.git
cd insurance-fraud-doc-intelligence

# Or clone the workshop repo directly:
# git clone https://github.com/qbentil/insurance-fraud-doc-intelligence.git
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
cp .env.example .env
# Open .env and add:
# - Your OpenAI or Google Gemini API key
# - LLM_PROVIDER=openai  or  LLM_PROVIDER=gemini
# - Your Neo4j connection details
```

### 5. Set Up Neo4j (choose one)

Full walkthrough: **[`docs/NEO4J_SETUP.md`](docs/NEO4J_SETUP.md)** (AuraDB Free + Neo4j Desktop).

**Option A — Neo4j AuraDB Free (Recommended, cloud, no install)**
1. Go to [console.neo4j.io](https://console.neo4j.io)
2. Create a free instance (save the password when shown)
3. Copy URI (`neo4j+s://...`), username, and password into `.env`

**Option B — Neo4j Desktop (local)**
1. Download from [neo4j.com/download](https://neo4j.com/download)
2. Create a local DBMS, set a password, click **Start**
3. Use `NEO4J_URI=bolt://localhost:7687` in `.env`

### 6. Verify Your Setup

```bash
python starter/schemas.py
# Should print: ✅ Setup verified. Ready for the workshop!
```

---

## Workshop Phases

| Phase | Time | File | What Happens |
|-------|------|------|-------------|
| **0 — Setup** | 15 min | — | Fork, clone, secrets check, Neo4j connect |
| **1 — Extract** | 35 min | `starter/01_extract.py` | LangChain parses PDFs → structured JSON |
| **2 — Graph** | 45 min | `starter/02_graph.py` | JSON entities → Neo4j nodes & relationships |
| **3 — Query** | 25 min | `starter/03_query.py` | Cypher queries expose the fraud rings |
| **Bonus** | if time | `bonus/app.py` | NL → Cypher investigator chat with the graph |

> Stuck after the session? Compare your work to [`final/`](final/) — complete solutions with step comments.

---

## API Key Safety

> **Never commit your `.env` file to GitHub.**

Your `.env` is already in `.gitignore`. To double-check:

```bash
git status   # .env should NOT appear here
```

With GitHub Copilot, you can generate boilerplate safely — but always review before committing. Use `git diff` before every push.

---

## Prerequisites

Before attending the workshop, ensure you have:

- [ ] Python 3.10–3.12 installed (recommended; 3.11 used in CI)
- [ ] Git configured with your GitHub account
- [ ] VS Code + Python extension installed
- [ ] GitHub Copilot extension installed (recommended)
- [ ] Neo4j AuraDB free instance **OR** Neo4j Desktop running
- [ ] OpenAI **or** Google Gemini API key with minimal credits
- [ ] This repo forked and cloned locally
- [ ] `python starter/schemas.py` runs without errors

---

## About the Dataset

The `data/sample_docs/` folder contains **36 synthetic insurance documents** set in Ghana:
- Policy certificates, claim forms, medical reports, provider invoices, police reports
- All names, amounts, and institutions are fictional
- **3 fraud rings are hidden in the data** — your graph will find them

---

## Bonus (if time) — Investigator Chat

After Phase 4, chat with the graph in natural language:

```bash
streamlit run bonus/app.py
```

Details: [`bonus/README.md`](bonus/README.md). Skip this folder during the core workshop.

---

## Contributing

Found a bug or want to improve the workshop materials?  
Open an issue or submit a PR — contributions welcome!

---

## License

MIT — free to use, adapt, and share with attribution.

---

*Built for PyCon Ghana 2026 · Powered by GitHub Education*
