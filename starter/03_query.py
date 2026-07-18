"""
03_query.py — Phase 4: Fraud Ring Detection with Cypher
=======================================================
WORKSHOP PHASE 4 · 25 minutes

YOUR TASK: Write Cypher queries that expose the 3 fraud rings
hidden in the knowledge graph.

Run from the repo root:
    python starter/03_query.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Allow `python starter/03_query.py` from the repo root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# TODO: from neo4j import GraphDatabase

load_dotenv(_ROOT / ".env")
console = Console()


def get_driver():
    """TODO: Same as 02_graph.py — connect to Neo4j."""
    raise NotImplementedError("TODO: Connect to Neo4j")


# ═══════════════════════════════════════════════════════════════════════════════
#  FRAUD DETECTION QUERIES
#  Complete each query below. The comments tell you what to find.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Query 1: Doctor Frequency ─────────────────────────────────────────────────
# Find doctors appearing across the most claims.
# A legitimate doctor serves many patients — but a fraudulent one
# appears with the same small group of claimants repeatedly.

QUERY_DOCTOR_FREQUENCY = """
TODO: Write a Cypher query that returns:
  - doctor name
  - number of distinct claims they appear on
  - number of distinct claimants they treated
  - total amount claimed across their cases

Order by total amount descending.

Hint:
MATCH (d:Doctor)<-[:TREATED_BY]-(claim:Claim)<-[:FILED]-(c:Claimant)
RETURN ...
"""


# ── Query 2: Fraud Ring A — Doctor + Provider Collusion ───────────────────────
# Find claimants who share BOTH the same doctor AND the same provider.
# In a legitimate system, claimants independently choose their doctors.
# When the same doctor+provider pair appears across multiple unrelated
# claimants, it signals coordinated fraud.

QUERY_RING_A = """
TODO: Write a Cypher query that finds groups of claimants
who share the same doctor AND the same billing provider.

Return: doctor name, provider name, list of claimant names, claim count

Hint: You need two MATCH paths that share (d:Doctor) and (p:Provider)
but have different (c1:Claimant) and (c2:Claimant).
"""


# ── Query 3: Fraud Ring B — Ghost Witness ─────────────────────────────────────
# Find witnesses who appear on more than one claim.
# A legitimate witness is present at ONE incident.
# Appearing on multiple unrelated claims is a strong fraud signal.

QUERY_RING_B = """
TODO: Write a Cypher query that finds witnesses appearing
on more than one claim or police report.

Return: witness name, witness phone, number of claims witnessed,
        list of claimant names they witnessed for.

Hint:
MATCH (w:Witness)<-[:WITNESSED_BY]-(c:Claimant)-[:FILED]->(claim:Claim)
RETURN w.name, w.phone, count(DISTINCT claim) as claims_witnessed,
       collect(DISTINCT c.name) as claimants
HAVING claims_witnessed > 1
"""


# ── Query 4: Fraud Ring C — Identity Cycling ──────────────────────────────────
# Find claimants who share the same phone number but have different names.
# This exposes someone using multiple identities to file claims
# under different policy numbers.

QUERY_RING_C = """
TODO: Write a Cypher query that finds claimants sharing
the same phone number but registered under different names.

Return: shared phone number, list of names using that phone,
        list of policy numbers associated.

Hint:
MATCH (c1:Claimant)-[:HAS_POLICY]->(p:Policy),
      (c2:Claimant)-[:HAS_POLICY]->(p2:Policy)
WHERE c1.phone = c2.phone AND c1.name <> c2.name
RETURN c1.phone as shared_phone,
       collect(DISTINCT c1.name) + collect(DISTINCT c2.name) as names,
       collect(DISTINCT p.number) + collect(DISTINCT p2.number) as policies
"""


# ── Query 5: Overbilling Detection ────────────────────────────────────────────
# Find providers billing significantly above the average claim amount.
# Compare each provider's average billing to the overall average.

QUERY_OVERBILLING = """
TODO: Write a Cypher query that:
1. Calculates the overall average claim amount
2. Returns each provider with their avg billing
3. Flags providers billing more than 2x the average

Return: provider name, their avg amount, overall avg, multiple (ratio)
Order by multiple descending.
"""


# ── Query 6: Full Fraud Network (The Big Reveal) ──────────────────────────────
# Return the entire fraud network as a path query.
# This is the SHOWSTOPPER query for the workshop — it draws
# the connected fraud ring on the Neo4j Browser graph visualisation.

QUERY_FULL_NETWORK = """
TODO: Write a Cypher query that returns all paths connecting
suspicious claimants through shared doctors, providers, and witnesses.

Hint: Use variable-length path matching.
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

    if query.strip().startswith("TODO"):
        console.print("[yellow]Query not yet implemented — complete the TODO above.[/yellow]")
        return []

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
    console.rule("[bold red]Phase 4: Fraud Ring Detection[/bold red]")
    console.print(Panel(
        "[bold]You are now a fraud investigator.[/bold]\n"
        "The graph holds 36 insurance documents. Three fraud rings are hidden inside.\n"
        "Your Cypher queries are about to expose them.",
        border_style="red"
    ))

    driver = get_driver()
    driver.verify_connectivity()

    run_query(driver, "Query 1 — Doctor Frequency",
              QUERY_DOCTOR_FREQUENCY,
              ["doctor", "total_claims", "unique_claimants", "total_billed"])

    run_query(driver, "Query 2 — Ring A: Doctor + Provider Collusion",
              QUERY_RING_A,
              ["doctor", "provider", "claimants", "claim_count"])

    run_query(driver, "Query 3 — Ring B: Ghost Witness",
              QUERY_RING_B,
              ["witness_name", "witness_phone", "claims_witnessed", "claimants"])

    run_query(driver, "Query 4 — Ring C: Identity Cycling (Same Phone, Different Names)",
              QUERY_RING_C,
              ["shared_phone", "names", "policies"])

    run_query(driver, "Query 5 — Overbilling Detection",
              QUERY_OVERBILLING,
              ["provider", "avg_billed", "overall_avg", "multiple"])

    console.print(Panel(
        "[bold green]Fraud Rings Exposed![/bold green]\n\n"
        "[bold]Ring A[/bold] — Dr. Kwabena Mensah + MediQuick Services Ltd\n"
        "  → Same doctor and provider across 4 unrelated claimants. Bills 4x the average.\n\n"
        "[bold]Ring B[/bold] — Emmanuel Kwesi Tetteh (Ghost Witness)\n"
        "  → Same witness on 5 staged accident claims, all on Accra-Tema Motorway.\n\n"
        "[bold]Ring C[/bold] — Abena Owusu (3 Identities, 1 Phone Number)\n"
        "  → Filed under 3 name variations across 3 separate policies.\n\n"
        "[dim]Open Neo4j Browser → run QUERY_FULL_NETWORK to visualise the graph.[/dim]",
        border_style="green"
    ))

    driver.close()


if __name__ == "__main__":
    run_fraud_detection()
