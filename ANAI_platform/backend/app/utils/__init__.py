"""
Utils package initialization.

Exports commonly used utility functions and classes.
"""

from backend.app.utils.logger import get_logger
from backend.app.utils.validators import (
    validate_subject,
    validate_question_type,
    validate_difficulty_level,
    validate_num_questions,
    sanitize_input,
)
from backend.app.utils.helpers import (
    generate_question_id,
    parse_llm_response,
    format_question_response,
    chunk_list,
    get_current_timestamp,
    retry_with_backoff,
    ensure_code_blocks,
    format_question_content,
    format_all_questions,
    fix_latex_backslashes,
    fix_question_latex,
)
from backend.app.utils.formatters import (
    FormatFlags,
    ContentFormatter,
    format_question_with_flags,
    format_all_questions_with_flags,
    format_output_block,
    format_steps,
    detect_language,
    is_code_content,
    get_formatting_category,
    TEXT_ONLY_TYPES,
    CODE_TYPES,
    MATH_TYPES,
    DIAGRAM_TYPES,
    SCENARIO_TYPES,
)

__all__ = [
    "get_logger",
    "validate_subject",
    "validate_question_type",
    "validate_difficulty_level",
    "validate_num_questions",
    "sanitize_input",
    "generate_question_id",
    "parse_llm_response",
    "format_question_response",
    "chunk_list",
    "get_current_timestamp",
    "retry_with_backoff",
    "ensure_code_blocks",
    "format_question_content",
    "format_all_questions",
    # Formatter exports
    "FormatFlags",
    "ContentFormatter",
    "format_question_with_flags",
    "format_all_questions_with_flags",
    "format_output_block",
    "format_steps",
    "detect_language",
    "is_code_content",
    "get_formatting_category",
    # Type constants
    "TEXT_ONLY_TYPES",
    "CODE_TYPES",
    "MATH_TYPES",
    "DIAGRAM_TYPES",
    "SCENARIO_TYPES",
]
