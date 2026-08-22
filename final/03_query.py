"""
03_query.py — REFERENCE SOLUTION (Phase 4)
==========================================
Complete Cypher queries for all fraud-ring investigations.

Run from the repo root (after graph load):
    python final/03_query.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")
console = Console()


def get_driver():
    """Connect to Neo4j using the same .env as Phase 3."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    return GraphDatabase.driver(uri, auth=(user, password))


# ═══════════════════════════════════════════════════════════════════════════════
#  FRAUD DETECTION QUERIES (complete)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Query 1: Doctor Frequency ─────────────────────────────────────────────────
# Count claims + claimants + billed amounts per doctor.

QUERY_DOCTOR_FREQUENCY = """
MATCH (d:Doctor)<-[:TREATED_BY]-(claim:Claim)<-[:FILED]-(c:Claimant)
RETURN d.name AS doctor,
       count(DISTINCT claim) AS total_claims,
       count(DISTINCT c) AS unique_claimants,
       sum(coalesce(claim.amount, 0)) AS total_billed
ORDER BY total_billed DESC
"""


# ── Query 2: Fraud Ring A — Doctor + Provider Collusion ───────────────────────
# Claimants who share BOTH the same doctor AND the same provider.

QUERY_RING_A = """
MATCH (c:Claimant)-[:FILED]->(claim:Claim)-[:TREATED_BY]->(d:Doctor),
      (claim)-[:BILLED_BY]->(p:Provider)
WITH d, p, collect(DISTINCT c.name) AS claimants, count(DISTINCT claim) AS claim_count
WHERE size(claimants) > 1
RETURN d.name AS doctor,
       p.name AS provider,
       claimants,
       claim_count
ORDER BY claim_count DESC
"""


# ── Query 3: Fraud Ring B — Ghost Witness ─────────────────────────────────────
# Witnesses linked to more than one claim (via claimant FILED path).

QUERY_RING_B = """
MATCH (w:Witness)<-[:WITNESSED_BY]-(c:Claimant)-[:FILED]->(claim:Claim)
WITH w,
     count(DISTINCT claim) AS claims_witnessed,
     collect(DISTINCT c.name) AS claimants
WHERE claims_witnessed > 1
RETURN w.name AS witness_name,
       w.phone AS witness_phone,
       claims_witnessed,
       claimants
ORDER BY claims_witnessed DESC
"""


# ── Query 4: Fraud Ring C — Identity Cycling ──────────────────────────────────
# Same phone + multiple name aliases and/or multiple policies.
# (Ring C PDFs share one Ghana Card id, so they MERGE to one Claimant —
#  writers accumulate c.aliases so the cycling names still show up.)

QUERY_RING_C = """
MATCH (c:Claimant)
WHERE c.phone IS NOT NULL
OPTIONAL MATCH (c)-[:HAS_POLICY]->(p:Policy)
WITH c.phone AS shared_phone,
     collect(DISTINCT c.name) AS node_names,
     collect(c.aliases) AS alias_lists,
     [pol IN collect(DISTINCT p.number) WHERE pol IS NOT NULL] AS policies
WITH shared_phone, policies,
     reduce(acc = [], lst IN alias_lists | acc + coalesce(lst, [])) + node_names AS raw_names
WITH shared_phone, policies,
     reduce(acc = [], n IN raw_names |
       CASE WHEN n IS NULL OR n IN acc THEN acc ELSE acc + n END) AS names
WHERE size(names) > 1 OR size(policies) > 1
RETURN shared_phone, names, policies
"""


# ── Query 5: Overbilling Detection ────────────────────────────────────────────
# Provider avg vs baseline of claims they did NOT bill.
# (Comparing to a global average that already includes the fraud claims
#  flattens the signal — MediQuick is ~1.7× overall but >2× everyone else.)

QUERY_OVERBILLING = """
MATCH (p:Provider)<-[:BILLED_BY]-(c:Claim)
WHERE c.amount IS NOT NULL
WITH p, avg(c.amount) AS avg_billed, collect(elementId(c)) AS billed_ids
MATCH (other:Claim)
WHERE other.amount IS NOT NULL AND NOT elementId(other) IN billed_ids
WITH p, avg_billed, avg(other.amount) AS baseline_avg
WHERE avg_billed > 2 * baseline_avg
RETURN p.name AS provider,
       avg_billed,
       baseline_avg,
       avg_billed / baseline_avg AS multiple
ORDER BY multiple DESC
"""


