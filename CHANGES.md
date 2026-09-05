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
