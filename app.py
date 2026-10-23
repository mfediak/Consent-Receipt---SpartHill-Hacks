"""ConsentReceipt: paste a privacy policy, get a source-linked disclosure receipt.

Run with:  streamlit run app.py
"""

import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src import render
from src.analyzer import DEFAULT_MODEL, AnalysisError, analyze_policy, resolve_api_key
from src.receipt import build_receipt, receipt_to_json, receipt_to_text
from src.verification import normalize_policy, split_paragraphs, verify_disclosures

load_dotenv()

MAX_CHARS = 40_000  # input cap: keeps cost and latency predictable
MIN_CHARS = 80
SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES = [
    ("Ad-supported app", "sample_policy.txt", "Example Company"),
    ("“We do not sell” wording", "sample_negation.txt", "Snapfolio"),
    ("Policy that says little", "sample_sparse.txt", "QuickNotes"),
]

st.set_page_config(page_title="ConsentReceipt", page_icon="🧾", layout="wide")
st.markdown(f"<style>{render.CSS}</style>", unsafe_allow_html=True)


# --- callbacks ---------------------------------------------------------------

def load_sample(filename: str, company: str) -> None:
    st.session_state["policy_text"] = (SAMPLES_DIR / filename).read_text(encoding="utf-8")
    st.session_state["company_name"] = company
    st.session_state["policy_source"] = "Sample policy included with ConsentReceipt"


def clear_result() -> None:
    st.session_state["result"] = None


# --- sidebar -----------------------------------------------------------------

def render_sidebar() -> tuple[str | None, str]:
    with st.sidebar:
        st.markdown("**Gemini settings**")
        env_key = resolve_api_key()
        if env_key:
            st.caption("Using the Gemini API key from your environment.")
            api_key = env_key
        else:
            api_key = st.text_input(
                "Gemini API key",
                type="password",
                key="api_key_input",
                help="Kept only in this browser session. Create one in Google AI Studio.",
            )
        model = st.text_input(
            "Model",
            value=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            key="model_name",
            help="Google retires model names regularly. Change this if the default stops working.",
        )

        st.markdown("**How a receipt is made**")
        st.markdown(
            "1. You paste the policy.\n"
            "2. The text is cleaned and split into labeled paragraphs.\n"
            "3. Gemini extracts five disclosures and a quote for each.\n"
            "4. Every quote is searched for in your policy.\n"
            "5. Each finding is marked disclosed, unclear, not found, or verification failed.\n"
            "6. You download the receipt."
        )
        st.markdown("**What it can’t do**")
        st.caption(
            "A found quote proves the words are in the policy, not that the summary reads "
            "them correctly. The receipt is not legal advice and does not record consent."
        )
    return api_key or None, (model or DEFAULT_MODEL).strip()


# --- input -------------------------------------------------------------------

def run_analysis(api_key: str | None, model: str) -> None:
    text = normalize_policy(st.session_state.get("policy_text", ""))
    if not text:
        st.warning("Paste a privacy policy first, or load one of the samples above.")
        return
    if len(text) < MIN_CHARS:
        st.warning("That is too short to be a privacy policy. Paste the full text.")
        return
    if len(text) > MAX_CHARS:
        st.error(
            f"This policy is {len(text):,} characters and the limit is {MAX_CHARS:,}. "
            "Paste the sections on data collection, use, sharing, your rights, and retention."
        )
        return
    if not api_key:
        st.error("Add a Gemini API key in the sidebar, or set GEMINI_API_KEY in your .env file.")
        return

    started = time.perf_counter()
    try:
        with st.spinner("Reading the policy and finding the exact words behind each finding…"):
            raw = analyze_policy(text, api_key=api_key, model=model)
    except AnalysisError as exc:
        st.error(str(exc))
        return
    elapsed = time.perf_counter() - started

    findings = verify_disclosures(text, raw)
    receipt = build_receipt(
        company=st.session_state.get("company_name", ""),
        source=st.session_state.get("policy_source", ""),
        policy_text=text,
        findings=findings,
        model=model,
        elapsed_seconds=elapsed,
    )
    st.session_state["result"] = {
        "findings": findings,
        "receipt": receipt,
        "policy_text": text,
        "paragraphs": split_paragraphs(text),
    }
    st.rerun()


