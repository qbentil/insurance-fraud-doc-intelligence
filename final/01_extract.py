"""
01_extract.py — REFERENCE SOLUTION (Phase 2)
============================================
Complete implementation of starter/01_extract.py.
Every former TODO is filled in with step comments.

Multimodal: each PDF is sent to the LLM as a file content block
(base64 + application/pdf) — no PyPDF text extraction.

Run from the repo root:
    python final/01_extract.py
    python final/01_extract.py --file some.pdf

Writes results/by_file/<stem>.json as each PDF finishes, then refreshes
classification.json, extraction.json, and combined.json.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.progress import track

# Allow `python final/01_extract.py` from the repo root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")
console = Console()

from starter.schemas import (  # noqa: E402
    ClaimFormExtraction,
    DocumentType,
    InvoiceExtraction,
    MedicalReportExtraction,
    PoliceReportExtraction,
    PolicyExtraction,
)


# ── Step 1: Initialise your LLM ──────────────────────────────────────────────

def get_llm():
    """Return ChatOpenAI or ChatGoogleGenerativeAI based on LLM_PROVIDER."""
    # 1a. Read which provider the participant chose in .env
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    # 1b. OpenAI path — model locked for the workshop
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing from .env")
        return ChatOpenAI(model="gpt-4.1", temperature=0, api_key=api_key)

    # 1c. Gemini path — default for the workshop
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is missing from .env")
        return ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            temperature=0,
            google_api_key=api_key,
        )

    raise ValueError(f"Unknown LLM_PROVIDER={provider!r}. Use 'openai' or 'gemini'.")


# ── Step 2: Build a multimodal PDF message ───────────────────────────────────

def pdf_file_block(path: Path) -> dict:
    """Encode the PDF so the LLM receives the file, not scraped text.

    Providers differ on the LangChain content-block shape:
      - OpenAI:  type=file with nested file.file_data (data URI) + filename
      - Gemini:  type=media + data  (langchain_google_genai)
    """
    # 2a. Read raw bytes from disk
    raw = path.read_bytes()
    # 2b. Base64 for the LangChain / provider content block
    data = base64.b64encode(raw).decode("utf-8")
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    # 2c. OpenAI Responses/Chat PDF input: nested file + data URI
    if provider == "openai":
        return {
            "type": "file",
            "file": {
                "filename": path.name,
                "file_data": f"data:application/pdf;base64,{data}",
            },
        }

    # 2d. Gemini (langchain_google_genai) expects type=media + data
    return {
        "type": "media",
        "mime_type": "application/pdf",
        "data": data,
    }


def multimodal_message(instruction: str, path: Path) -> HumanMessage:
    """HumanMessage = short text instruction + the PDF itself."""
    return HumanMessage(
        content=[
            {"type": "text", "text": instruction},
            
            pdf_file_block(path),
        ]
    )


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
    """Ask the multimodal LLM for a DocumentType label from the PDF."""
    # 3a. Instruction + PDF file block (no text extraction)
    message = multimodal_message(CLASSIFICATION_PROMPT.strip(), path)
    # 3b. Invoke the chat model directly with the multimodal message
    result = llm.invoke([message])
    # 3c. Parse the raw string into our enum
    label = result.content.strip().lower().replace("`", "").split()[0]
    return DocumentType(label)


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
    """Extract a Pydantic-validated dict from the PDF via multimodal LLM."""
    # 4a. Pick the matching schema + instruction for this doc type
    schema = SCHEMA_MAP[doc_type]
    instruction = EXTRACTION_PROMPTS[doc_type].strip()
    # 4b. Force structured JSON that matches the Pydantic model
    structured_llm = llm.with_structured_output(schema)
    # 4c. Same multimodal pattern: text instruction + PDF file
    message = multimodal_message(instruction, path)
    model = structured_llm.invoke([message])
    # 4d. Plain dict for JSON serialisation / Phase 3 writers
    return model.model_dump()


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
    """Main pipeline: multimodal classify → extract → save-as-you-go.

    Args:
        only_file: Optional PDF name or path. If set, process just that file
                   (keeps other by_file entries). If None, clear by_file and
                   process all.
    """

    console.rule("[bold cyan]Phase 2: Document Extraction (final/)[/bold cyan]")

    # 5a. One LLM instance for the whole batch
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
            # 5b. Classify from the PDF bytes (no text scrape)
            doc_type = classify_document(pdf_path, llm)
            if doc_type == DocumentType.UNKNOWN:
                raise ValueError("Could not classify document")
            # 5c. Structured extraction from the same PDF
            entities = extract_entities(pdf_path, doc_type, llm)
            # 5d. Drop schema's document_type — Phase 3 routes on doc_type only
            entities.pop("document_type", None)
            row = {
                "file": pdf_path.name,
                "doc_type": doc_type.value,
                **entities,
            }
            results.append(row)
            # 5e. Persist immediately (by_file + aggregates) — survive mid-run crashes
            _persist_result(row)
            console.print(f"[green]✓[/green] {pdf_path.name} → {doc_type.value}")

        except Exception as e:
            errors.append({"file": pdf_path.name, "error": str(e)})
            console.print(f"[red]✗[/red] {pdf_path.name}: {e}")

    # 5f. Final aggregate refresh from by_file (source of truth)
    results_dir = _rebuild_aggregates()

    console.print()
    console.rule("[bold green]Extraction Complete[/bold green]")
    console.print(f"[green]{len(results)}[/green] documents extracted this run")
    console.print(f"[red]{len(errors)}[/red] errors")
    console.print(f"Saved to [bold]{results_dir}[/bold]:")
    console.print("  · by_file/<stem>.json  (combined, one per PDF — written as you go)")
    console.print("  · classification.json  (file + doc_type)")
    console.print("  · extraction.json      (file + entities)")
    console.print("  · combined.json        (file + doc_type + entities) ← Phase 3")
    console.print("\nNext: [bold]python final/02_graph.py[/bold]")


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
