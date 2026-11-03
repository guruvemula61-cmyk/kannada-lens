"""Kannada Lens - Kannada Text Digitization
Image / scanned page / handwriting -> searchable digital Kannada text
+ Roman transliteration + English meaning + simple explanation.
"""
import json
import os
import re
import time
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

MODELS = [m for m in [os.getenv("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-3.7-flash"] if m]

st.set_page_config(page_title="Kannada Lens", page_icon="🔤", layout="wide")

PROMPT = """You are an expert Kannada OCR and language assistant.
Read ALL Kannada (and any English) text in the attached image/document.
Return ONLY valid JSON with exactly these keys:
{
  "document_type": "printed | handwritten | signboard | scanned page | other",
  "kannada_text": "full extracted text in Kannada script, keep line breaks as \\n",
  "transliteration": "Roman (English letters) reading of the Kannada text, line by line",
  "english_translation": "natural English translation",
  "simple_explanation": "2-3 simple sentences explaining what this text is about / where it is used",
  "keywords": ["5-10 important Kannada words from the text"],
  "confidence": "high | medium | low",
  "notes": "mention unclear/damaged parts, or empty string"
}
Do not invent text that is not visible. If no Kannada text is found, say so in notes
and leave kannada_text empty."""


def secret_key() -> str:
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:  # noqa: BLE001
        return ""


def get_client():
    key = st.session_state.get("api_key") or secret_key() or os.getenv("GEMINI_API_KEY", "")
    return genai.Client(api_key=key) if key else None


def digitize(client, data: bytes, mime: str) -> dict:
    last = None
    for model in MODELS:
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=[types.Part.from_bytes(data=data, mime_type=mime), PROMPT],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                text = re.sub(r"^```json|```$", "", (resp.text or "").strip()).strip()
                return json.loads(text)
            except Exception as e:  # noqa: BLE001
                last = e
                msg = str(e).lower()
                busy = any(w in msg for w in ("503", "429", "500", "high demand", "overloaded", "try again"))
                if busy:
                    time.sleep(2 * (attempt + 1))
                    continue
                break  # other error: try next model
    raise last


def highlight(text: str, query: str) -> str:
    if not query:
        return text
    return re.sub(f"({re.escape(query)})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)


if "docs" not in st.session_state:
    st.session_state.docs = []

with st.sidebar:
    st.title("🔤 Kannada Lens")
    st.caption("Kannada Text Digitization")
    if not secret_key() and not os.getenv("GEMINI_API_KEY"):
        st.text_input("Gemini API key", type="password", key="api_key",
                      help="Free key: aistudio.google.com/apikey")
    st.markdown("---")
    st.markdown(
        "**How it works**\n1. Upload / capture Kannada image or PDF\n"
        "2. AI reads the script\n3. Get text, reading, meaning\n"
        "4. Search across all your documents"
    )
    st.markdown("---")
    st.metric("Documents digitized", len(st.session_state.docs))

st.title("ಕನ್ನಡ Lens — Kannada Text Digitization")
st.write("Turn Kannada **signboards, scanned pages and handwritten notes** into "
         "searchable digital text, with Roman reading and English meaning.")

tab_scan, tab_search, tab_lib = st.tabs(["📷 Digitize", "🔎 Search", "📚 Library"])

with tab_scan:
    mode = st.radio("Input", ["Upload file", "Use camera"], horizontal=True)
    files = []
    if mode == "Upload file":
        up = st.file_uploader("Image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"],
                              accept_multiple_files=True)
        for f in up or []:
            mime = f.type or ("application/pdf" if f.name.endswith(".pdf") else "image/jpeg")
            files.append((f.name, f.getvalue(), mime))
    else:
        cam = st.camera_input("Take a photo")
        if cam:
            files.append(("camera.jpg", cam.getvalue(), "image/jpeg"))

    if files and st.button("✨ Digitize", type="primary"):
        client = get_client()
        if not client:
            st.error("Please add your Gemini API key in the sidebar.")
        else:
            for name, data, mime in files:
                with st.spinner(f"Reading {name} ... (may retry if the server is busy)"):
                    try:
                        result = digitize(client, data, mime)
                    except Exception as e:  # noqa: BLE001
                        st.error(f"{name}: failed ({e}). Please press Digitize again.")
                        continue
                st.session_state.docs.append({
                    "name": name,
                    "time": datetime.now().strftime("%d %b %Y %H:%M:%S"),
                    "data": data if mime.startswith("image") else None,
                    **result,
                })
            st.success("Done! Results below. They are also saved in Library & Search.")

    for doc in reversed(st.session_state.docs[-3:]):
        st.markdown(f"### 📄 {doc['name']}  ·  _{doc.get('document_type', '')}_  ·  confidence: **{doc.get('confidence', '')}**")
        c1, c2 = st.columns(2)
        if doc.get("data"):
            c1.image(doc["data"], use_container_width=True)
        with c2:
            st.markdown("**Kannada text**")
            st.text_area("kn", doc.get("kannada_text", ""), height=160,
                         key=f"kn_{doc['time']}_{doc['name']}", label_visibility="collapsed")
        t1, t2, t3 = st.tabs(["Reading (Roman)", "English", "Explanation"])
        t1.write(doc.get("transliteration", ""))
        t2.write(doc.get("english_translation", ""))
        t3.write(doc.get("simple_explanation", ""))
        if doc.get("keywords"):
            st.write("🏷️ " + " · ".join(doc["keywords"]))
        if doc.get("notes"):
            st.info(doc["notes"])
        st.download_button("⬇️ Download .txt", doc.get("kannada_text", "").encode("utf-8"),
                           file_name=f"{os.path.splitext(doc['name'])[0]}_kannada.txt",
                           key=f"dl_{doc['time']}_{doc['name']}")
        st.divider()

with tab_search:
    q = st.text_input("Search words (Kannada, Roman or English)")
    if not st.session_state.docs:
        st.info("Digitize a document first, then search here.")
    elif q:
        hits = 0
        for doc in st.session_state.docs:
            fields = {"Kannada": doc.get("kannada_text", ""),
                      "Reading": doc.get("transliteration", ""),
                      "English": doc.get("english_translation", "")}
            matched = {k: v for k, v in fields.items() if q.lower() in v.lower()}
            if matched:
                hits += 1
                st.markdown(f"**📄 {doc['name']}** ({doc['time']})")
                for k, v in matched.items():
                    for line in v.splitlines():
                        if q.lower() in line.lower():
                            st.markdown(f"- *{k}:* " + highlight(line, q), unsafe_allow_html=True)
        if not hits:
            st.warning("No matches found.")

with tab_lib:
    if not st.session_state.docs:
        st.info("Nothing here yet.")
    else:
        export = [{k: v for k, v in d.items() if k != "data"} for d in st.session_state.docs]
        st.download_button("⬇️ Export all as JSON",
                           json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name="kannada_lens_library.json")
        for doc in st.session_state.docs:
            with st.expander(f"{doc['name']} — {doc['time']}"):
                st.write(doc.get("kannada_text", ""))
                st.caption(doc.get("english_translation", ""))
