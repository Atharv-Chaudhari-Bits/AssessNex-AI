"""
Custom Formatting System for AssessNex AI.

This module provides TYPE-SPECIFIC formatting based on question type.
"""

import re
from typing import Dict, Any, List, Optional
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


# Question types that should NEVER get special formatting
TEXT_ONLY_TYPES = [
    "Multiple Choice",
    "True/False",
    "Short Answer",
    "Long Answer",
    "Essay",
    "Fill in the Blank",
]

# Question types that need CODE formatting
CODE_TYPES = [
    "Code Implementation",
    "Code Output Prediction", 
    "Coding",
    "Coding Problem",
]

# Question types that need MATH/LaTeX formatting
MATH_TYPES = [
    "Numerical Problem",
    "Numerical",
    "Complexity Analysis",
    "Algorithm Complexity",
]

# Question types that need DIAGRAM formatting
DIAGRAM_TYPES = [
    "Diagram-Based",
    "Diagram",
]

# Scenario-based gets code formatting ONLY if code is present
SCENARIO_TYPES = [
    "Scenario-Based",
]


def get_formatting_category(question_type: str) -> str:
    """Determine the formatting category for a question type."""
    if question_type in TEXT_ONLY_TYPES:
        return "text"
    elif question_type in CODE_TYPES:
        return "code"
    elif question_type in MATH_TYPES:
        return "math"
    elif question_type in DIAGRAM_TYPES:
        return "diagram"
    elif question_type in SCENARIO_TYPES:
        return "scenario"
    else:
        return "text"


class FormatFlags:
    """Constants for formatting flags."""
    CODE_PYTHON = "[CODE:python]"
    CODE_PYTHON_END = "[/CODE]"
    CODE_JS = "[CODE:javascript]"
    CODE_SQL = "[CODE:sql]"
    CODE_JAVA = "[CODE:java]"
    CODE_GENERIC = "[CODE:any]"
    MATH_BLOCK = "[MATH]"
    MATH_BLOCK_END = "[/MATH]"
    MATH_INLINE = "[IMATH]"
    MATH_INLINE_END = "[/IMATH]"
    DIAGRAM_MERMAID = "[DIAGRAM:mermaid]"
    DIAGRAM_ASCII = "[DIAGRAM:ascii]"
    DIAGRAM_END = "[/DIAGRAM]"
    TABLE = "[TABLE]"
    TABLE_END = "[/TABLE]"
    LIST = "[LIST]"
    LIST_END = "[/LIST]"
    OUTPUT = "[OUTPUT]"
    OUTPUT_END = "[/OUTPUT]"
    STEPS = "[STEPS]"
    STEPS_END = "[/STEPS]"
    BOLD = "[BOLD]"
    BOLD_END = "[/BOLD]"
    ITALIC = "[ITALIC]"
    ITALIC_END = "[/ITALIC]"
    HIGHLIGHT = "[HIGHLIGHT]"
    HIGHLIGHT_END = "[/HIGHLIGHT]"


CODE_PATTERNS = {
    "python": [
        r"^\s*(def |class |import |from .* import)",
        r"^\s*(if |for |while |try:|except:|with |elif |else:)",
        r"^\s*return\s",
        r"^\s*print\s*\(",
        r"^\s*@\w+",
        r"^\s*(async def|await )",
        r"^\s*self\.",
        r"^\s*lambda\s",
    ],
    "javascript": [
        r"^\s*(function |const |let |var )",
        r"^\s*(if |for |while )\s*\(",
        r"^\s*return\s",
        r"^\s*console\.",
        r"^\s*(async |await )",
        r"=>",
        r"^\s*export ",
    ],
    "sql": [
        r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s",
        r"^\s*(FROM|WHERE|JOIN|GROUP BY|ORDER BY|HAVING)\s",
    ],
    "java": [
        r"^\s*(public |private |protected )",
        r"^\s*(class |interface |enum )",
        r"^\s*(static |final |abstract )",
        r"^\s*System\.",
    ],
}


def detect_language(text: str) -> str:
    """Detect programming language of code snippet."""
    scores = {lang: 0 for lang in CODE_PATTERNS.keys()}
    for lang, patterns in CODE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                scores[lang] += 1
    best_lang = max(scores, key=scores.get)
    if scores[best_lang] == 0:
        return "any"
    return best_lang


def is_code_content(text: str) -> bool:
    """Check if text contains code."""
    for patterns in CODE_PATTERNS.values():
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                return True
    return False


