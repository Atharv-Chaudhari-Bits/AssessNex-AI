"""Deterministic educational visual generation for AssessNex AI.

The LLM describes a visual; this module renders it locally so the final image is
reproducible, safe, and does not require a separate image-generation provider.
"""

from __future__ import annotations

import base64
import io
import math
import re
from typing import Any, Dict, Iterable, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from backend.app.config import get_settings


_ALLOWED_NAMES = {
    "x": None,
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "log": np.log,
    "log10": np.log10,
    "abs": np.abs,
    "pi": np.pi,
    "e": math.e,
}


def _safe_expression(expression: str) -> str:
    """Normalize a small, explicitly allowed expression language."""
    expr = str(expression or "").strip()
    if not expr or len(expr) > 180:
        raise ValueError("Graph expression is empty or too long")
    expr = expr.replace("^", "**")
    expr = expr.replace("\\cdot", "*").replace("\\times", "*")
    expr = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", expr)
    if not re.fullmatch(r"[0-9A-Za-z_+\-*/()., *]+", expr):
        raise ValueError("Graph expression contains unsupported characters")
    return expr


def _evaluate_expression(expression: str, x: np.ndarray) -> np.ndarray:
    expr = _safe_expression(expression)
    names = dict(_ALLOWED_NAMES)
    names["x"] = x
    # Builtins are explicitly removed. The expression grammar above is also restricted.
    y = eval(expr, {"__builtins__": {}}, names)  # noqa: S307 - intentionally restricted
    y = np.asarray(y, dtype=float)
    if y.ndim == 0:
        y = np.full_like(x, float(y))
    if y.shape != x.shape:
        y = np.broadcast_to(y, x.shape)
    return np.nan_to_num(y, nan=np.nan, posinf=np.nan, neginf=np.nan)


def render_visual(visual: Dict[str, Any]) -> Optional[str]:
    """Render a visual specification and return a base64 PNG payload."""
    if not isinstance(visual, dict):
        return None

    kind = str(visual.get("type", "")).lower().strip()
    if kind not in {"function_graph", "line_graph", "scatter_graph"}:
        return None

    fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=get_settings().VISUAL_RENDER_DPI)
    try:
        ax.grid(True, alpha=0.22)
        ax.axhline(0, linewidth=0.8)
        ax.axvline(0, linewidth=0.8)
        ax.set_xlabel(str(visual.get("x_label", "x")))
        ax.set_ylabel(str(visual.get("y_label", "y")))
        ax.set_title(str(visual.get("title", "Graph")))

        if kind == "function_graph":
            xmin = float(visual.get("x_min", -10))
            xmax = float(visual.get("x_max", 10))
            if xmin >= xmax:
                raise ValueError("x_min must be smaller than x_max")
            x = np.linspace(xmin, xmax, max(100, min(get_settings().VISUAL_MAX_POINTS, 1200)))
            y = _evaluate_expression(str(visual.get("expression", "x")), x)
            ax.plot(x, y, linewidth=2.4, label=str(visual.get("label", "f(x)")))
        else:
            points = visual.get("points", [])
            if not isinstance(points, Iterable):
                raise ValueError("Graph points must be a list")
            xs, ys = [], []
            for point in points:
                if isinstance(point, (list, tuple)) and len(point) == 2:
                    xs.append(float(point[0]))
                    ys.append(float(point[1]))
            if not xs:
                raise ValueError("Graph contains no valid points")
            if kind == "scatter_graph":
                ax.scatter(xs, ys, s=44)
            else:
                ax.plot(xs, ys, marker="o", linewidth=2.0)

        if visual.get("x_min") is not None and visual.get("x_max") is not None:
            ax.set_xlim(float(visual["x_min"]), float(visual["x_max"]))
        if visual.get("y_min") is not None and visual.get("y_max") is not None:
            ax.set_ylim(float(visual["y_min"]), float(visual["y_max"]))
        if visual.get("legend", True):
            ax.legend(loc="best")

        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        return base64.b64encode(buf.getvalue()).decode("ascii")
    finally:
        plt.close(fig)


def attach_rendered_visual(question: Dict[str, Any]) -> Dict[str, Any]:
    """Render an optional LLM visual spec and attach it to the question."""
    visual = question.get("visual")
    if not get_settings().ENABLE_VISUAL_GENERATION:
        question["visual"] = None
        return question
    if not visual:
        return question
    try:
        image = render_visual(visual)
        if image:
            question["visual"]["image_base64"] = image
            question["visual"]["mime_type"] = "image/png"
            question["visual"]["render_status"] = "success"
    except Exception as exc:
        question["visual"]["render_status"] = "failed"
        question["visual"]["render_error"] = str(exc)
    return question
