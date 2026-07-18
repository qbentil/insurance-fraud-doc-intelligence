"""
schema_context.py — Graph schema text injected into NL→Cypher prompts
=====================================================================
Kept inside bonus/ so the walkthrough stays self-contained.
"""

GRAPH_SCHEMA = """
You are querying an insurance fraud knowledge graph in Neo4j (Ghana NIC context).

NODE LABELS AND KEY PROPERTIES:
- Claimant {id, name, phone, address, dob}
- Policy {number, insurer, coverage, premium, sum_insured, coverage_items, authorised_officer}
- Claim {number, amount, date, location, type, description, insurer, declaration_date}
- Doctor {reg, name, hospital}
- Hospital {name}
- Provider {name, reg, address}
- MedicalReport {ref, diagnosis, icd10, treatment, medications, presenting_complaints, cost, visit_date}
- Invoice {number, total, date, authorised_by}
- PoliceReport {number, date, time, location, type, description, officer, badge}
- Witness {phone, name, id, address}

RELATIONSHIPS:
(:Claimant)-[:HAS_POLICY]->(:Policy)
(:Claimant)-[:FILED]->(:Claim)
(:Claimant)-[:WITNESSED_BY]->(:Witness)
(:Claim)-[:COVERED_BY]->(:Policy)
(:Claim)-[:TREATED_BY]->(:Doctor)
(:Claim)-[:BILLED_BY]->(:Provider)
(:Claim)-[:SUPPORTED_BY]->(:MedicalReport)
(:Claim)-[:DOCUMENTED_IN]->(:PoliceReport)
(:Doctor)-[:WORKS_AT]->(:Hospital)
(:MedicalReport)-[:CERTIFIED_BY]->(:Doctor)
(:MedicalReport)-[:BILLED_TO]->(:Provider)
(:Invoice)-[:ISSUED_BY]->(:Provider)
(:Invoice)-[:FOR_CLAIM]->(:Claim)
(:PoliceReport)-[:FILED_BY]->(:Claimant)
(:PoliceReport)-[:WITNESSED_BY]->(:Witness)

FRAUD PATTERNS THIS GRAPH CAN REVEAL:
- Ring A: same Doctor + same Provider across multiple Claimants
- Ring B: same Witness on multiple unrelated Claims (ghost witness)
- Ring C: same phone on Claimants with different names (identity cycling)
- Overbilling: Provider average amount much higher than overall average
"""
