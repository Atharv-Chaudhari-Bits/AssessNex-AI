"""Assessment evaluation endpoints.

Combines deterministic grading for objective questions with a single Gemini
rubric pass for subjective questions. The API accepts the generated paper and
student answers, so it can evaluate papers produced in the current session or
from a saved/exported paper.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.llm_client import get_llm_client
from backend.app.utils.logger import get_logger
from backend.app.utils.paper_exports import build_pdf

logger = get_logger(__name__)
router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationRequest(BaseModel):
    paper: Dict[str, Any] = Field(..., description="Generated paper including answer_key")
    answers: Dict[str, str] = Field(default_factory=dict, description="Student answers keyed by question number")
    student_name: str = "Student"


class EvaluationResult(BaseModel):
    status: str
    student_name: str
    total_marks: float
    awarded_marks: float
    percentage: float
    grade: str
    passed: bool
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _objective_match(answer: str, expected: str, options: List[str] | None = None) -> bool:
    a = _norm(answer)
    e = _norm(expected)
    if not a:
        return False
    if a == e:
        return True
    # MCQ answers may be returned as "A", "A)", or the complete option text.
    if options:
        for opt in options:
            opt_norm = _norm(opt)
            letter = opt_norm[:1] if opt_norm else ""
            if a.rstrip(").:") == letter and (e == letter or e.startswith(letter + ")")):
                return True
            if a == opt_norm and (e == opt_norm or e in opt_norm):
                return True
    # True/false and fill-in answers often differ only in punctuation.
    return re.sub(r"[^a-z0-9.+\-/]", "", a) == re.sub(r"[^a-z0-9.+\-/]", "", e)


def _flatten_questions(paper: Dict[str, Any]) -> List[Dict[str, Any]]:
    questions: List[Dict[str, Any]] = []
    for section in paper.get("sections", []) or []:
        for q in section.get("questions", []) or []:
            item = dict(q)
            item["section_title"] = section.get("title", section.get("section_id", "Section"))
            questions.append(item)
    return questions


def _answer_lookup(paper: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for section in paper.get("answer_key", []) or []:
        for entry in section.get("answers", []) or []:
            lookup[str(entry.get("question_number"))] = entry
    return lookup


def _grade_from_percentage(pct: float) -> str:
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B"
    if pct >= 60: return "C"
    if pct >= 50: return "D"
    return "F"


def _build_llm_batch(subjective: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not subjective:
        return []
    payload = []
    for item in subjective:
        payload.append({
            "question_number": str(item["question_number"]),
            "question": item["question"],
            "student_answer": item["student_answer"],
            "expected_answer": item["expected_answer"],
            "marks": item["max_marks"],
            "marking_scheme": item.get("marking_scheme", []),
        })
    prompt = f"""
You are a careful academic evaluator. Evaluate each student answer against the supplied
question, expected answer, and marking scheme. Award partial marks when justified.
Never exceed the maximum marks. Do not invent missing work. Return ONLY JSON as an array.
Each item must contain: question_number, awarded_marks, feedback, strengths, missing_points.

