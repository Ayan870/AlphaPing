@echo off
echo Starting AlphaPing Backend...
call venv\Scripts\activate
uvicorn main:app --reload --port 8000