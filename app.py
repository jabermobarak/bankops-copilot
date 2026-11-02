"""Browser UI. Start the API first, or use scripts/run.py for both processes."""

import json
import os
from datetime import date

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="BankOps · Treasury Copilot", page_icon="🏦", layout="wide")
st.markdown(
    """<style>
 .stApp { background: #0b1120; }
 [data-testid="stMetric"] { background: #141e31; border: 1px solid #24334a;
 border-radius: 12px; padding: 18px; }
 .eyebrow { color: #4dd7b0; letter-spacing: .18em; font-size: 12px; }
 .muted { color: #94a3b8; }
 </style>""",
    unsafe_allow_html=True,
)
API = os.getenv("BANKOPS_API_URL", "http://127.0.0.1:8000").rstrip("/")
headers = {"X-API-Key": os.getenv("BANKOPS_API_KEY", "")}


def call(path, payload=None):
    with httpx.Client(timeout=45, trust_env=False) as client:
        res = (
            client.post(API + path, json=payload, headers=headers)
            if payload is not None
            else client.get(API + path, headers=headers)
        )
        res.raise_for_status()
        return res.json()


with st.sidebar:
    st.markdown("## ◈ BankOps")
    st.caption("TREASURY ANALYSIS WORKSPACE")
    as_of = st.date_input(
        "Snapshot date",
        value=date(2026, 10, 30),
        min_value=date(2026, 10, 1),
        max_value=date(2026, 10, 30),
    )
    horizon = st.slider("Schedule horizon · days", 1, 30, 7)
    language = st.selectbox("Answer language", ["en", "ru"])
    st.divider()
    st.caption("Synthetic RUB data · Read-only tools")
    st.caption("Independent portfolio project by Jaber Mobarak. No affiliation with Sber.")
    try:
        cfg = call("/v1/config")
        st.success("API connected")
        st.caption(f"Provider: {cfg['provider']} · Retrieval: {cfg['retriever']}")
    except (httpx.HTTPError, ValueError):
        st.error("API unavailable. Run: python scripts/run.py")
        st.stop()

st.markdown('<div class="eyebrow">BANKOPS / INTELLIGENCE DESK</div>', unsafe_allow_html=True)
st.title("From treasury data to a traceable answer.")
st.markdown(
    '<p class="muted">Ask about cash, stress scenarios and policy. Inspect every figure and source.</p>',
    unsafe_allow_html=True,
)
try:
    overview = call(f"/v1/overview?as_of={as_of.isoformat()}&horizon_days={horizon}")
except (httpx.HTTPError, ValueError):
    st.error("Could not load this snapshot. Check the API terminal.")
    st.stop()
values = overview["metrics"]
if not values:
    st.warning(overview["answer"])
    st.stop()
cols = st.columns(4)
cols[0].metric("OPENING CASH", f"₽{values['opening_cash_rub'] / 1e6:.1f}m")
cols[1].metric("MINIMUM SCHEDULED CASH", f"₽{values['minimum_cash_rub'] / 1e6:.1f}m")
cols[2].metric("REQUIRED BUFFER", f"₽{values['buffer_rub'] / 1e6:.1f}m")
cols[3].metric("BASELINE STATUS", "REVIEW" if values["breached"] else "WITHIN BUFFER")
st.caption("Scheduled cashflow projection, not an ML forecast. All amounts are fictional.")
left, right = st.columns([1.5, 1])
with left:
    st.subheader("Scheduled liquidity")
    frame = pd.DataFrame(overview["rows"]).set_index("date")
    chart = frame[["closing_cash_rub"]].copy()
    chart["policy_buffer_rub"] = values["buffer_rub"]
    st.line_chart(chart, color=["#4dd7b0", "#fb7185"])
with right:
    st.subheader("Start an investigation")
    st.caption("Snapshot date and horizon controls apply to every question.")
    for label, prompt in [
        ("01 · Run a 20% outflow stress", "What if outflows increase by 20%?"),
        ("02 · Check counterparty concentration", "Show counterparty exposure concentration"),
        ("03 · Inspect the liquidity policy", "What is the liquidity buffer policy?"),
    ]:
        if st.button(label, use_container_width=True):
            st.session_state["pending"] = prompt

question = st.chat_input("Ask: What if outflows increase by 20%?")
question = question or st.session_state.pop("pending", None)
if question:
    with st.spinner("Checking data and policy evidence…"):
        try:
            result = call(
                "/v1/ask",
                {
                    "question": question,
                    "as_of": as_of.isoformat(),
                    "horizon_days": horizon,
                    "language": language,
                },
            )
            st.session_state["result"] = result
            st.session_state["question"] = question
        except (httpx.HTTPError, ValueError):
            st.error("Analysis failed. Check the API terminal and retry.")
if "result" in st.session_state:
    r = st.session_state["result"]
    st.divider()
    st.subheader(st.session_state["question"])
    st.caption(f"{r['status']} · {r['task']} · {r['elapsed_ms']:.0f} ms · {r['request_id']}")
    st.write(r["answer"])
    if r.get("narrative"):
        st.info(r["narrative"])
        st.caption(
            "LLM explanation · citations and numeral tokens checked; meaning is not independently verified."
        )
    for warning in r["warnings"]:
        st.warning(warning)
    tables, evidence, trace = st.tabs(["Figures", "Policy evidence", "Execution trace"])
    with tables:
        st.json(r["metrics"])
        if r["rows"]:
            st.dataframe(r["rows"], use_container_width=True)
    with evidence:
        for s in r["sources"]:
            with st.expander(f"[{s['id']}] {s['title']}"):
                st.caption(f"Effective: {s['effective_from']} → {s['effective_to'] or 'open'}")
                st.write(s["text"])
    with trace:
        st.json(r["trace"])
    st.download_button(
        "Download analysis JSON",
        data=json.dumps(r, indent=2),
        file_name="bankops-analysis.json",
        mime="application/json",
    )
