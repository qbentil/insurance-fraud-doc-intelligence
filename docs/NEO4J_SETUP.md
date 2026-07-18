# Neo4j Setup Guide

This workshop needs a running Neo4j database. Pick **one** option:

| Option | Best for | Install? |
|--------|----------|----------|
| [AuraDB Free](#option-a--neo4j-auradb-free-cloud) | Workshop day (fastest) | No |
| [Neo4j Desktop](#option-b--neo4j-desktop-local) | Offline / local practice | Yes |

After setup, put the connection details in your project `.env` (copied from `.env.example`).

```env
NEO4J_URI=...
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
```

---

## Option A — Neo4j AuraDB Free (Cloud)

Recommended for the workshop: no local install, works from any laptop with internet.

### 1. Create an account

1. Open [https://console.neo4j.io](https://console.neo4j.io)
2. Sign up or log in (GitHub / Google / email)

### 2. Create a free instance

1. Click **New Instance** (or **Create instance**)
2. Choose the **Free** tier (AuraDB Free)
3. Pick a region close to you
4. Give the instance a name (e.g. `fraud-workshop`)
5. Click **Create**

Aura generates a password **once**. Copy it immediately and store it somewhere safe — you will not see it again.

### 3. Copy connection details

On the instance card / connection panel you will see:

| Field | Example | Goes in `.env` as |
|-------|---------|-------------------|
| Connection URI | `neo4j+s://xxxxxxxx.databases.neo4j.io` | `NEO4J_URI` |
| Username | `neo4j` | `NEO4J_USERNAME` |
| Password | *(the one you saved)* | `NEO4J_PASSWORD` |

Use the **`neo4j+s://`** URI (encrypted). Do **not** use `bolt://` for Aura.

Example `.env`:

```env
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-aura-password
```

### 4. Open Neo4j Browser (optional but useful)

1. In the Aura console, open your instance
2. Click **Query** / **Open** → Neo4j Browser
3. Run:

```cypher
RETURN 'Aura is ready' AS status
```

You will use Browser again in Phase 4 to visualise fraud rings.

### 5. Pause / resume

Free instances pause after inactivity. Before the workshop (and before Phase 3), open the Aura console and **Resume** the instance if it shows as paused.

---

## Option B — Neo4j Desktop (Local)

Use this if you prefer running Neo4j on your machine or expect weak conference Wi‑Fi for cloud DB traffic.

### 1. Install Neo4j Desktop

1. Download from [https://neo4j.com/download/](https://neo4j.com/download/)
2. Install and open **Neo4j Desktop**
3. Activate with a free Desktop key if prompted (from the download page / email)

### 2. Create a local DBMS

1. Create or open a **Project** (e.g. `Workshop`)
2. Click **Add** → **Local DBMS**
3. Name it (e.g. `fraud-graph`)
4. Set a password (remember it — this becomes `NEO4J_PASSWORD`)
5. Choose Neo4j version **5.x** if asked
6. Click **Create**

### 3. Start the database

1. Click **Start** on the DBMS
2. Wait until status is **Active**
3. Default Bolt port is **7687**

### 4. Copy connection details into `.env`

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=the-password-you-set
```

If you changed the Bolt port in Desktop settings, update `NEO4J_URI` to match (e.g. `bolt://localhost:7688`).

### 5. Open Neo4j Browser locally

1. With the DBMS running, click **Open** → **Neo4j Browser**
2. Log in with username `neo4j` and your password
3. Run:

```cypher
RETURN 'Local Neo4j is ready' AS status
```

### 6. Reset the graph between practice runs (optional)

If you re-run Phase 3 and want a clean database:

```cypher
MATCH (n) DETACH DELETE n
```

Only run this on your workshop database — it deletes all nodes and relationships.

---

## Verify from Python

From the repo root (with your venv activated and `.env` filled in):

```bash
python -c "
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD')),
)
driver.verify_connectivity()
print('Neo4j connection OK')
driver.close()
"
```

You should see `Neo4j connection OK`. If it fails, check the troubleshooting section below.

Also run the full workshop setup check:

```bash
python starter/schemas.py
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| `ServiceUnavailable` / connection refused | Local DBMS not started | Start the DBMS in Neo4j Desktop |
| Aura connection timeout | Instance paused or bad URI | Resume instance; confirm `neo4j+s://` URI |
| `Unauthorized` / auth failed | Wrong password | Reset password in Aura or Desktop; update `.env` |
| Works in Browser, fails in Python | `.env` not loaded / wrong directory | Run commands from repo root; confirm `.env` exists |
| SSL / certificate errors on Aura | Using `bolt://` instead of `neo4j+s://` | Switch URI to `neo4j+s://...` |
| Port already in use (Desktop) | Another Neo4j/process on 7687 | Stop the other process or change Bolt port |

---

## Security reminders

- Never commit `.env` (it is already in `.gitignore`)
- Do not paste Aura passwords into public chat, slides, or GitHub Issues
- Free Aura instances are fine for this workshop; delete the instance after if you no longer need it

---

## Next steps

Once Neo4j connects:

1. Complete Phase 2 → `python starter/01_extract.py`
2. Load the graph → `python starter/02_graph.py`
3. Run fraud queries → `python starter/03_query.py`

See also: [GRAPH_MODEL.md](GRAPH_MODEL.md) · [CYPHER_CHEATSHEET.md](CYPHER_CHEATSHEET.md)
