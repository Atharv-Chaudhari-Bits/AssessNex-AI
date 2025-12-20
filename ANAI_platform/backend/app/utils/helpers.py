"""
Utility functions module for AssessNex AI.

This module contains helper functions used throughout the application
for common operations and data transformations.
"""

import json
import uuid
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.utils.logger import get_logger


logger = get_logger(__name__)


# =============================================================================
# CODE FORMATTING UTILITIES
# =============================================================================

def ensure_code_blocks(text: str, language: str = "python") -> str:
    """
    Ensure any code in the text is wrapped in proper markdown code blocks.
    
    This function detects code patterns and wraps them in ```language blocks
    if they're not already wrapped.
    
    Args:
        text: Text that may contain code
        language: Programming language for the code block
        
    Returns:
        Text with properly formatted code blocks
    """
    if not text:
        return text
    
    # Normalize escaped newlines
    text = text.replace('\\n', '\n').replace('\\t', '    ')
    
    # Check if already has code blocks
    code_block_pattern = r'```\w*\n[\s\S]*?```'
    if re.search(code_block_pattern, text):
        # Already has code blocks - return as is
        return text
    
    # Code detection patterns
    code_indicators = [
        r'^\s*(def |class |import |from .* import)',  # Python definitions
        r'^\s*(if |for |while |try:|except:|with )',  # Control structures
        r'^\s*return ',  # Return statements
        r'^\s*print\(',  # Print calls
        r'^\s*[a-z_]+\s*=\s*\[',  # List assignments
        r'^\s*[a-z_]+\s*=\s*\{',  # Dict assignments
        r'^\s*[a-z_]+\s*=\s*pd\.',  # Pandas operations
        r'^\s*[a-z_]+\s*=\s*np\.',  # NumPy operations
        r'^\s*@\w+',  # Decorators
        r'^\s*"""',  # Docstrings
    ]
    
    # Check if text looks like code
    lines = text.split('\n')
    code_lines = []
    text_lines = []
    in_code_section = False
    
    for line in lines:
        is_code_line = any(re.match(pattern, line) for pattern in code_indicators)
        
        # Also check for indented lines that follow code
        if in_code_section and (line.startswith('    ') or line.startswith('\t') or line.strip() == ''):
            is_code_line = True
        
        if is_code_line:
            in_code_section = True
            code_lines.append(line)
        else:
            if code_lines and in_code_section:
                # End of code section - check if this line is part of it
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    in_code_section = False
                    text_lines.append(('code', '\n'.join(code_lines)))
                    code_lines = []
                    text_lines.append(('text', line))
                else:
                    code_lines.append(line)
            else:
                text_lines.append(('text', line))
    
    # Handle remaining code lines
    if code_lines:
        text_lines.append(('code', '\n'.join(code_lines)))
    
    # If we found no code sections, check if entire text is code
    if not any(t[0] == 'code' for t in text_lines):
        # Check if the entire text looks like code
        full_text_is_code = any(re.search(pattern, text, re.MULTILINE) for pattern in code_indicators)
        if full_text_is_code:
            return f"```{language}\n{text.strip()}\n```"
        return text
    
    # Reconstruct with code blocks
    result_parts = []
    for item_type, content in text_lines:
        if item_type == 'code':
            result_parts.append(f"```{language}\n{content.strip()}\n```")
        else:
            result_parts.append(content)
    
    return '\n'.join(result_parts)


