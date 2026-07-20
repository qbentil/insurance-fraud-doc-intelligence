"""
01_extract.py — Phase 2: Multimodal Extraction with LangChain
=============================================================
WORKSHOP PHASE 2 · 35 minutes

YOUR TASK: Complete the TODOs below to build a pipeline that:
  1. Sends each insurance PDF to a multimodal LLM (file bytes — not scraped text)
  2. Classifies it (policy / claim / medical report / invoice / police report)
  3. Extracts structured entities using an LLM + Pydantic schemas
  4. Saves results/by_file/<stem>.json as each PDF finishes, then refreshes
     classification.json, extraction.json, and combined.json

Run from the repo root:
    python starter/01_extract.py
    python starter/01_extract.py --file some.pdf   # cheap single-file test
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

# Allow `python starter/01_extract.py` from the repo root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")
console = Console()

# ── Imports you will need ─────────────────────────────────────────────────────
# TODO: Import LLM clients (you only need the one matching LLM_PROVIDER)
#   from langchain_openai import ChatOpenAI
#   from langchain_google_genai import ChatGoogleGenerativeAI
#
# TODO: Import multimodal message helper
#   from langchain_core.messages import HumanMessage

from starter.schemas import (
    DocumentType,
    PolicyExtraction,
    ClaimFormExtraction,
    MedicalReportExtraction,
    InvoiceExtraction,
    PoliceReportExtraction,
)


# ── Step 1: Initialise your LLM ──────────────────────────────────────────────

def get_llm():
    """
    TODO: Return an initialised LLM based on LLM_PROVIDER in .env.

    Supported values: "openai" | "gemini"

    Example (OpenAI):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4.1", temperature=0)

    Example (Gemini):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Initialise your LLM in get_llm()")


# ── Step 2: Build a multimodal PDF message ───────────────────────────────────

def pdf_file_block(path: Path) -> dict:
    """
    TODO: Read the PDF bytes, base64-encode them, and return a multimodal content block.

    Providers differ on the LangChain content-block shape — branch on LLM_PROVIDER:

      OpenAI (LLM_PROVIDER=openai):
        {
            "type": "file",
            "file": {
                "filename": path.name,
                "file_data": f"data:application/pdf;base64,{data}",
            },
        }

      Gemini (LLM_PROVIDER=gemini — default):
        {
            "type": "media",
            "mime_type": "application/pdf",
            "data": <base64 string>,
        }

    Hint:
        import base64
        data = base64.b64encode(path.read_bytes()).decode("utf-8")
        provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Build pdf_file_block()")


def multimodal_message(instruction: str, path: Path):
    """
    TODO: Return a HumanMessage whose content is:
      1. {"type": "text", "text": instruction}
      2. pdf_file_block(path)

    Hint:
        from langchain_core.messages import HumanMessage
        return HumanMessage(content=[...])
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Build multimodal_message()")


# ── Step 3: Classify the document ────────────────────────────────────────────

CLASSIFICATION_PROMPT = """
You are an insurance document classifier for a Ghanaian insurance company.

Look at the attached PDF and classify it into one of these types:
- policy          → Insurance Policy Certificate
- claim_form      → Insurance Claim Form
- medical_report  → Medical Report for Insurance
- invoice         → Provider Invoice
- police_report   → Police / Incident Report
- unknown         → Cannot determine

Respond with ONLY one of the exact type strings above. No explanation.
"""


def classify_document(path: Path, llm) -> DocumentType:
    """
    TODO: Classify the PDF with a multimodal LLM call (no text extraction).

    Hint:
        message = multimodal_message(CLASSIFICATION_PROMPT.strip(), path)
        result = llm.invoke([message])
        label = result.content.strip().lower().replace("`", "").split()[0]
        return DocumentType(label)
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Classify the document in classify_document()")


# ── Step 4: Extract structured entities ──────────────────────────────────────

EXTRACTION_PROMPTS = {
    DocumentType.POLICY: """
Look at the attached Ghanaian insurance policy certificate PDF.
Extract all structured fields.
Include coverage_items (checklist bullets) and authorised_officer when present.
Fill every field in the schema. Use null for missing optional values.
""",
    DocumentType.CLAIM_FORM: """
Look at the attached Ghanaian insurance claim form PDF.
Extract all structured fields.
Include insurer (form header), declaration_date, and witness when present.
Fill every field in the schema. Use null for missing optional values
(e.g. witness or attending_doctor when absent).
""",
    DocumentType.MEDICAL_REPORT: """
