"""
app.py — Investigator Chat UI (Streamlit)
=========================================
BONUS — run only if time remains after Phase 4.

    streamlit run bonus/app.py

Chat with the fraud graph in natural language. Each answer shows the
Cypher the LLM wrote — the same investigation patterns as starter/03_query.py.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

from bonus.nl2cypher import ask, get_driver, node_count  # noqa: E402

# Short label + full question (cards show label; click sends full question)
CASE_FILE = [
    {
        "ring": "Lead",
        "label": "Doctor frequency",
        "question": "Which doctors appear across the most claims?",
    },
    {
        "ring": "Ring A",
        "label": "Doctor + provider collusion",
        "question": "Which claimants share the same doctor AND the same provider?",
    },
    {
        "ring": "Ring B",
        "label": "Ghost witness",
        "question": "Which witnesses appear on more than one claim?",
    },
    {
        "ring": "Ring C",
        "label": "Identity cycling",
        "question": "Are there different claimant names sharing the same phone number?",
    },
    {
        "ring": "Lead",
        "label": "Provider overbilling",
        "question": "Which providers bill more than twice the average claim amount?",
    },
    {
        "ring": "Network",
        "label": "Shared-doctor network",
        "question": "Show me the network of claimants connected through shared doctors",
    },
]

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

html, body, [class*="css"] {
  font-family: 'DM Sans', system-ui, sans-serif;
}

/* Constrain main column — kill the ultra-wide stretch */
.main .block-container {
  max-width: 720px !important;
  padding-top: 1.75rem !important;
  padding-bottom: 6rem !important;
}

/* Atmosphere */
.stApp {
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, #1a2a24 0%, transparent 55%),
    linear-gradient(180deg, #0e1110 0%, #121816 40%, #0c0f0e 100%);
}

h1, h2, h3 {
  font-family: 'Fraunces', Georgia, serif !important;
  letter-spacing: -0.02em;
}

/* Hero */
.inv-hero {
  margin-bottom: 1.5rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid rgba(196, 165, 116, 0.25);
}
.inv-kicker {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #c4a574;
  margin-bottom: 0.35rem;
}
.inv-hero h1 {
  font-size: 2rem !important;
  font-weight: 700 !important;
  color: #f3efe6 !important;
  margin: 0 0 0.4rem 0 !important;
  line-height: 1.15 !important;
}
.inv-sub {
  color: #9aa59c;
  font-size: 0.95rem;
  line-height: 1.45;
  max-width: 36rem;
}

/* Case file section */
.case-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #c4a574;
  margin: 0.5rem 0 0.75rem 0;
}

/* Template card buttons */
div[data-testid="stHorizontalBlock"] button[kind="secondary"],
div[data-testid="stHorizontalBlock"] button {
  background: linear-gradient(165deg, #1c2420 0%, #151a17 100%) !important;
  border: 1px solid rgba(196, 165, 116, 0.28) !important;
  border-radius: 10px !important;
  color: #e8e4db !important;
  text-align: left !important;
  padding: 0.85rem 1rem !important;
  height: auto !important;
  min-height: 4.5rem !important;
  white-space: normal !important;
  line-height: 1.35 !important;
  font-weight: 500 !important;
  box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
div[data-testid="stHorizontalBlock"] button:hover {
  border-color: rgba(196, 165, 116, 0.65) !important;
  transform: translateY(-1px);
}
div[data-testid="stHorizontalBlock"] button p {
  text-align: left !important;
  white-space: normal !important;
}

.ring-tag {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0e1110;
  background: #c4a574;
  padding: 0.12rem 0.45rem;
  border-radius: 4px;
  margin-bottom: 0.35rem;
}

/* Chat bubbles area breathing room */
[data-testid="stChatMessage"] {
  background: rgba(28, 36, 32, 0.55);
  border: 1px solid rgba(196, 165, 116, 0.12);
  border-radius: 12px;
  padding: 0.35rem 0.5rem;
  margin-bottom: 0.65rem;
}

/* Chat input */
[data-testid="stChatInput"] {
  max-width: 720px;
  margin: 0 auto;
}
[data-testid="stChatInput"] textarea {
  border-radius: 12px !important;
}

/* Sidebar polish */
section[data-testid="stSidebar"] {
  background: #0c100e !important;
  border-right: 1px solid rgba(196, 165, 116, 0.15);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-family: 'Fraunces', Georgia, serif !important;
}

.sidebar-meta {
  font-size: 0.8rem;
  color: #9aa59c;
  line-height: 1.6;
}
.sidebar-meta code {
  color: #d4c4a8;
  background: rgba(196, 165, 116, 0.12);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

/* Hide Streamlit chrome a bit */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
"""

