# Kannada Lens: Kannada Text Digitization

Kannada Digital Innovation Hackathon 2026 | Problem Statement 5 | Individual entry by Vemula Guru Prasad (Seshadri Rao Gudlavalleru Engineering College)

## Problem
Kannada text on signboards, scanned pages and handwritten notes is locked inside images. It cannot be copied or searched, and non-Kannada readers cannot understand it.

## Solution
Upload or capture an image or PDF. Kannada Lens extracts the Kannada text and returns:
- Digital Kannada text (copy or download as .txt)
- Roman transliteration (how to read it)
- English translation and a simple explanation
- Keywords, document type and a confidence level
- A searchable library across Kannada, Roman and English, with JSON export

## Tech stack
Python, Streamlit, Google Gemini vision model (google-genai SDK).

## Run locally
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
streamlit run app.py
```
Free key: https://aistudio.google.com/apikey. You can also paste the key in the app sidebar.

## Deploy
Streamlit Community Cloud: choose this repo and app.py, then add GEMINI_API_KEY under Settings > Secrets.

## Limitations
- Very messy handwriting or damaged scans can reduce accuracy; the app shows a confidence level and notes.
- The library is session-based; use the JSON export to keep results.

## Future work
Offline OCR fallback, text-to-speech, batch PDF processing with a database, handwriting tuning, Old Kannada (Halegannada) support.
