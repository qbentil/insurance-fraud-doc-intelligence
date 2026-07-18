"""
02_graph.py — Phase 3: Populating the Knowledge Graph
======================================================
WORKSHOP PHASE 3 · 45 minutes

YOUR TASK: Read extracted_data.json and write each entity
into Neo4j as nodes and relationships.

Graph Model:
    (:Claimant)-[:FILED]->(:Claim)-[:COVERED_BY]->(:Policy)
    (:Claim)-[:TREATED_BY]->(:Doctor)-[:WORKS_AT]->(:Hospital)
    (:Claim)-[:BILLED_BY]->(:Provider)
    (:Claim)-[:SUPPORTED_BY]->(:MedicalReport)
    (:Claim)-[:DOCUMENTED_IN]->(:PoliceReport)
    (:Claimant)-[:WITNESSED_BY]->(:Witness)
    (:Claimant)-[:HAS_POLICY]->(:Policy)

Run from the repo root:
    python starter/02_graph.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Allow `python starter/02_graph.py` from the repo root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# TODO: Import the Neo4j driver
# from neo4j import GraphDatabase

load_dotenv(_ROOT / ".env")
console = Console()


# ── Step 1: Connect to Neo4j ─────────────────────────────────────────────────

def get_driver():
    """
    TODO: Create and return a Neo4j driver using credentials from .env.

    Example:
        from neo4j import GraphDatabase
        return GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Connect to Neo4j in get_driver()")


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
    """
    TODO: Run each constraint query in CONSTRAINTS above.

    Hint:
        with driver.session() as session:
            for q in CONSTRAINTS:
                session.run(q)
    """
    # TODO: Implement this
    raise NotImplementedError("TODO: Create constraints in create_constraints()")


# ── Step 3: Write nodes & relationships ──────────────────────────────────────

def write_policy(tx, doc: dict):
    """
    TODO: MERGE a Policy node and its Claimant, then create HAS_POLICY.

    Cypher pattern:
        MERGE (c:Claimant {id: $claimant_id})
        SET c.name = $name, c.phone = $phone, c.address = $address
        MERGE (p:Policy {number: $policy_number})
        SET p.insurer = $insurer, p.coverage = $coverage,
            p.premium = $premium, p.sum_insured = $sum_insured,
            p.coverage_items = $coverage_items, p.authorised_officer = $officer
        MERGE (c)-[:HAS_POLICY]->(p)

    Use tx.run(cypher, **params) to execute.
    """
    # TODO: Implement this
    pass


def write_claim(tx, doc: dict):
    """
    TODO: Write a Claim node and connect it to Claimant, Policy, Doctor, Witness.

    Nodes to MERGE:
        - (:Claimant {id})
        - (:Claim {number: claim_number})
          SET amount, date, location, type, insurer, declaration_date
        - (:Policy {number: policy_number}) — if present
        - (:Doctor {reg: reg_number})       — if present
        - (:Hospital {name})                — if doctor has hospital
        - (:Witness {phone})                — if witness present

    Relationships:
        (:Claimant)-[:FILED]->(:Claim)
        (:Claim)-[:COVERED_BY]->(:Policy)
        (:Claim)-[:TREATED_BY]->(:Doctor)-[:WORKS_AT]->(:Hospital)
        (:Claimant)-[:WITNESSED_BY]->(:Witness)
    """
    # TODO: Implement this
    pass


def write_medical_report(tx, doc: dict):
    """
    TODO: Write a MedicalReport node and connect to Claim, Doctor, Provider.

    Nodes to MERGE:
        - (:MedicalReport {ref: report_ref})
          SET diagnosis, icd10, treatment, medications, cost, visit_date
        - (:Claim {number: claim_ref})
        - (:Doctor {reg})
        - (:Provider {name: billing_provider})

    Relationships:
        (:Claim)-[:SUPPORTED_BY]->(:MedicalReport)
        (:MedicalReport)-[:CERTIFIED_BY]->(:Doctor)
        (:MedicalReport)-[:BILLED_TO]->(:Provider)
    """
    # TODO: Implement this
    pass


def write_invoice(tx, doc: dict):
    """
    TODO: Write an Invoice node and connect to Claim and Provider.

    Nodes to MERGE:
        - (:Invoice {number: invoice_number})  SET total, date, authorised_by
        - (:Provider {name})  SET reg, address
        - (:Claim {number: claim_reference})

    Relationships:
        (:Claim)-[:BILLED_BY]->(:Provider)
        (:Invoice)-[:ISSUED_BY]->(:Provider)
        (:Invoice)-[:FOR_CLAIM]->(:Claim)
    """
    # TODO: Implement this
    pass


def write_police_report(tx, doc: dict):
    """
    TODO: Write a PoliceReport node and connect to Claim, Claimant, Witness.

    Nodes to MERGE:
        - (:PoliceReport {number: report_number})
          SET date, time, location, type, description, officer, badge
        - (:Claim {number: claim_ref})
        - (:Claimant {id})
        - (:Witness {phone}) — if witness present

    Relationships:
        (:Claim)-[:DOCUMENTED_IN]->(:PoliceReport)
        (:PoliceReport)-[:FILED_BY]->(:Claimant)
        (:PoliceReport)-[:WITNESSED_BY]->(:Witness)
    """
    # TODO: Implement this
    pass


# ── Step 4: Route each document to the right writer ──────────────────────────

WRITERS = {
    "policy": write_policy,
    "claim_form": write_claim,
    "medical_report": write_medical_report,
    "invoice": write_invoice,
    "police_report": write_police_report,
}


def write_document(driver, doc: dict):
    """
    TODO: Route a document to the right write function based on doc["doc_type"].

    Hint:
        writer = WRITERS.get(doc.get("doc_type"))
        if writer:
            with driver.session() as session:
                session.execute_write(writer, doc)
    """
    # TODO: Implement this
    pass


# ── Step 5: Run the full graph population ────────────────────────────────────

def run_graph_population():
    console.rule("[bold cyan]Phase 3: Graph Population[/bold cyan]")

    data_path = _ROOT / "extracted_data.json"
    if not data_path.exists():
        console.print("[red]extracted_data.json not found. Run 01_extract.py first.[/red]")
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
            # TODO: Call write_document(driver, doc) and increment counts[doc["doc_type"]]
            pass  # ← Replace with your implementation
        except Exception as e:
            errors.append({"file": doc.get("file"), "error": str(e)})

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
    console.print("\nNext: [bold]python starter/03_query.py[/bold]")


if __name__ == "__main__":
    run_graph_population()