st.set_page_config(
    page_title="Investigator Chat",
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Crime lab")
    provider = os.getenv("LLM_PROVIDER", "(not set)")
    st.markdown(
        f'<div class="sidebar-meta">'
        f'LLM <code>{provider}</code><br/>'
        f'Neo4j <code>{os.getenv("NEO4J_URI", "(not set)")}</code>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    graph_nodes = None
    try:
        driver = get_driver()
        driver.verify_connectivity()
        graph_nodes = node_count(driver)
        driver.close()
        st.success(f"Connected · {graph_nodes} nodes")
    except Exception as exc:
        st.error(f"Neo4j not ready: {exc}")

    if graph_nodes == 0:
        st.warning("Graph empty — run Phase 3 (`02_graph.py`) first.")

    st.divider()
    st.markdown(
        """
**Workshop path**
1. Extract → `01_extract.py`
2. Graph → `02_graph.py`
3. Queries → `03_query.py`
4. **Bonus** → this chat
"""
    )
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Session state ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="inv-hero">
  <div class="inv-kicker">Bonus · Fraud graph</div>
  <h1>Investigator Chat</h1>
  <p class="inv-sub">
    Ask the graph in plain English. We translate to Cypher, query Neo4j,
    and brief you like a case officer — the same rings you proved by hand in Phase 4.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Case file cards ───────────────────────────────────────────────────────────

st.markdown('<p class="case-label">Case file</p>', unsafe_allow_html=True)

for row_start in range(0, len(CASE_FILE), 2):
    c1, c2 = st.columns(2, gap="medium")
    for col, item in zip((c1, c2), CASE_FILE[row_start : row_start + 2]):
        with col:
            # Button label: ring tag + short title (keeps cards compact)
            btn_label = f"{item['ring']}  ·  {item['label']}"
            if st.button(
                btn_label,
                key=f"tpl_{row_start}_{item['label']}",
                use_container_width=True,
                help=item["question"],
            ):
                st.session_state.pending_question = item["question"]

st.caption("Hover a card for the full question. Click to run the investigation.")

st.markdown("")  # spacer before chat

# ── Chat history ──────────────────────────────────────────────────────────────

if not st.session_state.messages:
    st.info(
        "No messages yet — pick a case-file lead above, or type your own question below."
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("cypher"):
            with st.expander("Cypher used"):
                st.code(msg["cypher"], language="cypher")
        if msg.get("rows") is not None:
            with st.expander(f"Results ({len(msg['rows'])} row(s))"):
                if msg["rows"]:
                    st.dataframe(msg["rows"], use_container_width=True, hide_index=True)
                else:
                    st.write("No rows returned.")

# ── Input ─────────────────────────────────────────────────────────────────────

prompt = st.chat_input("Ask the graph… e.g. Who shares the same witness?")
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("NL → Cypher → Neo4j…"):
            result = ask(prompt)
        st.markdown(result["answer"])
        if result.get("cypher"):
            with st.expander("Cypher used", expanded=True):
                st.code(result["cypher"], language="cypher")
        rows = result.get("rows") or []
        with st.expander(f"Results ({len(rows)} row(s))"):
            if rows:
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.write("No rows returned.")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "cypher": result.get("cypher", ""),
            "rows": result.get("rows", []),
        }
    )
