"""
01_extract.py — Phase 2: Multimodal Extraction with LangChain
=============================================================
WORKSHOP PHASE 2 · 35 minutes

YOUR TASK: Complete the TODOs below to build a pipeline that:
  1. Loads each insurance PDF from data/sample_docs/
  2. Classifies it (policy / claim / medical report / invoice / police report)
  3. Extracts structured entities using an LLM + Pydantic schemas
  4. Saves results to extracted_data.json for Phase 3

Run from the repo root:
    python starter/01_extract.py
"""

from __future__ import annotations

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
# TODO: Import the PDF loader
# Hint: from langchain_community.document_loaders import PyPDFLoader

# TODO: Import the LLM clients (you only need the one matching LLM_PROVIDER)
#   from langchain_openai import ChatOpenAI
#   from langchain_google_genai import ChatGoogleGenerativeAI

# TODO: Import prompt helpers
# Hint: from langchain_core.prompts import ChatPromptTemplate

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


# ── Step 2: Load a PDF ───────────────────────────────────────────────────────

def load_pdf(path: Path) -> str:
    """
    TODO: Load a PDF and return its text content as a string.

    Hint: Use PyPDFLoader from langchain_community.
    Join all page contents together.

    Example:
        loader = PyPDFLoader(str(path))
        pages = loader.load()
        return "\\n".join(p.page_content for p in pages)
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Load the PDF in load_pdf()")


# ── Step 3: Classify the document ────────────────────────────────────────────

CLASSIFICATION_PROMPT = """
You are an insurance document classifier for a Ghanaian insurance company.

Read the document text below and classify it into one of these types:
- policy          → Insurance Policy Certificate
- claim_form      → Insurance Claim Form
- medical_report  → Medical Report for Insurance
- invoice         → Provider Invoice
- police_report   → Police / Incident Report
- unknown         → Cannot determine

Respond with ONLY one of the exact type strings above. No explanation.

Document:
{text}
"""


def classify_document(text: str, llm) -> DocumentType:
    """
    TODO: Use the LLM to classify the document.

    Hint:
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        chain = prompt | llm
        result = chain.invoke({"text": text[:3000]})  # truncate to save tokens
        return DocumentType(result.content.strip().lower())
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Classify the document in classify_document()")


# ── Step 4: Extract structured entities ──────────────────────────────────────

EXTRACTION_PROMPTS = {
    DocumentType.POLICY: """
Extract all structured fields from this Ghanaian insurance policy certificate.
Include coverage_items (checklist bullets) and authorised_officer when present.
Fill every field in the schema. Use null for missing optional values.

Document:
{text}
""",
    DocumentType.CLAIM_FORM: """
Extract all structured fields from this Ghanaian insurance claim form.
Include insurer (form header), declaration_date, and witness when present.
Fill every field in the schema. Use null for missing optional values
(e.g. witness or attending_doctor when absent).

Document:
{text}
""",
    DocumentType.MEDICAL_REPORT: """
Extract all fields from this Ghanaian medical report for insurance.
Include icd10_code, presenting_complaints, and medications when present.
Fill every field in the schema. Use null for missing optional values.

Document:
{text}
""",
    DocumentType.INVOICE: """
Extract all fields from this Ghanaian provider invoice.
Include line items and authorised_by when present.
Fill every field in the schema.

Document:
{text}
""",
    DocumentType.POLICE_REPORT: """
Extract all fields from this Ghana Police Service incident report.
Include incident_time, incident_type, officer_badge, and claim_ref
(from an explicit field or embedded in the report number, e.g. CLM-...).
Fill every field in the schema. Use null for missing optional values.

Document:
{text}
""",
}

SCHEMA_MAP = {
    DocumentType.POLICY: PolicyExtraction,
    DocumentType.CLAIM_FORM: ClaimFormExtraction,
    DocumentType.MEDICAL_REPORT: MedicalReportExtraction,
    DocumentType.INVOICE: InvoiceExtraction,
    DocumentType.POLICE_REPORT: PoliceReportExtraction,
}


def extract_entities(text: str, doc_type: DocumentType, llm) -> dict:
    """
    TODO: Extract structured entities with LangChain structured output.

    Steps:
    1. Look up the prompt in EXTRACTION_PROMPTS[doc_type]
    2. Look up the Pydantic schema in SCHEMA_MAP[doc_type]
    3. Bind structured output: structured_llm = llm.with_structured_output(schema)
    4. Build a ChatPromptTemplate and chain: prompt | structured_llm
    5. Invoke with truncated text (~4000 chars)
    6. Return model.model_dump()

    Hint:
        from langchain_core.prompts import ChatPromptTemplate
        schema = SCHEMA_MAP[doc_type]
        prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPTS[doc_type])
        chain = prompt | llm.with_structured_output(schema)
        model = chain.invoke({"text": text[:4000]})
        return model.model_dump()
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Extract entities in extract_entities()")


# ── Step 5: Run the full pipeline ────────────────────────────────────────────

def run_extraction():
    """Main pipeline: load → classify → extract → save."""

    console.rule("[bold cyan]Phase 2: Document Extraction[/bold cyan]")

    console.print("Initialising LLM...", end=" ")
    llm = get_llm()
    console.print("[green]OK[/green]")

    docs_path = Path(os.getenv("DOCS_PATH", "data/sample_docs"))
    if not docs_path.is_absolute():
        docs_path = _ROOT / docs_path

    pdf_files = sorted(docs_path.glob("*.pdf"))
    console.print(f"Found [bold]{len(pdf_files)}[/bold] documents in {docs_path}\n")

    results = []
    errors = []

    for pdf_path in track(pdf_files, description="Extracting..."):
        try:
            # TODO: Call load_pdf, classify_document, extract_entities
            # Append a result dict with "file", "doc_type", and extracted fields
            #
            # Example shape:
            #   text = load_pdf(pdf_path)
            #   doc_type = classify_document(text, llm)
            #   if doc_type == DocumentType.UNKNOWN:
            #       raise ValueError("Could not classify document")
            #   entities = extract_entities(text, doc_type, llm)
            #   results.append({"file": pdf_path.name, "doc_type": doc_type.value, **entities})
            pass  # ← Replace this with your implementation

        except Exception as e:
            errors.append({"file": pdf_path.name, "error": str(e)})
            console.print(f"[red]✗[/red] {pdf_path.name}: {e}")

    output_path = _ROOT / "extracted_data.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    console.print()
    console.rule("[bold green]Extraction Complete[/bold green]")
    console.print(f"[green]{len(results)}[/green] documents extracted")
    console.print(f"[red]{len(errors)}[/red] errors")
    console.print(f"Saved to [bold]{output_path}[/bold]")
    console.print("\nNext: [bold]python starter/02_graph.py[/bold]")


if __name__ == "__main__":
    run_extraction()
