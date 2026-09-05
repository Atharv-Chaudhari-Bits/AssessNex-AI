# AssessNex AI cleanup — 2.0.0

## LLM migration

- Gemini is now the only active provider.
- OpenAI, Grok and Groq execution paths are disabled by default and are not imported by the active runtime.
- Added explicit provider flags to backend settings.
- Centralized model construction in `backend.app.llm_client.get_llm_client()`.
- Removed the old Azure/OpenAI initialization from the question-paper agent.
- Removed fake token accounting and made JSON responses fail validation instead of being mislabeled as valid JSON.
- Added bounded retry behavior for transient model/API failures.

## Backend cleanup

- Removed the LangGraph import monkey-patch.
- Updated LangGraph/LangChain Core/Gemini integration to the current compatible major-generation line.
- Migrated PDF parsing from the obsolete `PyPDF2` dependency to `pypdf`.
- Updated `python-docx` and Pydantic dependencies.
- Fixed a misspelled difficulty-level setting reference.
- Fixed the customized-document endpoint so it parses documents directly instead of calling the same API over HTTP and referencing a nonexistent `API_BASE_URL` setting.
- Disabled plagiarism checking and RAG by default through feature flags.
- Assignment and question-paper generation now return an explicit disabled response when their feature flags are off.
- Removed silent mock assignment generation on LLM failures.
- Reduced the active agent package to the agents used by the API.
- Removed unused legacy agent/formatting/RAG modules from the active codebase.

## Frontend cleanup

- Removed Create React App leftovers (`App.js`, `index.js`, test setup, web-vitals).
- Removed unused frontend dependencies.
- Replaced the abandoned `react-beautiful-dnd` package with maintained `@hello-pangea/dnd`.
- Fixed the API service's duplicate `questions` object, which previously caused earlier methods to be overwritten.
- Removed fake API fallbacks for generation/document operations.
- Added an explicit `VITE_ENABLE_MOCK_AUTH` flag for the still-unimplemented backend authentication endpoints.
- Corrected the frontend API default to the FastAPI `/api/v1` base path.

## Runtime / documentation

- Normal startup is now FastAPI + Vite React; legacy Streamlit is opt-in.
- Added backend and frontend `.env.example` files.
- Added a canonical dependency layout and separated legacy Streamlit dependencies.
- Removed generated caches, logs and frontend build artifacts from the deliverable.
- Rewrote the root and frontend setup documentation.


## Deployment hotfix — September 2026

- Fixed LangGraph/LangChain Core incompatibility by pinning `langchain-core==1.6.1` with `langgraph==1.2.11` and `langchain-google-genai==4.4.0`.
- Removed the broken LangGraph import compatibility shim.
- Replaced the Render Procfile process type with `web` and bind to Render's `$PORT`.
- Removed the nested Procfile so Render cannot accidentally launch the wrong process definition.
- Added `render.yaml` for separate FastAPI and Vite deployments.
- React now consistently supports `VITE_API_BASE_URL` (with `VITE_API_BASE` retained as a fallback).
- Render is explicitly configured to use FastAPI + React; legacy Streamlit is not part of the normal deployment.

## 2026-09-05 — Render/dependency correction

- Corrected `langchain-core` to `1.6.1`; `langchain-google-genai 4.4.0` requires Core >=1.6.1.
- Kept LangGraph on the compatible 1.2.11 line.
- Removed the remaining stale `react-beautiful-dnd` import.
- Changed Render's React build from `npm ci` to `npm install` because the repository intentionally does not ship a lockfile yet.
- Changed Vite production base to `/` for Render static hosting rather than a GitHub Pages subpath.

## 2026-09-05 — Paper/Math/Visual UX upgrade

- Added a teacher-facing answer key and marking scheme to generated question papers.
- Added a separate answer-key section in the Streamlit paper view and included it in text export.
- Added background paper-generation jobs with real LangGraph node progress reporting so users see what the system is doing while Gemini is working.
- Added deterministic server-side graph rendering for LLM-specified function, line, and scatter graphs.
- Preserved rendered visuals through the question schema and displayed them in both question and paper views.
- Tightened LaTeX normalization, including `\\(...\\)`, `\\[...\\]`, and common escaped-command corruption.
- Added explicit Gemini prompt rules for valid LaTeX and structured visual specifications.
