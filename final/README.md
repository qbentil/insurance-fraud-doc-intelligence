# Final — Reference Solutions

> **Facilitator / self-check only.**  
> Keep this folder closed during live participant coding.  
> Open it to verify answers, demo a stuck room, or rehearse the pipeline.

These files are the **complete** versions of the workshop TODOs in `starter/`.  
Line-by-line comments mark each former TODO step.

| File | Phase | What it completes |
|------|-------|-------------------|
| [`01_extract.py`](01_extract.py) | 2 | Multimodal PDF classify + structured extract |

| [`02_graph.py`](02_graph.py) | 3 | Neo4j connect, constraints, all writers |
| [`03_query.py`](03_query.py) | 4 | All six fraud Cypher queries |

`starter/schemas.py` is already complete — both `starter/` and `final/` import it.  
`bonus/` is already complete — no duplicate here.

## How to run (repo root)

```bash
source .venv/bin/activate   # or your venv
# .env must have LLM + Neo4j credentials

python final/01_extract.py   # all PDFs → results/by_file/ + aggregates
python final/02_graph.py     # reads results/combined.json → Neo4j
python final/03_query.py     # → fraud ring tables
```

Cheap smoke test (one PDF; writes `results/by_file/<stem>.json` and refreshes aggregates):

```bash
python final/01_extract.py --file 01_policy_ring_a_1_kofi_asante_boateng.pdf
```

Same `--file` flag works on `starter/01_extract.py` once participants fill the TODOs.

Each finished PDF is saved immediately under `results/by_file/` (combined shape only), so a mid-batch crash does not lose progress. Aggregates (`classification.json`, `extraction.json`, `combined.json`) refresh after every file.

Then optionally:

```bash
streamlit run bonus/app.py
```

## Checking against starter

Diff a stub vs the solution:

```bash
diff -u starter/01_extract.py final/01_extract.py | less
```

Or open both side-by-side in the editor and walk the `# Step N:` comments in `final/`.