ITEMS:
{json.dumps(payload, ensure_ascii=False)}
"""
    raw = get_llm_client().generate_json_message(
        prompt,
        "Evaluate fairly and conservatively. Mathematical answers must be checked for correctness before awarding full marks.",
    )
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Gemini evaluator returned an invalid result")
    return data


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_paper(request: EvaluationRequest) -> EvaluationResult:
    settings = get_settings()
    if not settings.ENABLE_EVALUATION:
        raise HTTPException(status_code=503, detail="Evaluation is disabled")

    questions = _flatten_questions(request.paper)
    key = _answer_lookup(request.paper)
    if not questions:
        raise HTTPException(status_code=400, detail="Paper contains no questions")
    if not key:
        raise HTTPException(status_code=400, detail="Paper does not contain an answer key")

    results: List[Dict[str, Any]] = []
    subjective: List[Dict[str, Any]] = []
    total_marks = 0.0

    objective_types = {"multiple choice", "true/false", "fill in the blank"}
    for q in questions:
        qnum = str(q.get("question_number"))
        entry = key.get(qnum, {})
        marks = float(entry.get("marks", q.get("marks", 0)) or 0)
        total_marks += marks
        student_answer = str(request.answers.get(qnum, "") or "").strip()
        expected = str(entry.get("answer", q.get("answer", q.get("expected_answer", ""))) or "")
        qtype = _norm(q.get("type", q.get("question_type", "")))
        base = {
            "question_number": qnum,
            "question": q.get("question", q.get("question_text", "")),
            "student_answer": student_answer,
            "expected_answer": expected,
            "max_marks": marks,
            "awarded_marks": 0.0,
            "feedback": "No answer provided.",
            "method": "deterministic" if qtype in objective_types else "gemini_rubric",
        }
        if qtype in objective_types:
            correct = _objective_match(student_answer, expected, q.get("options"))
            base["awarded_marks"] = marks if correct else 0.0
            base["feedback"] = "Correct." if correct else "Incorrect. Review the answer key."
            base["correct"] = correct
            results.append(base)
        else:
            subjective.append({
                **base,
                "expected_answer": expected,
                "marking_scheme": entry.get("marking_scheme", []),
            })

    if subjective:
        if not settings.ENABLE_EVALUATION_GEMINI:
            # Safe fallback: leave subjective answers ungraded rather than pretending.
            for item in subjective:
                item["feedback"] = "Manual teacher review required (AI evaluation disabled)."
                item["method"] = "manual_review"
                results.append(item)
        else:
            try:
                evaluated = _build_llm_batch(subjective)
                by_num = {str(x.get("question_number")): x for x in evaluated}
                for item in subjective:
                    ev = by_num.get(str(item["question_number"]), {})
                    awarded = max(0.0, min(float(item["max_marks"]), float(ev.get("awarded_marks", 0) or 0)))
                    item["awarded_marks"] = awarded
                    item["feedback"] = str(ev.get("feedback", "Teacher review recommended."))
                    item["strengths"] = ev.get("strengths", [])
                    item["missing_points"] = ev.get("missing_points", [])
                    results.append(item)
            except Exception as exc:
                logger.exception("AI evaluation failed")
                for item in subjective:
                    item["feedback"] = f"AI evaluation failed; manual review required: {exc}"
                    item["method"] = "manual_review"
                    results.append(item)

    results.sort(key=lambda x: int(x["question_number"]) if str(x["question_number"]).isdigit() else str(x["question_number"]))
    awarded = sum(float(r.get("awarded_marks", 0) or 0) for r in results)
    percentage = round((awarded / total_marks) * 100, 2) if total_marks else 0.0
    pass_mark = float(settings.EVALUATION_PASS_PERCENT)
    return EvaluationResult(
        status="success",
        student_name=request.student_name,
        total_marks=total_marks,
        awarded_marks=round(awarded, 2),
        percentage=percentage,
        grade=_grade_from_percentage(percentage),
        passed=percentage >= pass_mark,
        results=results,
        summary={
            "pass_percent": pass_mark,
            "graded_questions": len(results),
            "ai_evaluated": sum(1 for r in results if r.get("method") == "gemini_rubric"),
            "manual_review": sum(1 for r in results if r.get("method") == "manual_review"),
        },
    )


@router.post("/export-pdf")
async def export_evaluation_pdf(payload: Dict[str, Any]) -> Response:
    """Export an evaluation result as a teacher-facing PDF."""
    buf = __import__("io").BytesIO()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph("AssessNex Evaluation Report", styles["Title"]), Spacer(1, 10)]
    story.append(Paragraph(f"Student: {payload.get('student_name','Student')} | Score: {payload.get('awarded_marks',0)} / {payload.get('total_marks',0)} | {payload.get('percentage',0)}% | Grade: {payload.get('grade','F')}", styles["BodyText"]))
    story.append(Spacer(1, 12))
    rows = [["Q", "Marks", "Awarded", "Feedback"]]
    for r in payload.get("results", []) or []:
        rows.append([str(r.get("question_number","")), str(r.get("max_marks",0)), str(r.get("awarded_marks",0)), str(r.get("feedback",""))])
    table = Table(rows, colWidths=[32, 55, 60, 360], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8f4fd")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))
    story.append(table)
    doc.build(story)
    return Response(content=buf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=evaluation_report.pdf"})