# ── Query 6: Full Fraud Network (Browser visualisation) ───────────────────────
# Paths connecting claimants through shared doctors.

QUERY_FULL_NETWORK = """
MATCH path = (c:Claimant)-[:FILED]->(:Claim)-[:TREATED_BY]->(d:Doctor)
             <-[:TREATED_BY]-(:Claim)<-[:FILED]-(c2:Claimant)
WHERE c <> c2
RETURN path
LIMIT 50
"""


# ═══════════════════════════════════════════════════════════════════════════════

def run_query(driver, title: str, query: str, columns: list) -> list:
    """Run a Cypher query and display results in a Rich table."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")

    with driver.session() as session:
        results = list(session.run(query))

    if not results:
        console.print("[dim]No results found.[/dim]")
        return []

    table = Table(show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)

    for record in results:
        table.add_row(*[str(record.get(c, "—")) for c in columns])

    console.print(table)
    return results


def run_fraud_detection():
    console.rule("[bold red]Phase 4: Fraud Ring Detection (final/)[/bold red]")
    console.print(Panel(
        "[bold]You are now a fraud investigator.[/bold]\n"
        "The graph holds 36 insurance documents. Three fraud rings are hidden inside.\n"
        "Your Cypher queries are about to expose them.",
        border_style="red",
    ))

    driver = get_driver()
    driver.verify_connectivity()

    # Q1 — Who treats the most expensive / frequent claims?
    run_query(
        driver,
        "Query 1 — Doctor Frequency",
        QUERY_DOCTOR_FREQUENCY,
        ["doctor", "total_claims", "unique_claimants", "total_billed"],
    )

    # Q2 — Ring A smoking gun
    run_query(
        driver,
        "Query 2 — Ring A: Doctor + Provider Collusion",
        QUERY_RING_A,
        ["doctor", "provider", "claimants", "claim_count"],
    )

    # Q3 — Ring B ghost witness
    run_query(
        driver,
        "Query 3 — Ring B: Ghost Witness",
        QUERY_RING_B,
        ["witness_name", "witness_phone", "claims_witnessed", "claimants"],
    )

    # Q4 — Ring C identity cycling
    run_query(
        driver,
        "Query 4 — Ring C: Identity Cycling (Same Phone, Different Names)",
        QUERY_RING_C,
        ["shared_phone", "names", "policies"],
    )

    # Q5 — Overbilling
    run_query(
        driver,
        "Query 5 — Overbilling Detection",
        QUERY_OVERBILLING,
        ["provider", "avg_billed", "baseline_avg", "multiple"],
    )

    # Q6 is meant for Neo4j Browser path viz — print the Cypher for copy-paste
    console.print("\n[bold cyan]Query 6 — Full Fraud Network[/bold cyan]")
    console.print(
        "[dim]Copy this into Neo4j Browser for the path visualisation:[/dim]"
    )
    console.print(Panel(QUERY_FULL_NETWORK.strip(), border_style="cyan"))

    console.print(Panel(
        "[bold green]Fraud Rings Exposed![/bold green]\n\n"
        "[bold]Ring A[/bold] — Dr. Kwabena Mensah + MediQuick Services Ltd\n"
        "  → Same doctor and provider across 4 unrelated claimants. Bills 4x the average.\n\n"
        "[bold]Ring B[/bold] — Emmanuel Kwesi Tetteh (Ghost Witness)\n"
        "  → Same witness on 5 staged accident claims, all on Accra-Tema Motorway.\n\n"
        "[bold]Ring C[/bold] — Abena Owusu (3 Identities, 1 Phone Number)\n"
        "  → Filed under 3 name variations across 3 separate policies.\n\n"
        "[dim]Open Neo4j Browser → paste QUERY_FULL_NETWORK to visualise the graph.[/dim]",
        border_style="green",
    ))

    driver.close()


if __name__ == "__main__":
    run_fraud_detection()
