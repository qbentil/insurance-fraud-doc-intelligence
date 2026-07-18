"""
nl2cypher.py — Natural language → Cypher → Neo4j → investigator answer
======================================================================
BONUS WALKTHROUGH FILE (fully implemented — no TODOs)

Pipeline:
  1. LLM turns the question into a READ-ONLY Cypher query
  2. Guard rejects write/dangerous statements
  3. Query runs against Neo4j
  4. LLM summarises rows as a fraud investigator

Used by: bonus/app.py
"""

from __future__ import annotations

import os
import re
from typing import Any

from neo4j import GraphDatabase

from bonus.schema_context import GRAPH_SCHEMA

# Lazy-import LLM inside functions so Streamlit's main process can load this
# module for Neo4j helpers without pulling in gRPC/Gemini until ask() runs.

# Words that must never appear in generated Cypher (case-insensitive)
_FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|"
    r"CALL\s+\{|apoc\.|dbms\.|CREATE\s+CONSTRAINT|CREATE\s+INDEX)\b",
    re.IGNORECASE,
)


def get_driver():
    """Neo4j driver from .env."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    return GraphDatabase.driver(uri, auth=(user, password))


def node_count(driver) -> int:
    with driver.session() as session:
        return session.run("MATCH (n) RETURN count(n) AS c").single()["c"]


def _to_plain(value: Any) -> Any:
    """Convert Neo4j / nested values into JSON-safe Python (avoids Streamlit/pyarrow crashes)."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_plain(v) for k, v in value.items()}
    # Neo4j temporal
    if hasattr(value, "iso_format"):
        return value.iso_format()
    # Neo4j Path
    if hasattr(value, "nodes") and hasattr(value, "relationships"):
        return str(value)
    # Neo4j Node — labels + properties
    if hasattr(value, "labels") and hasattr(value, "items"):
        return {"_labels": sorted(value.labels), **{k: _to_plain(v) for k, v in value.items()}}
    # Neo4j Relationship
    if hasattr(value, "type") and hasattr(value, "items"):
        return {"_type": value.type, **{k: _to_plain(v) for k, v in value.items()}}
    # neo4j.time / DateTime-like, bytes, etc.
    return str(value)


def _strip_fences(text: str) -> str:
    raw = text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.lstrip().lower().startswith("cypher"):
            raw = raw.lstrip()[6:]
    return raw.strip().strip("`").strip()


def assert_read_only(cypher: str) -> None:
    """Raise if the query looks like a write or admin operation."""
    if _FORBIDDEN.search(cypher):
        raise ValueError(
            "Refusing to run a non-read-only Cypher query. "
            "Only MATCH / RETURN / WITH / ORDER BY / WHERE / UNWIND are allowed."
        )
    # Must look like a read query
    head = cypher.lstrip().upper()
    if not (head.startswith("MATCH") or head.startswith("WITH") or head.startswith("CALL DB.")):
        raise ValueError("Cypher must start with MATCH, WITH, or CALL db. (read-only).")


def generate_cypher(question: str, llm=None) -> str:
    """Ask the LLM for a single read-only Cypher query."""
    from bonus.llm import get_llm

    llm = llm or get_llm(temperature=0)
    prompt = f"""{GRAPH_SCHEMA}

Write ONE read-only Neo4j Cypher query that answers the investigator's question.
Rules:
- Use only MATCH / OPTIONAL MATCH / WITH / WHERE / RETURN / ORDER BY / LIMIT / UNWIND / collect / count / sum / avg
- Never CREATE, MERGE, DELETE, SET, REMOVE, or DROP
- Prefer RETURN of clear column aliases (doctor, claimants, claim_count, etc.)
- LIMIT 50 unless aggregating
- Return ONLY the Cypher text — no markdown, no explanation

Question: {question}
"""
    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)
    cypher = _strip_fences(content)
    assert_read_only(cypher)
    return cypher