Look at the attached Ghanaian medical report for insurance PDF.
Extract all fields.
Include icd10_code, presenting_complaints, and medications when present.
Fill every field in the schema. Use null for missing optional values.
""",
    DocumentType.INVOICE: """
Look at the attached Ghanaian provider invoice PDF.
Extract all fields.
Include line items and authorised_by when present.
Fill every field in the schema.
""",
    DocumentType.POLICE_REPORT: """
Look at the attached Ghana Police Service incident report PDF.
Extract all fields.
Include incident_time, incident_type, officer_badge, and claim_ref
(from an explicit field or embedded in the report number, e.g. CLM-...).
Fill every field in the schema. Use null for missing optional values.
""",
}

SCHEMA_MAP = {
    DocumentType.POLICY: PolicyExtraction,
    DocumentType.CLAIM_FORM: ClaimFormExtraction,
    DocumentType.MEDICAL_REPORT: MedicalReportExtraction,
    DocumentType.INVOICE: InvoiceExtraction,
    DocumentType.POLICE_REPORT: PoliceReportExtraction,
}


def extract_entities(path: Path, doc_type: DocumentType, llm) -> dict:
    """
    TODO: Extract structured entities from the PDF via multimodal + structured output.

    Steps:
    1. Look up EXTRACTION_PROMPTS[doc_type] and SCHEMA_MAP[doc_type]
    2. structured_llm = llm.with_structured_output(schema)
    3. message = multimodal_message(instruction, path)
    4. model = structured_llm.invoke([message])
    5. return model.model_dump()
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Extract entities in extract_entities()")


# ── Step 5: Run the full pipeline ────────────────────────────────────────────

def _resolve_pdf_files(docs_path: Path, only_file: str | None) -> list[Path]:
    """All PDFs under docs_path, or a single file for --file tests."""
    if not only_file:
        return sorted(docs_path.glob("*.pdf"))

    raw = Path(only_file)
    if raw.is_absolute():
        candidates = [raw]
    else:
        # Accept bare name, repo-relative path, or cwd-relative path
        candidates = [
            Path.cwd() / raw,
            _ROOT / raw,
            docs_path / raw.name,
            docs_path / raw,
        ]

    for candidate in candidates:
        if candidate.is_file():
            return [candidate.resolve()]

    tried = "\n".join(f"  - {c}" for c in candidates)
    raise FileNotFoundError(
        f"PDF not found: {only_file}\nTried:\n{tried}\n"
        f"Tip: pass a filename under {docs_path}, a path from the repo root, "
        "or an absolute path."
    )


def _save_results(output_path: Path, new_results: list[dict], merge: bool) -> None:
    """
    Full run: overwrite JSON.
    Single-file run: merge/replace entries by `file` name so other docs stay.
    """
    if merge and output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        by_name = {row.get("file"): row for row in existing if row.get("file")}
        for row in new_results:
            by_name[row["file"]] = row
        payload = list(by_name.values())
    else:
        payload = new_results

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)


