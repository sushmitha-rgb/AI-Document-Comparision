import asyncio
import sys
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import google.generativeai as genai
# ... rest of your codefrom pypdf import PdfReader
from dotenv import load_dotenv
import google.generativeai as genai
from docx import Document
from io import BytesIO

st.sidebar.title("🔑 Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")if not api_key:
    st.sidebar.warning("Paste your Gemini API key here to compare")
    st.stop()
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.8-flash")

st.set_page_config(page_title="AI Document Comparison Assistant", layout="wide")
st.title("📄 AI Document Comparison Assistant")
st.write("Upload two PDF documents to compare summaries, similarities, differences and key details.")

def extract_text(file):
    reader = PdfReader(io.BytesIO(file.read()))
    text = ""
    for i, page in enumerate(reader.pages, start=1):
        t = page.extract_text() or ""
        text += f"\n--- Page {i} ---\n{t}"
    return text.strip()

col1, col2 = st.columns(2)
with col1:
    file_a = st.file_uploader("Document A", type=["pdf"], key="a")
with col2:
    file_b = st.file_uploader("Document B", type=["pdf"], key="b")

if st.button("Compare Documents"):
    if not file_a or not file_b:
        st.error("Please upload both Document A and Document B.")
        st.stop()
    with st.spinner("Comparing..."):
        text_a = extract_text(file_a)
        text_b = extract_text(file_b)
        if not text_a or not text_b:
            st.error("No readable text found. Use text-based PDF, not scanned image.")
            st.stop()
        st.info(f"Doc A: {len(text_a)} chars | Doc B: {len(text_b)} chars")
        prompt = f"""Use ONLY the text below. Do NOT invent details. If missing, write 'Not found in the provided text'. Return ONLY valid JSON with keys: summary_a, summary_b, similarities, differences, key_details, conclusion, limitations. Key details should be list of objects with field, document_a, document_b.
        DOCUMENT A: {text_a[:15000]}
        DOCUMENT B: {text_b[:15000]}"""
        try:
            response = model.generate_content(prompt)
            raw = re.sub(r"^```json|```$", "", response.text.strip(), flags=re.MULTILINE).strip()
            r = json.loads(raw)
            st.session_state["r"] = r
            st.session_state["fa"] = file_a.name
            st.session_state["fb"] = file_b.name
            st.success("Comparison complete!")
        except Exception as e:
            st.error(f"Error: {e}. Check API Key / Internet and retry.")

if "r" in st.session_state:
    r = st.session_state["r"]
    t1,t2,t3,t4,t5,t6 = st.tabs(["Summary A","Summary B","Similarities","Differences","Key Details","Conclusion"])
    with t1: st.write(r.get("summary_a",""))
    with t2: st.write(r.get("summary_b",""))
    with t3:
        for s in r.get("similarities",[]): st.write(f"- {s}")
    with t4:
        for d in r.get("differences",[]): st.write(f"- {d}")
    with t5: st.table(r.get("key_details",[]))
    with t6:
        st.write(r.get("conclusion",""))
        st.warning(r.get("limitations",""))
    doc = Document()
    doc.add_heading("AI Document Comparison Report", 0)
    doc.add_heading(f"Document A - {st.session_state['fa']}", level=1)
    doc.add_paragraph(r.get("summary_a",""))
    doc.add_heading(f"Document B - {st.session_state['fb']}", level=1)
    doc.add_paragraph(r.get("summary_b",""))
    doc.add_heading("Similarities", level=1)
    for s in r.get("similarities",[]): doc.add_paragraph(s, style="List Bullet")
    doc.add_heading("Differences", level=1)
    for d in r.get("differences",[]): doc.add_paragraph(d, style="List Bullet")
    doc.add_heading("Conclusion", level=1)
    doc.add_paragraph(r.get("conclusion",""))
    buf = BytesIO(); doc.save(buf); buf.seek(0)
    st.download_button("📥 Download Comparison Report", data=buf, file_name="comparison_report.docx")
    if st.button("Clear and Compare Again"):
        st.session_state.clear(); st.rerun()