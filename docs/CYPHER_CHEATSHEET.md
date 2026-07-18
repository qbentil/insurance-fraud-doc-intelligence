# Cypher Quick Reference
## For Workshop Participants — PyCon Ghana 2026

---

## Core Syntax

```cypher
-- Create a node
CREATE (n:Person {name: 'Kofi', age: 30})

-- Find a node
MATCH (n:Person {name: 'Kofi'}) RETURN n

-- Create a relationship
MATCH (a:Person {name: 'Kofi'}), (b:Person {name: 'Ama'})
CREATE (a)-[:KNOWS]->(b)

-- MERGE (create if not exists)
MERGE (n:Claimant {id: 'GHA-7731-2019'})
SET n.name = 'Kofi Asante Boateng'
RETURN n
```

---

## Pattern Matching

```cypher
-- Two-hop path
MATCH (a)-[:FILED]->(b)-[:TREATED_BY]->(c)
RETURN a.name, c.name

-- Variable-length path (1 to 3 hops)
MATCH path = (a)-[*1..3]->(b)
RETURN path

-- Optional match (like LEFT JOIN)
MATCH (c:Claimant)
OPTIONAL MATCH (c)-[:FILED]->(claim:Claim)
RETURN c.name, claim.number
```

---

## Filtering & Aggregation

```cypher
-- WHERE
MATCH (c:Claimant)-[:FILED]->(claim:Claim)
WHERE claim.amount > 10000
RETURN c.name, claim.amount

-- COUNT, COLLECT, SUM
MATCH (d:Doctor)<-[:TREATED_BY]-(claim:Claim)
RETURN d.name,
       count(claim)          AS total_claims,
       sum(claim.amount)     AS total_billed,
       collect(claim.number) AS claim_numbers

-- HAVING equivalent (filter on aggregation)
MATCH (w:Witness)<-[:WITNESSED_BY]-(c:Claimant)
WITH w, count(c) AS witness_count
WHERE witness_count > 1
RETURN w.name, witness_count
```

---

## Fraud Detection Patterns

```cypher
-- Shared relationship (two nodes connected to same third node)
MATCH (c1:Claimant)-[:FILED]->(:Claim)-[:TREATED_BY]->(d:Doctor),
      (c2:Claimant)-[:FILED]->(:Claim)-[:TREATED_BY]->(d)
WHERE c1 <> c2
RETURN d.name, c1.name, c2.name

-- Find nodes with same property but different identity
MATCH (c1:Claimant), (c2:Claimant)
WHERE c1.phone = c2.phone
  AND c1.name <> c2.name
RETURN c1.name, c2.name, c1.phone

-- Degree centrality (most connected node)
MATCH (n)-[r]-()
RETURN n.name, count(r) AS degree
ORDER BY degree DESC
LIMIT 10
```

---

## Useful Commands

```cypher
-- See all node labels
CALL db.labels()

-- See all relationship types
CALL db.relationshipTypes()

-- Count all nodes
MATCH (n) RETURN count(n)

-- Delete everything (careful!)
MATCH (n) DETACH DELETE n

-- Show schema
CALL db.schema.visualization()
```