def _split_outputs(combined: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Split combined rows into classification / extraction / combined views."""
    classifications: list[dict] = []
    extractions: list[dict] = []
    for row in combined:
        classifications.append(
            {"file": row.get("file"), "doc_type": row.get("doc_type")}
        )
        entities = {k: v for k, v in row.items() if k not in ("file", "doc_type")}
        extractions.append({"file": row.get("file"), **entities})
    return classifications, extractions, combined


def _results_dirs() -> tuple[Path, Path]:
    results_dir = _ROOT / "results"
    by_file_dir = results_dir / "by_file"
    return results_dir, by_file_dir


def _clear_by_file() -> None:
    """Full-batch runs start clean so stale PDFs don't linger."""
    _, by_file_dir = _results_dirs()
    if not by_file_dir.exists():
        return
    for path in by_file_dir.glob("*.json"):
        path.unlink()


def _write_by_file(row: dict) -> Path:
    """One combined record per PDF under results/by_file/<stem>.json."""
    _, by_file_dir = _results_dirs()
    by_file_dir.mkdir(parents=True, exist_ok=True)
    path = by_file_dir / f"{Path(row['file']).stem}.json"
    with open(path, "w") as f:
        json.dump(row, f, indent=2, default=str)
    return path


def _load_all_by_file() -> list[dict]:
    """Reassemble combined rows from per-file JSON (crash-recovery source of truth)."""
    _, by_file_dir = _results_dirs()
    if not by_file_dir.exists():
        return []
    rows: list[dict] = []
    for path in sorted(by_file_dir.glob("*.json")):
        with open(path) as f:
            rows.append(json.load(f))
    return rows


def _rebuild_aggregates() -> Path:
    """Rewrite classification / extraction / combined from results/by_file/."""
    results_dir, _ = _results_dirs()
    combined = _load_all_by_file()
    classifications, extractions, combined = _split_outputs(combined)
    _save_results(results_dir / "classification.json", classifications, merge=False)
    _save_results(results_dir / "extraction.json", extractions, merge=False)
    _save_results(results_dir / "combined.json", combined, merge=False)
    return results_dir


def _persist_result(row: dict) -> None:
    """Crash-safe: write per-file combined JSON, then refresh the three aggregates."""
    _write_by_file(row)
    _rebuild_aggregates()


def run_extraction(only_file: str | None = None):
    """Main pipeline: load → classify → extract → save-as-you-go.

    Args:
        only_file: Optional PDF name or path. If set, process just that file
                   (keeps other by_file entries). If None, clear by_file and
                   process all.
    """

    console.rule("[bold cyan]Phase 2: Document Extraction[/bold cyan]")

    console.print("Initialising LLM...", end=" ")
    llm = get_llm()
    console.print("[green]OK[/green]")

    docs_path = Path(os.getenv("DOCS_PATH", "data/sample_docs"))
    if not docs_path.is_absolute():
        docs_path = _ROOT / docs_path

    pdf_files = _resolve_pdf_files(docs_path, only_file)
    mode = "single-file" if only_file else "all"
    console.print(
        f"Mode: [bold]{mode}[/bold] · multimodal PDF · "
        f"[bold]{len(pdf_files)}[/bold] document(s) in {docs_path}\n"
    )

    # Full batch: wipe per-file cache so aggregates match this run only
    if not only_file:
        _clear_by_file()

    results = []
    errors = []

    for pdf_path in track(pdf_files, description="Extracting..."):
        try:
            # TODO: Call classify_document(pdf_path, llm) and extract_entities(pdf_path, ...)
            # Build a combined row, then call _persist_result(row) so a crash
            # mid-batch does not lose finished PDFs.
            #
            # Example shape:
            #   doc_type = classify_document(pdf_path, llm)
            #   if doc_type == DocumentType.UNKNOWN:
            #       raise ValueError("Could not classify document")
            #   entities = extract_entities(pdf_path, doc_type, llm)
            #   entities.pop("document_type", None)  # schema echo — routing uses doc_type
            #   row = {"file": pdf_path.name, "doc_type": doc_type.value, **entities}
            #   results.append(row)
            #   _persist_result(row)  # by_file/<stem>.json + refresh aggregates
            #   console.print(f"[green]✓[/green] {pdf_path.name} → {doc_type.value}")
            pass  # ← Replace this with your implementation

        except Exception as e:
            errors.append({"file": pdf_path.name, "error": str(e)})
            console.print(f"[red]✗[/red] {pdf_path.name}: {e}")

    # Final aggregate refresh from by_file (source of truth) — save helpers are provided
    results_dir = _rebuild_aggregates()

    console.print()
    console.rule("[bold green]Extraction Complete[/bold green]")
    console.print(f"[green]{len(results)}[/green] documents extracted this run")
    console.print(f"[red]{len(errors)}[/red] errors")
    console.print(f"Saved to [bold]{results_dir}[/bold]/")
    console.print("  · by_file/<stem>.json  (combined, one per PDF — written as you go)")
    console.print("  · classification.json  (file + doc_type)")
    console.print("  · extraction.json      (file + entities)")
    console.print("  · combined.json        (file + doc_type + entities) ← Phase 3")
    console.print("\nNext: [bold]python starter/02_graph.py[/bold]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract structured entities from insurance PDFs (multimodal)."
    )
    parser.add_argument(
        "--file",
        dest="only_file",
        default=None,
        help="Process a single PDF (name under data/sample_docs/ or absolute path). "
        "Merges into results/*.json. Omit to process all PDFs.",
    )
    args = parser.parse_args()
    run_extraction(only_file=args.only_file)
