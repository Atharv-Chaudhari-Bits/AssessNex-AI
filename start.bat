@echo off
cd /d "%~dp0ANAI_platform"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
