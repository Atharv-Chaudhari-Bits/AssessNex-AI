# AssessNex AI - Complete Stack Procfile
# Manages all three services: Backend, Streamlit Frontend, and React App
# Run with: honcho start

backend: cd ANAI_platform && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
frontend: cd ANAI_platform && python frontend_wrapper.py
# reactapp: cd ANAI_reactapp && npm run dev