def format_question_content(question: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """
    Format all content in a question to ensure proper code/math/diagram formatting.
    
    This is a post-processing step that runs after LLM generation to enforce
    proper formatting before sending to the UI.
    
    Args:
        question: Question dictionary with question_text, expected_answer, explanation
        question_type: Type of question for context-aware formatting
        
    Returns:
        Question with properly formatted content
    """
    CODE_TYPES = ["Code Implementation", "Code Output Prediction", "Coding", "Coding Problem"]
    
    if question_type in CODE_TYPES:
        # Ensure code blocks in question_text
        if question.get("question_text"):
            question["question_text"] = ensure_code_blocks(
                question["question_text"], 
                language="python"
            )
        
        # Ensure code blocks in expected_answer
        if question.get("expected_answer"):
            question["expected_answer"] = ensure_code_blocks(
                question["expected_answer"], 
                language="python"
            )
        
        # Ensure code blocks in explanation (code examples within)
        if question.get("explanation"):
            question["explanation"] = ensure_code_blocks(
                question["explanation"], 
                language="python"
            )
    
    return question


def format_all_questions(
    questions: List[Dict[str, Any]], 
    question_type: str
) -> List[Dict[str, Any]]:
    """
    Format all questions in a list to ensure proper formatting.
    
    Args:
        questions: List of question dictionaries
        question_type: Type of questions
        
    Returns:
        List of properly formatted questions
    """
    formatted = []
    for q in questions:
        try:
            formatted.append(format_question_content(q, question_type))
        except Exception as e:
            logger.error(f"Error formatting question: {e}")
            formatted.append(q)  # Keep original if formatting fails
    return formatted


def generate_question_id() -> str:
    """
    Generate a unique question ID.

    Returns:
        str: Unique question identifier

    Example:
        >>> question_id = generate_question_id()
        >>> len(question_id) > 0
        True
    """
    return f"Q-{uuid.uuid4().hex[:12].upper()}"


def preserve_latex_in_json(json_str: str) -> str:
    """
    Preserve LaTeX backslash commands before JSON parsing.
    
    The issue is that in JSON, \\t is a valid escape for TAB.
    So when LLM returns "\\times" in JSON, the JSON parser sees \\t as TAB.
    
    We need to escape the backslash before \t commands to prevent this.
    In the raw JSON string, we look for backslash-t patterns and double the backslash.
    """
    import re
    
    # In the raw JSON string (before parsing), LaTeX commands appear as:
    # "\\times" (which is \ + times in the actual string)
    # The JSON parser will interpret \t as TAB, so we need to escape it
    
    # Pattern: backslash followed by t and then specific suffixes
    # We need to replace \t with \\t (escape the backslash)
    latex_t_patterns = [
        (r'\\times', r'\\\\times'),
        (r'\\text', r'\\\\text'),
        (r'\\theta', r'\\\\theta'),
        (r'\\tan', r'\\\\tan'),
        (r'\\triangle', r'\\\\triangle'),
        (r'\\tau', r'\\\\tau'),
        (r'\\to(?![a-z])', r'\\\\to'),  # \to but not \top, \total, etc.
        (r'\\top', r'\\\\top'),
    ]
    
    for pattern, replacement in latex_t_patterns:
        json_str = re.sub(pattern, replacement, json_str)
    
    return json_str


def parse_llm_response(response_text: str) -> Any:
    """
    Parse LLM response text into structured data.

    Attempts to parse JSON from LLM response. If parsing fails,
    returns the raw response in a dictionary format.

    Args:
        response_text: Raw response from LLM

    Returns:
        Any: Parsed response data (list, dict, or raw response)

    Raises:
        ValueError: If response cannot be parsed
    """
    try:
        # Preserve LaTeX backslashes before parsing
        response_text = preserve_latex_in_json(response_text)
        
        # First, try to parse the entire response as JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON array from response
        start_idx = response_text.find("[")
        end_idx = response_text.rfind("]") + 1

        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            logger.debug(f"Extracted JSON array: {json_str[:100]}...")
            return json.loads(json_str)

        # Try to extract JSON object from response
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1

        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            logger.debug(f"Extracted JSON object: {json_str[:100]}...")
            return json.loads(json_str)

        logger.warning("No JSON found in response, returning raw text")
        return {"raw_response": response_text}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from response: {str(e)}")
        logger.error(f"Response text: {response_text[:200]}")
        return {"raw_response": response_text, "parse_error": str(e)}


def fix_latex_backslashes(text: str) -> str:
    """
    Fix LaTeX backslashes that may have been corrupted during JSON parsing.
    
    Common issues:
    - \\times becomes TAB + imes (because \\t is interpreted as tab)
    - \\text becomes TAB + ext
    - \\frac becomes frac (backslash lost)
    
    Args:
        text: Text that may contain corrupted LaTeX
        
    Returns:
        Text with fixed LaTeX commands
    """
    if not text:
        return text
    
    import re
    
    # CRITICAL FIX: Direct replacement for TAB + suffix patterns
    # When JSON parses \times, the \t becomes a TAB character, leaving TAB + "imes"
    # We need to replace TAB + suffix with backslash + t + suffix
    
    # Use explicit TAB character (\t) replacement
    text = text.replace('\t' + 'imes', '\\times')
    text = text.replace('\t' + 'ext{', '\\text{')
    text = text.replace('\t' + 'ext ', '\\text ')
    text = text.replace('\t' + 'heta', '\\theta')
    text = text.replace('\t' + 'an(', '\\tan(')
    text = text.replace('\t' + 'an ', '\\tan ')
    text = text.replace('\t' + 'riangle', '\\triangle')
    text = text.replace('\t' + 'au', '\\tau')
    
    # Also handle 4-space expansion of tabs
    text = text.replace('    imes', '\\times')
    text = text.replace('    ext{', '\\text{')
    text = text.replace('    heta', '\\theta')
    
    # Common LaTeX commands that need backslash prefix (for other cases)
    latex_commands = [
        'times', 'text', 'theta', 'tan', 'triangle', 'tau',  # t-commands added
        'frac', 'sqrt', 'sum', 'prod', 'int', 'lim', 'log', 'ln', 'sin', 'cos',
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'lambda', 'mu', 'sigma', 'pi',
        'infty', 'partial', 'nabla', 'cdot', 'div', 'pm', 'mp', 'leq', 'geq', 'neq',
        'approx', 'equiv', 'subset', 'supset', 'in', 'notin', 'cup', 'cap', 'forall', 'exists',
        'rightarrow', 'leftarrow', 'Rightarrow', 'Leftarrow', 'implies', 'iff',
        'mathbf', 'mathit', 'mathrm', 'mathcal', 'mathbb', 'binom', 'choose',
        'begin', 'end', 'left', 'right', 'big', 'Big', 'bigg', 'Bigg',
        'over', 'atop', 'above', 'displaystyle', 'textstyle',
    ]
    
    # Fix commands that lost their backslash (only within $ delimiters)
    def fix_in_math(match):
        content = match.group(0)
        for cmd in latex_commands:
            # Pattern: command name not preceded by backslash or letter
            pattern = r'(?<!\\)(?<![a-zA-Z])(' + cmd + r')(?=\{|[^a-zA-Z]|$)'
            content = re.sub(pattern, r'\\' + cmd, content)
        return content
    
    # Process inline math ($...$)
    text = re.sub(r'\$[^\$]+\$', fix_in_math, text)
    
    # Process display math ($$...$$)  
    text = re.sub(r'\$\$[^\$]+\$\$', fix_in_math, text, flags=re.DOTALL)
    
    return text


def fix_question_latex(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix LaTeX in all text fields of a question.
    
    Args:
        question: Question dictionary
        
    Returns:
        Question with fixed LaTeX
    """
    text_fields = ['question_text', 'expected_answer', 'explanation']
    
    for field in text_fields:
        if question.get(field):
            question[field] = fix_latex_backslashes(question[field])
    
    return question


def format_question_response(
    question_id: str,
    subject: str,
    question_type: str,
    difficulty_level: str,
    question_text: str,
    options: Optional[List[str]] = None,
    expected_answer: str = "",
    explanation: str = "",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Format a question into the standard response structure.

    Args:
        question_id: Unique question identifier
        subject: Subject area
        question_type: Type of question
        difficulty_level: Difficulty level
        question_text: The question
        options: Optional answer options
        expected_answer: Expected answer
        explanation: Answer explanation
        tags: Optional tags

    Returns:
        Dict[str, Any]: Formatted question dictionary
    """
    # Ensure options is a list or None
    if options is not None and not isinstance(options, list):
        if isinstance(options, bool):
            options = None
        else:
            try:
                options = [str(options)]
            except Exception:
                options = None
    
    # Ensure all string fields are strings
    if not isinstance(question_text, str):
        question_text = str(question_text) if question_text else ""
    if not isinstance(expected_answer, str):
        expected_answer = str(expected_answer) if expected_answer else ""
    if not isinstance(explanation, str):
        explanation = str(explanation) if explanation else ""
    
    # Ensure tags is a list
    if tags is None:
        tags = []
    elif not isinstance(tags, list):
        try:
            tags = [str(tags)]
        except Exception:
            tags = []
    
    return {
        "id": str(question_id),
        "subject": str(subject),
        "question_type": str(question_type),
        "difficulty_level": str(difficulty_level),
        "question_text": question_text,
        "options": options,
        "expected_answer": expected_answer,
        "explanation": explanation,
        "tags": tags,
    }


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List[List[Any]]: List of chunks

    Example:
        >>> numbers = list(range(10))
        >>> chunks = chunk_list(numbers, 3)
        >>> len(chunks)
        4
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        str: ISO formatted timestamp
    """
    return datetime.utcnow().isoformat() + "Z"


def retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
):
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        backoff_factor: Factor to multiply delay by each retry

    Returns:
        Any: Result from function

    Raises:
        Exception: If all retries fail
    """
    import time

    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1} failed. "
                    f"Retrying in {delay} seconds: {str(e)}"
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries} attempts failed")

    raise last_exception if last_exception else Exception("Operation failed")
