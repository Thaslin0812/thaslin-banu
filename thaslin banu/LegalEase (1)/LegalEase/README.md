# LegalEase - AI Legal Document Generator

## Setup
```
python -m venv venv
venv\Scripts\activate        # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env         # then put your GEMINI_API_KEY in .env
```

## Run
- Both at once: `./run.sh` (Linux/Mac) or `run.bat` (Windows)
- Or separately:
  - `uvicorn legalEaseAPI.main:app --reload`
  - `streamlit run frontend/app.py`

Open http://localhost:8501. Without an API key the backend returns an offline template,
so you can test the UI and the TXT/DOCX/PDF exports immediately.

Put your own logos in `Image/Logo.png` (light background) and `Image/inverseLogo.png` (dark UI);
placeholders are auto-generated if missing.
