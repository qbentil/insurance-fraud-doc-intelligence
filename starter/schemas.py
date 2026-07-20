"""
schemas.py — Pydantic Output Schemas for Entity Extraction
==========================================================
These schemas define the structured data LangChain will extract
from each insurance document. They are pre-built so you can focus
on the pipeline logic during the workshop.

Run this file directly to verify your environment is set up correctly:
    python starter/schemas.py
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Document Type Classifier ──────────────────────────────────────────────────

class DocumentType(str, Enum):
    POLICY = "policy"
    CLAIM_FORM = "claim_form"
    MEDICAL_REPORT = "medical_report"
    INVOICE = "invoice"
    POLICE_REPORT = "police_report"
    UNKNOWN = "unknown"


# ── Core Entity Schemas ───────────────────────────────────────────────────────

class Claimant(BaseModel):
    """A person filing an insurance claim."""
    name: str = Field(description="Full name of the claimant")
    id: Optional[str] = Field(None, description="Ghana Card or national ID number")
    phone: Optional[str] = Field(None, description="Contact phone number")
    address: Optional[str] = Field(None, description="Residential address")
    dob: Optional[str] = Field(None, description="Date of birth")


class Doctor(BaseModel):
    """An attending physician or medical professional."""
    name: str = Field(description="Full name including title (e.g. Dr.)")
    reg_number: Optional[str] = Field(None, description="Medical registration number (MDC-GH-XXXXX)")
    hospital: Optional[str] = Field(None, description="Hospital or clinic name and location")


class Provider(BaseModel):
    """A medical services provider or billing entity."""
    name: str = Field(description="Provider company or facility name")
    reg: Optional[str] = Field(None, description="NIC provider registration number")
    address: Optional[str] = Field(None, description="Provider address")


class Witness(BaseModel):
    """A witness named in a claim or police report."""
    name: str = Field(description="Full name of the witness")
    id: Optional[str] = Field(None, description="Ghana Card or national ID")
    phone: Optional[str] = Field(None, description="Contact phone number")
    address: Optional[str] = Field(None, description="Address of witness")


class InvoiceItem(BaseModel):
    """A single line item on a provider invoice."""
    description: str = Field(description="Service or item description")
    quantity: int = Field(description="Number of units")
    unit_cost: float = Field(description="Cost per unit in GHS")
    total: float = Field(description="Line total in GHS")


# ── Document-Level Extraction Schemas ────────────────────────────────────────

class PolicyExtraction(BaseModel):
    """Extracted data from an Insurance Policy Certificate."""
    document_type: DocumentType = DocumentType.POLICY
    policy_number: str
    insurer: str
    claimant: Claimant
    coverage_type: Optional[str] = None
    annual_premium: Optional[float] = None
    sum_insured: Optional[float] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    coverage_items: List[str] = Field(
        default_factory=list,
        description="Coverage checklist items (e.g. Hospitalisation & Surgery)",
    )
    authorised_officer: Optional[str] = Field(
        None, description="Authorised NIC / insurer officer name"
    )


class ClaimFormExtraction(BaseModel):
    """Extracted data from an Insurance Claim Form."""
    document_type: DocumentType = DocumentType.CLAIM_FORM
    claim_number: str
    policy_number: Optional[str] = None
    insurer: Optional[str] = Field(
        None, description="Insurer named on the claim form header"
    )
    claimant: Claimant
    incident_date: Optional[str] = None
    incident_location: Optional[str] = None
    incident_type: Optional[str] = None
    incident_description: Optional[str] = None
    attending_doctor: Optional[Doctor] = None
    claim_amount: Optional[float] = None
    witness: Optional[Witness] = None
    declaration_date: Optional[str] = Field(
        None, description="Date the claimant signed the declaration"
    )


class MedicalReportExtraction(BaseModel):
    """Extracted data from a Medical Report."""
    document_type: DocumentType = DocumentType.MEDICAL_REPORT
    report_ref: Optional[str] = None
    claim_ref: Optional[str] = None
    patient: Claimant
    doctor: Doctor
    diagnosis: Optional[str] = None
    icd10_code: Optional[str] = Field(
        None, description="ICD-10 diagnosis code (e.g. ICD-806)"
    )
    presenting_complaints: Optional[str] = Field(
        None, description="Presenting complaints / clinical narrative"
    )
    treatment: Optional[str] = None
    medications: Optional[str] = Field(
        None, description="Medications prescribed"
    )
    total_cost: Optional[float] = None
    billing_provider: Optional[str] = None
    visit_date: Optional[str] = None


class InvoiceExtraction(BaseModel):
    """Extracted data from a Provider Invoice."""
    document_type: DocumentType = DocumentType.INVOICE
    invoice_number: Optional[str] = None
    claim_reference: Optional[str] = None
    provider: Provider
    claimant_name: Optional[str] = None
    invoice_date: Optional[str] = None
    items: List[InvoiceItem] = []
    total_payable: Optional[float] = None
    authorised_by: Optional[str] = Field(
        None, description="Person who authorised the invoice"
    )


class PoliceReportExtraction(BaseModel):
    """Extracted data from a Police / Incident Report."""
    document_type: DocumentType = DocumentType.POLICE_REPORT
    report_number: Optional[str] = None
    claim_ref: Optional[str] = Field(
        None,
        description="Related claim reference if stated or embedded in the report number",
    )
    claimant: Claimant
    incident_date: Optional[str] = None
    incident_time: Optional[str] = Field(
        None, description="Time of incident (e.g. 09:26 hrs)"
    )
    incident_location: Optional[str] = None
    incident_type: Optional[str] = Field(
        None, description="Nature of incident (e.g. Road Traffic Accident)"
    )
    incident_description: Optional[str] = None
    witness: Optional[Witness] = None
    recording_officer: Optional[str] = None
    officer_badge: Optional[str] = Field(
        None, description="Recording officer badge number (e.g. GPS-8367)"
    )


# ── Union type for type-routing ───────────────────────────────────────────────

DocumentExtraction = (
    PolicyExtraction
    | ClaimFormExtraction
    | MedicalReportExtraction
    | InvoiceExtraction
    | PoliceReportExtraction
)


# ── Setup Verification ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path

    from rich.console import Console
    from rich.panel import Panel

    # Ensure repo root is on path when run as a script
    _ROOT = Path(__file__).resolve().parent.parent
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))

    console = Console()

    console.print(Panel.fit(
        "[bold cyan]Insurance Fraud Doc Intelligence — Setup Check[/bold cyan]\n"
        "[dim]PyCon Ghana 2026 Workshop[/dim]",
        border_style="cyan"
    ))

    checks = []

    # Python version
    v = sys.version_info
    if v.major == 3 and v.minor >= 10:
        checks.append(("✅", f"Python {v.major}.{v.minor}.{v.micro}", ""))
    else:
        checks.append(("❌", f"Python {v.major}.{v.minor}", "Need Python 3.10+"))

    # Pydantic
    try:
        import pydantic
        checks.append(("✅", f"Pydantic {pydantic.__version__}", ""))
    except ImportError:
        checks.append(("❌", "Pydantic", "Run: pip install -r requirements.txt"))

    # LangChain core stack
    try:
        import langchain
        checks.append(("✅", f"LangChain {langchain.__version__}", ""))
    except ImportError:
        checks.append(("❌", "LangChain", "Run: pip install -r requirements.txt"))

    try:
        import langchain_core  # noqa: F401
        checks.append(("✅", "langchain-core", ""))
    except ImportError:
        checks.append(("❌", "langchain-core", "Run: pip install -r requirements.txt"))

    try:
        import langchain_openai  # noqa: F401
        checks.append(("✅", "langchain-openai", ""))
    except ImportError:
        checks.append(("❌", "langchain-openai", "Run: pip install -r requirements.txt"))

    try:
        import langchain_google_genai  # noqa: F401
        checks.append(("✅", "langchain-google-genai", ""))
    except ImportError:
        checks.append(("❌", "langchain-google-genai", "Run: pip install -r requirements.txt"))

    # Neo4j driver
    try:
        import neo4j
        checks.append(("✅", f"Neo4j driver {neo4j.__version__}", ""))
    except ImportError:
        checks.append(("❌", "Neo4j driver", "Run: pip install -r requirements.txt"))

    # dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv(_ROOT / ".env")
        checks.append(("✅", "python-dotenv", ""))
    except ImportError:
        checks.append(("❌", "python-dotenv", "Run: pip install -r requirements.txt"))

    # .env file
    env_path = _ROOT / ".env"
    if env_path.exists():
        checks.append(("✅", ".env file found", ""))
    else:
        checks.append(("⚠️ ", ".env file missing", "cp .env.example .env and fill in your keys"))

    # LLM provider + API key
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider in {"openai", "gemini"}:
        checks.append(("✅", f"LLM_PROVIDER={provider}", ""))
    else:
        checks.append(("⚠️ ", "LLM_PROVIDER not set", "Set LLM_PROVIDER=openai or gemini in .env"))

    if provider == "openai":
        api_ok = bool(os.getenv("OPENAI_API_KEY"))
        key_label = "OPENAI_API_KEY"
    elif provider == "gemini":
        api_ok = bool(os.getenv("GOOGLE_API_KEY"))
        key_label = "GOOGLE_API_KEY"
    else:
        api_ok = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        key_label = "OPENAI_API_KEY or GOOGLE_API_KEY"

    if api_ok:
        checks.append(("✅", f"{key_label} detected", ""))
    else:
        checks.append(("⚠️ ", f"{key_label} missing", f"Add {key_label} to .env"))

    # Neo4j URI
    neo4j_uri = os.getenv("NEO4J_URI")
    if neo4j_uri:
        checks.append(("✅", f"Neo4j URI: {neo4j_uri}", ""))
    else:
        checks.append(("⚠️ ", "NEO4J_URI not set", "Add NEO4J_URI to .env"))

    # Sample docs
    docs_path = _ROOT / "data" / "sample_docs"
    doc_count = len(list(docs_path.glob("*.pdf"))) if docs_path.exists() else 0
    if doc_count >= 36:
        checks.append(("✅", f"{doc_count} sample PDFs found", ""))
    elif doc_count > 0:
        checks.append(("⚠️ ", f"Only {doc_count} PDFs found", "Expected 36 in data/sample_docs/"))
    else:
        checks.append(("❌", "No sample PDFs found", "Expected PDFs in data/sample_docs/"))

    for icon, label, note in checks:
        note_str = f"  [dim red]{note}[/dim red]" if note else ""
        console.print(f"  {icon}  {label}{note_str}")

    failures = [c for c in checks if c[0] == "❌"]

    console.print()
    if not failures:
        console.print(Panel(
            "[bold green]Setup verified. Ready for the workshop![/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]{len(failures)} issue(s) to fix before the workshop.[/bold red]\n"
            "[dim]See notes above for fix instructions.[/dim]",
            border_style="red"
        ))
        sys.exit(1)
