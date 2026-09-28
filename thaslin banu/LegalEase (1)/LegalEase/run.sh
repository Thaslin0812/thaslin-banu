#!/usr/bin/env bash
# Starts the FastAPI backend (port 8000) and Streamlit frontend (port 8501)
cd "$(dirname "$0")"
uvicorn legalEaseAPI.main:app --port 8000 &
API_PID=$!
trap "kill $API_PID" EXIT
streamlit run frontend/app.py
