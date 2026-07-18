# Graph Model — Insurance Fraud Knowledge Graph

## Node Labels

| Label | Key Property | Description |
|-------|-------------|-------------|
| `Claimant` | `id` (Ghana Card) | Person filing a claim |
| `Policy` | `number` | Insurance policy certificate |
| `Claim` | `number` | Individual insurance claim |
| `Doctor` | `reg` (MDC-GH-XXXXX) | Attending physician |
| `Hospital` | `name` | Medical facility |
| `Provider` | `name` | Billing/medical services provider |
| `MedicalReport` | `ref` | Medical report for insurance |
| `Invoice` | `number` | Provider invoice |
| `PoliceReport` | `number` | Ghana Police incident report |
| `Witness` | `phone` | Witness named on a claim |

### Useful optional properties (from extraction)

These do **not** add new labels — set them on existing nodes when present:

| Node | Extra properties |
|------|------------------|
| `Policy` | `coverage_items`, `authorised_officer` |
| `Claim` | `insurer`, `declaration_date` |
| `MedicalReport` | `icd10`, `medications`, `presenting_complaints` |
| `Invoice` | `authorised_by` |
| `PoliceReport` | `time`, `type`, `badge` |

## Relationships

```
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
```

## Visual Schema

```
                    ┌──────────┐
                    │ Claimant │
                    └────┬─────┘
              HAS_POLICY │  FILED      WITNESSED_BY
                         │    │              │
                    ┌────▼─┐  ▼          ┌──▼─────┐
                    │Policy│ Claim ──────►│Witness │
                    └──────┘  │           └────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
          TREATED_BY     BILLED_BY    SUPPORTED_BY
               │              │              │
          ┌────▼───┐    ┌─────▼────┐  ┌─────▼────────┐
          │ Doctor │    │ Provider │  │ MedicalReport │
          └────┬───┘    └──────────┘  └──────────────┘
          WORKS_AT
               │
          ┌────▼────┐
          │Hospital │
          └─────────┘
```

## Why Graph over SQL?

To find Ring A fraud in SQL:
```sql
SELECT d.name, COUNT(DISTINCT c.id) as claimant_count
FROM claims cl
JOIN doctors d ON cl.doctor_id = d.id
JOIN claimants c ON cl.claimant_id = c.id
JOIN invoices i ON cl.id = i.claim_id
JOIN providers p ON i.provider_id = p.id
WHERE p.name = 'MediQuick Services Ltd'
GROUP BY d.name
HAVING claimant_count > 2;
```
— 3 JOINs, brittle, misses cross-document connections.

Same query in Cypher:
```cypher
MATCH (c:Claimant)-[:FILED]->(:Claim)-[:TREATED_BY]->(d:Doctor),
      (:Claim)-[:BILLED_BY]->(p:Provider {name: 'MediQuick Services Ltd'})
RETURN d.name, count(DISTINCT c) as claimants
```
— 1 pattern, reads like English, traverses relationships natively.
