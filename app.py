import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import streamlit as st

import config
from ai_core.generator import (
    ensure_logo, format_docx, format_html_preview, format_pdf, sanitize_text,
)

st.set_page_config(page_title="LegalEase", layout="centered")

ss = st.session_state
ss.setdefault("generated_text", "")
ss.setdefault("show_edit", False)
ss.setdefault("meta", {})

# Header
_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.image(ensure_logo(config.WEB_LOGO_PATH, dark=True), width=260)
st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# Inputs
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if st.button("Generate Document"):
    if not all(v.strip() for v in (document_type, parties, terms, dates)):
        st.warning("Please fill in all fields.")
    else:
        with st.spinner("Generating document..."):
            try:
                resp = requests.post(
                    config.API_URL,
                    json={"document_type": document_type, "parties": parties,
                          "terms": terms, "dates": dates},
                    timeout=120,
                )
                resp.raise_for_status()
                ss.generated_text = sanitize_text(resp.json()["document"])
                ss.editor_text = ss.generated_text
                ss.meta = {"document_type": document_type, "terms": terms}
                ss.show_edit = False
                st.success("Document Generated Successfully!")
            except requests.RequestException as exc:
                st.error(f"Could not reach the backend at {config.API_URL}: {exc}")
elif not ss.generated_text:
    st.info("Click 'Generate Document' to start")

if ss.generated_text:
    doc_type = ss.meta.get("document_type", "Legal Document")
    doc_terms = ss.meta.get("terms", "")

    styled_html = format_html_preview(ss.generated_text)
    st.markdown(
        "<div style='background:#0e1525;color:#e6e6e6;padding:16px 20px;border-radius:8px;"
        f"max-height:400px;overflow-y:auto;'>{styled_html}</div>",
        unsafe_allow_html=True,
    )

    if st.button("Click to Edit Document"):
        ss.show_edit = not ss.show_edit

    if ss.show_edit:
        st.text_area("Edit Document Below:", key="editor_text", height=300)
        ss.generated_text = ss.editor_text

    fname = doc_type.replace(" ", "_").lower()
    st.download_button("Download as .TXT", data=ss.generated_text,
                       file_name=f"{fname}.txt", mime="text/plain")
    st.download_button("Download as .DOCX", data=format_docx(ss.generated_text, doc_type, doc_terms),
                       file_name=f"{fname}.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.download_button("Download as .PDF", data=format_pdf(ss.generated_text, doc_type, doc_terms),
                       file_name=f"{fname}.pdf", mime="application/pdf")

st.caption("AI-generated documents are drafts, not legal advice. Have a qualified lawyer review before signing.")