def has_existing_code_blocks(text: str) -> bool:
    """Check if text already has markdown code blocks."""
    return "```" in text


class ContentFormatter:
    """Type-specific content formatter."""
    
    def __init__(self):
        logger.debug("ContentFormatter initialized")
    
    def format_content(self, text: str, question_type: str, field_type: str = "answer") -> str:
        """Format content based on question type."""
        if not text:
            return text
        
        text = text.replace("\\n", "\n").replace("\\t", "    ")
        category = get_formatting_category(question_type)
        
        if category == "text":
            return text
        if category == "code":
            return self._format_for_code_type(text)
        if category == "math":
            return text
        if category == "diagram":
            return self._format_for_diagram_type(text)
        if category == "scenario":
            return self._format_for_scenario_type(text)
        return text
    
    def _format_for_code_type(self, text: str) -> str:
        if has_existing_code_blocks(text):
            return text
        if is_code_content(text):
            lang = detect_language(text)
            return f"```{lang}\n{text.strip()}\n```"
        return text
    
    def _format_for_diagram_type(self, text: str) -> str:
        if "```mermaid" in text.lower():
            return text
        mermaid_keywords = ["graph ", "flowchart ", "sequenceDiagram", "classDiagram"]
        if any(kw in text for kw in mermaid_keywords):
            return f"```mermaid\n{text.strip()}\n```"
        return text
    
    def _format_for_scenario_type(self, text: str) -> str:
        if not is_code_content(text) and not has_existing_code_blocks(text):
            return text
        return self._format_for_code_type(text)


def format_question_with_flags(question: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """Format question fields based on question type."""
    formatter = ContentFormatter()
    category = get_formatting_category(question_type)
    
    if category == "text":
        return question
    
    if question.get("question_text"):
        question["question_text"] = formatter.format_content(
            question["question_text"], question_type=question_type, field_type="question"
        )
    
    if question.get("expected_answer"):
        question["expected_answer"] = formatter.format_content(
            question["expected_answer"], question_type=question_type, field_type="answer"
        )
    
    if question.get("explanation") and category in ["code", "scenario"]:
        question["explanation"] = formatter.format_content(
            question["explanation"], question_type=question_type, field_type="explanation"
        )
    
    return question


def format_all_questions_with_flags(questions: List[Dict[str, Any]], question_type: str) -> List[Dict[str, Any]]:
    """Format all questions in a list based on question type."""
    category = get_formatting_category(question_type)
    
    if category == "text":
        # IMPORTANT: Sanitize text-only questions - remove any accidental code/mermaid
        logger.info(f"Text type '{question_type}': Sanitizing {len(questions)} questions (no special formatting)")
        return [sanitize_text_question(q) for q in questions]
    
    formatted = []
    for q in questions:
        try:
            formatted.append(format_question_with_flags(q, question_type))
        except Exception as e:
            logger.error(f"Error formatting question: {e}")
            formatted.append(q)
    
    logger.info(f"Formatted {len(formatted)} questions of type '{question_type}'")
    return formatted


def sanitize_text_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a text-only question by removing any accidental code/mermaid blocks.
    
    This is a safety net for when LLM generates inappropriate formatting for
    text-based question types (MCQ, True/False, Essay, etc.)
    """
    def clean_text(text: str) -> str:
        if not text:
            return text
        
        # Remove mermaid blocks
        mermaid_pattern = r'```mermaid\s*[\s\S]*?```'
        text = re.sub(mermaid_pattern, '', text, flags=re.IGNORECASE)
        
        # Remove other code blocks (unless the question explicitly references code)
        # Be careful not to remove code from questions that mention code in the text
        code_block_pattern = r'```\w*\s*[\s\S]*?```'
        
        # Only remove code blocks if the question doesn't seem to be about code
        code_keywords = ['code', 'function', 'output', 'program', 'algorithm', 'implement']
        if not any(kw in text.lower() for kw in code_keywords):
            text = re.sub(code_block_pattern, '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
    
    # Clean each field
    if question.get("question_text"):
        question["question_text"] = clean_text(question["question_text"])
    
    if question.get("expected_answer"):
        question["expected_answer"] = clean_text(question["expected_answer"])
    
    if question.get("explanation"):
        question["explanation"] = clean_text(question["explanation"])
    
    return question


def format_output_block(output: str) -> str:
    return f"[OUTPUT]\n{output}\n[/OUTPUT]"


def format_steps(steps: List[str]) -> str:
    steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
    return f"[STEPS]\n{steps_text}\n[/STEPS]"
