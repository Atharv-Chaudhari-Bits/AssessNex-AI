"""Deterministic quality gate for generated papers."""
from __future__ import annotations
import re
from typing import Any, Dict, List
from backend.app.config import get_settings
from backend.app.utils.math_validation import validate_math_question


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def evaluate_question(question: Dict[str, Any], section_type: str) -> Dict[str, Any]:
    issues: List[str] = []
    text = _normalize(question.get("question_text", ""))
    answer = _normalize(question.get("expected_answer", ""))
    if len(text) < 12:
        issues.append("Question text is too short")
    if not answer:
        issues.append("Missing expected answer")
    if section_type == "Multiple Choice":
        options = question.get("options") or []
        cleaned = [_normalize(x) for x in options if _normalize(x)]
        if len(cleaned) < 4:
            issues.append("MCQ should contain at least four options")
        if len(cleaned) != len(set(cleaned)):
            issues.append("Duplicate MCQ options detected")
    math = validate_math_question(question) if get_settings().ENABLE_MATH_VALIDATION else {"enabled": False, "status": "disabled", "issues": [], "score": 1.0}
    issues.extend(math.get("issues", []))
    score = max(0, 100 - 15 * len(issues))
    return {"score": score, "passed": score >= get_settings().PAPER_QUALITY_THRESHOLD, "issues": issues, "math": math}


def evaluate_paper(sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    reports = []
    seen = {}
    for section in sections:
        for question in section.get("questions", []):
            report = evaluate_question(question, section.get("question_type", ""))
            normalized = _normalize(question.get("question_text", ""))
            if normalized and normalized in seen:
                report["issues"].append(f"Duplicate wording with question {seen[normalized]}")
                report["score"] = max(0, report["score"] - 20)
                report["passed"] = report["score"] >= get_settings().PAPER_QUALITY_THRESHOLD
            elif normalized:
                seen[normalized] = question.get("question_number")
            question["quality"] = report
            reports.append(report)
    avg = round(sum(r["score"] for r in reports) / len(reports), 2) if reports else 0
    return {
        "enabled": get_settings().ENABLE_QUALITY_CHECK,
        "overall_score": avg,
        "passed": avg >= get_settings().PAPER_QUALITY_THRESHOLD,
        "question_reports": reports,
        "issues_count": sum(len(r["issues"]) for r in reports),
    }
