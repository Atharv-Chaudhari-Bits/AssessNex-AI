# AssessNex AI – Production Pass: Configuration Fidelity + Evaluation

## Fixed
- Paper Generator now sends the UI's difficulty distribution, per-section difficulty, marks-per-question, Bloom distribution, and validation flags to the backend.
- Paper generation now validates that question counts, section marks, and Bloom percentages match the UI before calling Gemini.
- `mixed` section difficulty uses the global difficulty target as its backend selection signal.
- Bloom level selection now considers the requested Bloom distribution rather than only question position.

## Added: Evaluation
- `POST /api/v1/evaluation/evaluate` evaluates a generated paper against student answers.
- MCQ, True/False, and fill-in-the-blank answers are graded deterministically.
- Subjective/code/numerical answers can be evaluated in one Gemini rubric pass.
- Partial marks are capped at the question's maximum marks.
- Each result includes score, feedback, strengths, and missing points when available.
- `POST /api/v1/evaluation/export-pdf` exports a teacher-facing evaluation report.
- Streamlit now includes an **Evaluate Paper** tab using the generated paper's answer key.

## Environment controls
- `ENABLE_EVALUATION=true`
- `ENABLE_EVALUATION_GEMINI=true`
- `EVALUATION_PASS_PERCENT=40`

These are environment variables so production behavior can be changed in Render without code edits.
