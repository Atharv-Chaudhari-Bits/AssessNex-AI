frontend: cd ANAI_platform && API_BASE_URL=http://127.0.0.1:${BACKEND_PORT:-8000} streamlit run frontend/app.py --server.address 0.0.0.0 --server.port ${PORT} --server.headless true
backend: cd ANAI_platform && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port ${BACKEND_PORT:-8000}
