"""
02_graph.py — REFERENCE SOLUTION (Phase 3)
==========================================
Complete implementation of starter/02_graph.py.
Every former TODO is filled in with step comments.

Run from the repo root (after extraction):
    python final/02_graph.py

Reads results/combined.json (written by 01_extract.py).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from rich.console import Console
from rich.table import Table

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")
console = Console()


# ── Step 1: Connect to Neo4j ─────────────────────────────────────────────────

def get_driver():
    """Create a Neo4j driver from .env credentials."""
    # 1a. URI may be bolt:// (Desktop) or neo4j+s:// (Aura)
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    # 1b. Driver manages the connection pool — close it when done
    return GraphDatabase.driver(uri, auth=(user, password))


# ── Step 2: Create constraints ───────────────────────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Claimant)  REQUIRE c.id       IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Policy)    REQUIRE p.number    IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (cl:Claim)    REQUIRE cl.number   IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Doctor)    REQUIRE d.reg       IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Provider) REQUIRE pr.name     IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Witness)   REQUIRE w.phone     IS UNIQUE",
]


def create_constraints(driver):
    """Ensure unique keys so MERGE is safe across 36 documents."""
    # 2a. Run each DDL statement in its own session call
    with driver.session() as session:
        for query in CONSTRAINTS:
            session.run(query)


# ── helpers ───────────────────────────────────────────────────────────────────

def _claimant_id(person: dict | None, fallback_name: str | None = None) -> str | None:
    """Prefer Ghana Card id; fall back to a synthetic key from name."""
    if not person:
        return None
    if person.get("id"):
        return person["id"]
    name = person.get("name") or fallback_name
    return f"name:{name}" if name else None


# ── Step 3: Write nodes & relationships ──────────────────────────────────────

def write_policy(tx, doc: dict):
    """MERGE Claimant + Policy and link with HAS_POLICY."""
    # 3a. Nested claimant object from extraction
    claimant = doc.get("claimant") or {}
    cid = _claimant_id(claimant)
    if not cid or not doc.get("policy_number"):
        return

    # 3b. One Cypher: upsert both nodes, then the relationship
    
    tx.run(
        """
        MERGE (c:Claimant {id: $claimant_id})
        SET c.name = coalesce($name, c.name),
            c.phone = coalesce($phone, c.phone),
            c.address = coalesce($address, c.address),
            c.dob = coalesce($dob, c.dob),
            // Ring C: same Ghana Card, cycling names — keep every alias we see
            c.aliases = CASE
              WHEN $name IS NULL THEN coalesce(c.aliases, [])
              WHEN c.aliases IS NULL THEN [$name]
              WHEN NOT $name IN c.aliases THEN c.aliases + $name
              ELSE c.aliases
            END
        MERGE (p:Policy {number: $policy_number})
        SET p.insurer = $insurer,
            p.coverage = $coverage,
            p.premium = $premium,
            p.sum_insured = $sum_insured,
            p.effective_date = $effective_date,
            p.expiry_date = $expiry_date,
            p.coverage_items = $coverage_items,
            p.authorised_officer = $officer
        MERGE (c)-[:HAS_POLICY]->(p)
        """,
        claimant_id=cid,
        name=claimant.get("name"),
        phone=claimant.get("phone"),
        address=claimant.get("address"),
        dob=claimant.get("dob"),
        policy_number=doc["policy_number"],
        insurer=doc.get("insurer"),
        coverage=doc.get("coverage_type"),
        premium=doc.get("annual_premium"),
        sum_insured=doc.get("sum_insured"),
        effective_date=doc.get("effective_date"),
        expiry_date=doc.get("expiry_date"),
        coverage_items=doc.get("coverage_items") or [],
        officer=doc.get("authorised_officer"),
    )


def write_claim(tx, doc: dict):
    """Write Claim and connect Claimant, Policy, Doctor, Hospital, Witness."""
    claimant = doc.get("claimant") or {}
    cid = _claimant_id(claimant)
    claim_number = doc.get("claim_number")
    if not cid or not claim_number:
        return

    # 3c. Always MERGE claimant + claim + FILED
    tx.run(
        """
        MERGE (c:Claimant {id: $claimant_id})
        SET c.name = coalesce($name, c.name),
            c.phone = coalesce($phone, c.phone),
            c.address = coalesce($address, c.address),
            c.aliases = CASE
              WHEN $name IS NULL THEN coalesce(c.aliases, [])
              WHEN c.aliases IS NULL THEN [$name]
              WHEN NOT $name IN c.aliases THEN c.aliases + $name
              ELSE c.aliases
            END
        MERGE (cl:Claim {number: $claim_number})
        SET cl.amount = $amount,
            cl.date = $date,
            cl.location = $location,
            cl.type = $type,
            cl.description = $description,
            cl.insurer = $insurer,
            cl.declaration_date = $declaration_date
        MERGE (c)-[:FILED]->(cl)
        """,
        claimant_id=cid,
        name=claimant.get("name"),
        phone=claimant.get("phone"),
        address=claimant.get("address"),
        claim_number=claim_number,
        amount=doc.get("claim_amount"),
        date=doc.get("incident_date"),
        location=doc.get("incident_location"),
        type=doc.get("incident_type"),
        description=doc.get("incident_description"),
        insurer=doc.get("insurer"),
        declaration_date=doc.get("declaration_date"),
    )

    # 3d. Optional policy link
    if doc.get("policy_number"):
        tx.run(
            """
            MATCH (cl:Claim {number: $claim_number})
            MERGE (p:Policy {number: $policy_number})
            MERGE (cl)-[:COVERED_BY]->(p)
            """,
            claim_number=claim_number,
            policy_number=doc["policy_number"],
        )

    # 3e. Optional doctor (+ hospital)
    doctor = doc.get("attending_doctor") or {}
    if doctor.get("reg_number") or doctor.get("name"):
        reg = doctor.get("reg_number") or f"name:{doctor.get('name')}"
        tx.run(
            """
            MATCH (cl:Claim {number: $claim_number})
            MERGE (d:Doctor {reg: $reg})
            SET d.name = $doctor_name
            MERGE (cl)-[:TREATED_BY]->(d)
            """,
            claim_number=claim_number,
            reg=reg,
            doctor_name=doctor.get("name"),
        )
        if doctor.get("hospital"):
            tx.run(
                """
                MATCH (d:Doctor {reg: $reg})
                MERGE (h:Hospital {name: $hospital})
                MERGE (d)-[:WORKS_AT]->(h)
                """,
                reg=reg,
                hospital=doctor["hospital"],
            )

    # 3f. Optional witness (Ring B signal lives here)
    witness = doc.get("witness") or {}
    if witness.get("phone") or witness.get("name"):
        phone = witness.get("phone") or f"name:{witness.get('name')}"
        tx.run(
            """
            MATCH (c:Claimant {id: $claimant_id})
            MERGE (w:Witness {phone: $phone})
            SET w.name = $w_name,
                w.id = $w_id,
                w.address = $w_address
            MERGE (c)-[:WITNESSED_BY]->(w)
            """,
            claimant_id=cid,
            phone=phone,
            w_name=witness.get("name"),
            w_id=witness.get("id"),
            w_address=witness.get("address"),
        )


def write_medical_report(tx, doc: dict):
    """MedicalReport → Claim, Doctor, Provider."""
    report_ref = doc.get("report_ref") or doc.get("claim_ref")
    if not report_ref:
        return

    patient = doc.get("patient") or {}
    doctor = doc.get("doctor") or {}
    reg = doctor.get("reg_number") or (
        f"name:{doctor.get('name')}" if doctor.get("name") else None
    )

    # 3g. Core report node + claim support edge
    tx.run(
        """
        MERGE (mr:MedicalReport {ref: $ref})
        SET mr.diagnosis = $diagnosis,
            mr.icd10 = $icd10,
            mr.treatment = $treatment,
            mr.medications = $medications,
            mr.presenting_complaints = $complaints,
            mr.cost = $cost,
            mr.visit_date = $visit_date
        WITH mr
        MERGE (cl:Claim {number: $claim_ref})
        MERGE (cl)-[:SUPPORTED_BY]->(mr)
        """,
        ref=report_ref,
        diagnosis=doc.get("diagnosis"),
        icd10=doc.get("icd10_code"),
        treatment=doc.get("treatment"),
        medications=doc.get("medications"),
        complaints=doc.get("presenting_complaints"),
        cost=doc.get("total_cost"),
        visit_date=doc.get("visit_date"),
        claim_ref=doc.get("claim_ref") or report_ref,
    )

    if reg:
        tx.run(
            """
            MATCH (mr:MedicalReport {ref: $ref})
            MERGE (d:Doctor {reg: $reg})
            SET d.name = $doctor_name
            MERGE (mr)-[:CERTIFIED_BY]->(d)
            """,
            ref=report_ref,
            reg=reg,
            doctor_name=doctor.get("name"),
        )
        if doctor.get("hospital"):
            tx.run(
                """
                MATCH (d:Doctor {reg: $reg})
                MERGE (h:Hospital {name: $hospital})
                MERGE (d)-[:WORKS_AT]->(h)
                """,
                reg=reg,
                hospital=doctor["hospital"],
            )

    # 3h. Billing provider (Ring A overbilling partner)
    if doc.get("billing_provider"):
        tx.run(
            """
            MATCH (mr:MedicalReport {ref: $ref})
            MERGE (pr:Provider {name: $provider})
            MERGE (mr)-[:BILLED_TO]->(pr)
            """,
            ref=report_ref,
            provider=doc["billing_provider"],
        )

    # Keep patient on the graph if we have an id
    pid = _claimant_id(patient)
    if pid:
        tx.run(
            """
            MERGE (c:Claimant {id: $id})
            SET c.name = coalesce($name, c.name),
                c.dob = coalesce($dob, c.dob),
                c.aliases = CASE
                  WHEN $name IS NULL THEN coalesce(c.aliases, [])
                  WHEN c.aliases IS NULL THEN [$name]
                  WHEN NOT $name IN c.aliases THEN c.aliases + $name
                  ELSE c.aliases
                END
            """,
            id=pid,
            name=patient.get("name"),
            dob=patient.get("dob"),
        )


def write_invoice(tx, doc: dict):
    """Invoice issued by Provider for a Claim (+ BILLED_BY on the claim)."""
    provider = doc.get("provider") or {}
    provider_name = provider.get("name")
    invoice_number = doc.get("invoice_number")
    claim_ref = doc.get("claim_reference")
    if not provider_name:
        return

    # 3i. Provider always exists for Ring A queries
    tx.run(
        """
        MERGE (pr:Provider {name: $name})
        SET pr.reg = $reg,
            pr.address = $address
        """,
        name=provider_name,
        reg=provider.get("reg"),
        address=provider.get("address"),
    )

    if invoice_number:
        tx.run(
            """
            MERGE (inv:Invoice {number: $number})
            SET inv.total = $total,
                inv.date = $date,
                inv.authorised_by = $authorised_by,
                inv.claimant_name = $claimant_name
            MERGE (pr:Provider {name: $provider})
            MERGE (inv)-[:ISSUED_BY]->(pr)
            """,
            number=invoice_number,
            total=doc.get("total_payable"),
            date=doc.get("invoice_date"),
            authorised_by=doc.get("authorised_by"),
            claimant_name=doc.get("claimant_name"),
            provider=provider_name,
        )

    if claim_ref:
        # Normalise claim refs that may have suffixes like _0
        claim_key = claim_ref.split("_")[0] if "_" in claim_ref else claim_ref
        tx.run(
            """
            MERGE (cl:Claim {number: $claim_ref})
            MERGE (pr:Provider {name: $provider})
            MERGE (cl)-[:BILLED_BY]->(pr)
            """,
            claim_ref=claim_key,
            provider=provider_name,
        )
        if invoice_number:
            tx.run(
                """
                MATCH (inv:Invoice {number: $number})
                MERGE (cl:Claim {number: $claim_ref})
                MERGE (inv)-[:FOR_CLAIM]->(cl)
                """,
                number=invoice_number,
                claim_ref=claim_key,
            )


def write_police_report(tx, doc: dict):
    """PoliceReport documented on Claim; witness may repeat (Ring B)."""
    report_number = doc.get("report_number")
    if not report_number:
        return

    claimant = doc.get("claimant") or {}
    cid = _claimant_id(claimant)
    claim_ref = doc.get("claim_ref")
    # Many reports embed CLM-… inside the GPS report number
    if not claim_ref and "CLM-" in report_number:
        start = report_number.index("CLM-")
        claim_ref = report_number[start:].split()[0]

    # 3j. Report node
    tx.run(
        """
        MERGE (pr:PoliceReport {number: $number})
        SET pr.date = $date,
            pr.time = $time,
            pr.location = $location,
            pr.type = $type,
            pr.description = $description,
            pr.officer = $officer,
            pr.badge = $badge
        """,
        number=report_number,
        date=doc.get("incident_date"),
        time=doc.get("incident_time"),
        location=doc.get("incident_location"),
        type=doc.get("incident_type"),
        description=doc.get("incident_description"),
        officer=doc.get("recording_officer"),
        badge=doc.get("officer_badge"),
    )

    if claim_ref:
        tx.run(
            """
            MATCH (pr:PoliceReport {number: $number})
            MERGE (cl:Claim {number: $claim_ref})
            MERGE (cl)-[:DOCUMENTED_IN]->(pr)
            """,
            number=report_number,
            claim_ref=claim_ref,
        )

    if cid:
        tx.run(
            """
            MATCH (pr:PoliceReport {number: $number})
            MERGE (c:Claimant {id: $claimant_id})
            SET c.name = coalesce($name, c.name),
                c.phone = coalesce($phone, c.phone),
                c.address = coalesce($address, c.address),
                c.aliases = CASE
                  WHEN $name IS NULL THEN coalesce(c.aliases, [])
                  WHEN c.aliases IS NULL THEN [$name]
                  WHEN NOT $name IN c.aliases THEN c.aliases + $name
                  ELSE c.aliases
                END
            MERGE (pr)-[:FILED_BY]->(c)
            """,
            number=report_number,
            claimant_id=cid,
            name=claimant.get("name"),
            phone=claimant.get("phone"),
            address=claimant.get("address"),
        )

    witness = doc.get("witness") or {}
    if witness.get("phone") or witness.get("name"):
        phone = witness.get("phone") or f"name:{witness.get('name')}"
        tx.run(
            """
            MATCH (pr:PoliceReport {number: $number})
            MERGE (w:Witness {phone: $phone})
            SET w.name = $w_name,
                w.id = $w_id,
                w.address = $w_address
            MERGE (pr)-[:WITNESSED_BY]->(w)
            """,
            number=report_number,
            phone=phone,
            w_name=witness.get("name"),
            w_id=witness.get("id"),
            w_address=witness.get("address"),
        )
        # Also link witness to claimant when both exist (matches Phase 4 query shape)
        if cid:
            tx.run(
                """
                MATCH (c:Claimant {id: $claimant_id})
                MATCH (w:Witness {phone: $phone})
                MERGE (c)-[:WITNESSED_BY]->(w)
                """,
                claimant_id=cid,
                phone=phone,
            )


# ── Step 4: Route each document to the right writer ──────────────────────────

WRITERS = {
    "policy": write_policy,
    "claim_form": write_claim,
    "medical_report": write_medical_report,
    "invoice": write_invoice,
    "police_report": write_police_report,
}


def write_document(driver, doc: dict):
    """Dispatch by doc_type using a write transaction."""
    # 4a. Look up the writer for this extraction type
    writer = WRITERS.get(doc.get("doc_type"))
    if not writer:
        raise ValueError(f"Unknown doc_type: {doc.get('doc_type')}")
    # 4b. execute_write retries transient Neo4j errors
    with driver.session() as session:
        session.execute_write(writer, doc)


# ── Step 5: Run the full graph population ────────────────────────────────────

def run_graph_population():
    console.rule("[bold cyan]Phase 3: Graph Population (final/)[/bold cyan]")

    data_path = _ROOT / "results" / "combined.json"
    if not data_path.exists():
        console.print(
            "[red]results/combined.json not found. Run final/01_extract.py first.[/red]"
        )
        return

    with open(data_path) as f:
        documents = json.load(f)

    console.print(f"Loaded [bold]{len(documents)}[/bold] extracted documents\n")

    console.print("Connecting to Neo4j...", end=" ")
    driver = get_driver()
    driver.verify_connectivity()
    console.print("[green]Connected[/green]")

    console.print("Creating constraints...", end=" ")
    create_constraints(driver)
    console.print("[green]Done[/green]\n")

    counts = {k: 0 for k in WRITERS}
    errors = []

    for doc in documents:
        try:
            # 5a. Write one document, then bump the counter for its type
            write_document(driver, doc)
            doc_type = doc.get("doc_type")
            if doc_type in counts:
                counts[doc_type] += 1
        except Exception as e:
            errors.append({"file": doc.get("file"), "error": str(e)})
            console.print(f"[red]✗[/red] {doc.get('file')}: {e}")

    table = Table(title="Graph Population Summary")
    table.add_column("Document Type", style="cyan")
    table.add_column("Written", justify="right", style="green")
    for doc_type, count in counts.items():
        table.add_row(doc_type, str(count))
    console.print(table)

    console.print(f"\n[green]{sum(counts.values())}[/green] documents written to Neo4j")
    if errors:
        console.print(f"[red]{len(errors)}[/red] errors")

    driver.close()
    console.print("\nNext: [bold]python final/03_query.py[/bold]")


if __name__ == "__main__":
    run_graph_population()
