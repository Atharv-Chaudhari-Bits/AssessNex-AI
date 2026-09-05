"""Deterministic math sanity checks for generated educational questions."""
from __future__ import annotations
import re
from typing import Any, Dict

try:
    import sympy as sp
except Exception:  # pragma: no cover
    sp = None

_LATEX_RE = re.compile(r"\\(?:frac|sqrt|sum|int|lim|sin|cos|tan|log|ln|times|cdot|leq|geq|neq|pm)\b")


def _latex_to_sympy(text: str) -> str:
    s = str(text or "")
    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)
    s = s.replace("\\times", "*").replace("\\cdot", "*")
    s = s.replace("\\leq", "<=").replace("\\geq", ">=").replace("\\neq", "!=")
    s = s.replace("^", "**")
    return s


def validate_math_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deterministic sanity report; never raises for user content."""
    result = {"enabled": sp is not None, "status": "not_applicable", "issues": [], "score": 1.0}
    if sp is None:
        result["status"] = "validator_unavailable"
        return result
    text = " ".join(str(question.get(k, "")) for k in ("question_text", "expected_answer", "explanation"))
    if not (_LATEX_RE.search(text) or question.get("question_type") in {"Numerical Problem", "Complexity Analysis"}):
        return result

    result["status"] = "checked"
    answer = str(question.get("expected_answer", ""))
    try:
        # Catch malformed common fraction/square-root structures.
        if "\\frac" in answer and not re.search(r"\\frac\{[^{}]+\}\{[^{}]+\}", answer):
            result["issues"].append("Malformed LaTeX fraction in expected answer")
        if "\\sqrt" in answer and not re.search(r"\\sqrt(?:\[[^]]+\])?\{[^{}]+\}", answer):
            result["issues"].append("Malformed LaTeX square root in expected answer")
        # If an explicit simple equality is present, make sure both sides parse.
        plain = _latex_to_sympy(answer)
        match = re.search(r"(?<![<>])(?<![=])([0-9xX*+\-/(). ]+)\s*=\s*([0-9xX*+\-/(). ]+)", plain)
        if match:
            lhs = sp.sympify(match.group(1).replace("X", "x"))
            rhs = sp.sympify(match.group(2).replace("X", "x"))
            if lhs.has(sp.Symbol("x")) or rhs.has(sp.Symbol("x")):
                # Symbolic equality is not necessarily an identity; just ensure it parses.
                pass
            elif sp.simplify(lhs - rhs) != 0:
                result["issues"].append("Explicit numeric equality in answer is inconsistent")
    except Exception as exc:
        result["issues"].append(f"Math expression could not be parsed: {exc}")

    if result["issues"]:
        result["score"] = max(0.0, 1.0 - 0.25 * len(result["issues"]))
        result["status"] = "warning"
    return result
