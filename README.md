# AssessNex AI

AssessNex AI is an assessment-generation platform with a FastAPI backend and React frontend. The active AI provider is **Google Gemini** through a single LLM gateway.

## Current architecture

```text
React (Vite)
    |
    v
FastAPI /api/v1
    |
    +--> QuestionGenerationAgent
    +--> AssignmentGenerationAgent
    +--> QuestionPaperAgent
    +--> Document services
    |
    v
LLMClient
    |
    v
Google Gemini
```

Legacy providers (Azure OpenAI, OpenAI-compatible Grok, and Groq) are no longer part of the active runtime path. Their configuration flags remain so a future migration can be deliberate instead of requiring another rewrite.

## Requirements

- Python 3.11.x (the repository is pinned to 3.11.9)
- Node.js 18+ / npm
- A Google Gemini API key

## Backend setup

```bash
cd ANAI_platform
python -m venv venv

# Windows
venv\\Scripts\\activate

# macOS/Linux
# source venv/bin/activate

python -m pip install -r backend/requirements.txt
```

Copy `ANAI_platform/backend/.env.example` to `ANAI_platform/backend/.env` and set:

```env
GOOGLE_API_KEY=your_key_here
GOOGLE_MODEL=gemini-2.5-flash
LLM_PROVIDER=google
ENABLE_PROVIDER_GEMINI=true
```

Run the API:

```bash
cd ANAI_platform
python -m uvicorn backend.app.main:app --reload --port 8000
```

API docs: `http://127.0.0.1:8000/docs`

## Frontend setup

```bash
cd ANAI_reactapp
npm install
npm run dev
```

Set `VITE_API_BASE_URL` if the backend is not using the default API location. The frontend service layer is designed to use the configured API base URL.

## One-command development launcher

From `ANAI_platform`:

```bash
python smart_launcher.py
```

This starts the **FastAPI + React** stack. It does not start the legacy Streamlit application.

## Feature flags

The backend uses explicit flags for optional or disabled functionality:

| Flag | Default | Purpose |
|---|---:|---|
| `ENABLE_PROVIDER_GEMINI` | `true` | Active Gemini provider |
| `ENABLE_PROVIDER_OPENAI` | `false` | Reserved legacy provider |
| `ENABLE_PROVIDER_GROK` | `false` | Reserved legacy provider |
| `ENABLE_PROVIDER_GROQ` | `false` | Reserved legacy provider |
| `ENABLE_ASSIGNMENT_GENERATION` | `true` | Assignment generation |
| `ENABLE_QUESTION_PAPER_GENERATION` | `true` | Paper generation |
| `ENABLE_DOCUMENT_RAG` | `false` | Dormant RAG subsystem |
| `ENABLE_PLAGIARISM_CHECK` | `false` | Dormant plagiarism subsystem |
| `ENABLE_IMAGE_QUESTIONS` | `false` | Image-question feature |
| `ENABLE_LEGACY_STREAMLIT_FRONTEND` | `false` | Old Streamlit UI |

Disabled features return a clear `503` response instead of silently falling back to mock data or another AI provider.

## Dependency policy

`ANAI_platform/backend/requirements.txt` is the canonical backend runtime dependency file. The root platform requirements file includes it and only adds development tooling.

The legacy Streamlit dependencies live separately in `ANAI_platform/requirements-legacy.txt` and are intentionally not installed by the normal backend setup.

## Project cleanup

The cleanup removed generated Python caches, committed runtime logs, generated frontend `dist` output, duplicate CRA entry points/tests, duplicate dependency declarations, direct Azure/OpenAI/Groq initialization from active agents, and the old LangGraph monkey-patch.

The active application now has one LLM entry point: `backend.app.llm_client.get_llm_client()`.