def render_input(api_key: str | None, model: str) -> None:
    st.markdown(render.hero_html(), unsafe_allow_html=True)
    st.markdown(
        render.section_title_html(
            "Paste the privacy policy",
            "Paste the text, or start from a sample to see how a receipt reads.",
        ),
        unsafe_allow_html=True,
    )

    columns = st.columns(len(SAMPLES))
    for column, (label, filename, company) in zip(columns, SAMPLES):
        column.button(
            label,
            key=f"sample_{filename}",
            on_click=load_sample,
            args=(filename, company),
        )

    st.text_area(
        "Privacy policy text",
        key="policy_text",
        height=300,
        placeholder="Paste the full privacy policy here.",
        label_visibility="collapsed",
    )
    length = len(st.session_state.get("policy_text", ""))
    st.caption(f"{length:,} of {MAX_CHARS:,} characters")

    left, right = st.columns(2)
    left.text_input("Company or product (optional)", key="company_name")
    right.text_input("Where the policy came from (optional)", key="policy_source",
                     placeholder="A link or a note")

    st.caption(
        "Your text is sent to Google’s Gemini API for analysis. This app does not save it or "
        "write it to logs. Only paste text you are comfortable sending to an outside AI provider."
    )
    if st.button("Analyze policy", type="primary"):
        run_analysis(api_key, model)


# --- results -----------------------------------------------------------------

def render_results(result: dict) -> None:
    receipt, findings = result["receipt"], result["findings"]
    st.button("Edit the policy or start over", on_click=clear_result)

    tab_receipt, tab_source, tab_export = st.tabs(["Receipt", "Source policy", "Export"])

    with tab_receipt:
        st.markdown(render.sheet_html(receipt, findings), unsafe_allow_html=True)

    with tab_source:
        st.markdown(
            render.section_title_html(
                "The policy, with your quotes marked",
                "Highlighted passages are the quotes that were found. The numbers match the numbered "
                "findings in the receipt. Paragraph labels match the receipt’s source locations.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(render.legend_html(findings), unsafe_allow_html=True)
        st.markdown(
            render.policy_html(result["policy_text"], result["paragraphs"], findings),
            unsafe_allow_html=True,
        )

    with tab_export:
        st.markdown(
            render.section_title_html(
                "Keep a copy",
                "The receipt stores a fingerprint of the policy, not the policy itself. "
                "You can use the fingerprint later to check you are looking at the same text.",
            ),
            unsafe_allow_html=True,
        )
        stem = f"consent_receipt_{receipt['policy_sha256'][:8]}"
        json_col, text_col = st.columns(2)
        json_col.download_button(
            "Download JSON receipt",
            data=receipt_to_json(receipt),
            file_name=f"{stem}.json",
            mime="application/json",
        )
        text_col.download_button(
            "Download text receipt",
            data=receipt_to_text(receipt),
            file_name=f"{stem}.txt",
            mime="text/plain",
        )
        with st.expander("Preview the JSON"):
            st.code(receipt_to_json(receipt), language="json")


# --- main --------------------------------------------------------------------

def main() -> None:
    # Streamlit drops a widget's value when the widget is not drawn. The results view
    # hides the input fields, so re-assign them to keep the text for "Edit the policy".
    for key in ("policy_text", "company_name", "policy_source"):
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]

    api_key, model = render_sidebar()
    result = st.session_state.get("result")
    if result:
        st.markdown(render.topbar_html(), unsafe_allow_html=True)
        render_results(result)
    else:
        render_input(api_key, model)  # the hero carries the logotype


main()
