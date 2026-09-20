@echo off
echo Starting EcoTrace-AI...

echo Starting FastAPI Backend...
start cmd /k "uvicorn main:app --port 8000"

echo Starting Streamlit Dashboard...
start cmd /k "streamlit run app.py"

echo Both services have been started in separate windows!
pause