def run_cypher(driver, cypher: str) -> list[dict[str, Any]]:
    """Execute Cypher and return list of plain dicts."""
    assert_read_only(cypher)
    with driver.session() as session:
        records = list(session.run(cypher))
    rows: list[dict[str, Any]] = []
    for record in records:
        row = {key: _to_plain(record[key]) for key in record.keys()}
        rows.append(row)
    return rows


def summarise_answer(question: str, cypher: str, rows: list[dict], llm=None) -> str:
    """Turn raw rows into an investigator-style natural language answer."""
    from bonus.llm import get_llm

    llm = llm or get_llm(temperature=0.2)
    preview = rows[:25]
    prompt = f"""You are a sharp insurance fraud investigator briefing a colleague.
Answer the question using ONLY the query results below.
Cite specific names, phones, amounts (GHS), and counts when present.
If results are empty, say what that means for the investigation.
Be concise (3–6 sentences). Do not invent data.

Question: {question}

Cypher used:
{cypher}

Results ({len(rows)} row(s), showing up to 25):
{preview}
"""
    result = llm.invoke(prompt)
    return (result.content if hasattr(result, "content") else str(result)).strip()


def ask(question: str, driver=None, llm=None) -> dict[str, Any]:
    """
    Full pipeline: question → Cypher → rows → answer.

    Returns:
        {question, cypher, rows, answer, error?}
    """
    from bonus.llm import get_llm

    close_driver = False
    if driver is None:
        driver = get_driver()
        close_driver = True

    llm = llm or get_llm()
    try:
        cypher = generate_cypher(question, llm=llm)
        rows = run_cypher(driver, cypher)
        answer = summarise_answer(question, cypher, rows, llm=llm)
        return {
            "question": question,
            "cypher": cypher,
            "rows": rows,
            "answer": answer,
        }
    except Exception as exc:
        return {
            "question": question,
            "cypher": "",
            "rows": [],
            "answer": f"Investigation stalled: {exc}",
            "error": str(exc),
        }
    finally:
        if close_driver:
            driver.close()


def _ask_worker(question: str, out_path: str) -> None:
    """Child-process entry: run ask() and write JSON (isolates gRPC segfaults)."""
    import json
    from pathlib import Path

    from dotenv import load_dotenv

    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")
    try:
        result = ask(question)
    except Exception as exc:
        result = {
            "question": question,
            "cypher": "",
            "rows": [],
            "answer": f"Investigation stalled: {exc}",
            "error": str(exc),
        }
    Path(out_path).write_text(json.dumps(result, default=str), encoding="utf-8")


def ask_in_subprocess(question: str, timeout_s: int = 180) -> dict[str, Any]:
    """
    Run ask() in a spawned subprocess.

    On macOS, Gemini/gRPC + Streamlit in one process can segfault after a
    question; isolating the LLM call keeps the UI alive.
    """
    import json
    import tempfile
    from multiprocessing import get_context
    from pathlib import Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        out_path = tmp.name

    ctx = get_context("spawn")
    proc = ctx.Process(target=_ask_worker, args=(question, out_path))
    proc.start()
    proc.join(timeout=timeout_s)

    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        return {
            "question": question,
            "cypher": "",
            "rows": [],
            "answer": "Investigation timed out. Try a shorter question.",
            "error": "timeout",
        }

    out = Path(out_path)
    try:
        if proc.exitcode not in (0, None):
            return {
                "question": question,
                "cypher": "",
                "rows": [],
                "answer": (
                    "Investigation process crashed (often a macOS + gRPC issue). "
                    "Click the case-file card again — the UI should still be up."
                ),
                "error": f"exitcode={proc.exitcode}",
            }
        if not out.exists() or out.stat().st_size == 0:
            return {
                "question": question,
                "cypher": "",
                "rows": [],
                "answer": "Investigation returned no result. Try again.",
                "error": "empty",
            }
        return json.loads(out.read_text(encoding="utf-8"))
    finally:
        try:
            out.unlink(missing_ok=True)
        except OSError:
            pass
