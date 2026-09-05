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


## Render deployment

AssessNex uses **one Render Web Service** with **Honcho** managing both processes.

```text
Honcho
├── frontend -> Streamlit -> 0.0.0.0:$PORT   (public)
└── backend  -> FastAPI   -> 127.0.0.1:8000  (private)
```

Render must expose the Streamlit process because Render supplies `$PORT` to the public process. FastAPI deliberately binds to `127.0.0.1` so Render cannot accidentally detect or route public traffic to the backend.

Build command:

```bash
pip install -r ANAI_platform/requirements.txt
```

Start command:

```bash
honcho start
```

Do not create separate Render services for the frontend/backend.

The Streamlit frontend calls FastAPI internally at:

```text
http://127.0.0.1:8000
```

No `.env` file is required on Render. Put Gemini and application environment variables in Render's Environment settings.

## Recent UX upgrades

- **Question papers now include an answer key and marking scheme** for instructor use.
- **Paper generation now reports progress** (blueprint → Gemini generation → validation → answer key → finalization) instead of appearing idle.
- **Math rendering is more robust** with normalized LaTeX delimiters and safer handling of escaped commands.
- **Educational graphs can be generated end-to-end**: Gemini emits a small structured graph specification and the backend renders a clean PNG locally, avoiding a separate image API and keeping results deterministic.

## Production feature controls

The production behavior is intentionally environment-driven. You can change the Gemini model and assessment features in Render without editing code:

```text
GOOGLE_MODEL=gemini-2.5-flash
GOOGLE_FALLBACK_MODEL=
ENABLE_QUALITY_CHECK=true
ENABLE_MATH_VALIDATION=true
ENABLE_VISUAL_GENERATION=true
ENABLE_PAPER_EXPORTS=true
ENABLE_QUESTION_BANK=true
ENABLE_MULTI_VERSION_PAPERS=true
PAPER_QUALITY_THRESHOLD=85
PAPER_MAX_VERSIONS=4
PAPER_JOB_TTL_SECONDS=3600
PAPER_POLL_INTERVAL_SECONDS=1.0
QUESTION_BANK_DB_PATH=data/question_bank.sqlite3
VISUAL_RENDER_DPI=150
VISUAL_MAX_POINTS=1000
```

### Assessment workflow

Question-paper generation now supports real progress updates, answer keys, marking schemes, a paper blueprint, deterministic quality checks, math sanity checks, reproducible graph rendering, professional PDF/DOCX export, multi-version paper generation, and a SQLite-backed question bank. The Gemini model remains configurable through `GOOGLE_MODEL`; an optional `GOOGLE_FALLBACK_MODEL` is used only if the primary model fails.

## Evaluation

After generating a paper, use the **Evaluate Paper** tab to enter student answers and grade the paper. Objective questions are checked deterministically; subjective questions are evaluated in a single Gemini rubric request and are capped at the configured maximum marks. Evaluation reports can be exported to PDF.

### Production environment variables

```text
ENABLE_EVALUATION=true
ENABLE_EVALUATION_GEMINI=true
EVALUATION_PASS_PERCENT=40
```

The paper generator now forwards the visible UI configuration instead of silently replacing it with backend defaults.
