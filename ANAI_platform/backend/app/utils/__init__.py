"""
Utils package initialization.

Exports commonly used utility functions and classes.
"""

from backend.app.utils.logger import get_logger
from backend.app.utils.validators import (
    validate_subject,
    validate_question_type,
    validate_difficulty_level,
    validate_bloom_level,  # ADD THIS
    validate_num_questions,
    validate_topic_focus,  # ADD THIS
    sanitize_input,
    sanitize_document_text,  # ADD THIS
    validate_all,  # ADD THIS
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
    normalize_latex_delimiters,
    fix_question_latex,
)
from backend.app.utils.visuals import render_visual, attach_rendered_visual
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

# Try to import document parser functions (optional)
DOCUMENT_PARSER_AVAILABLE = False
parse_document_bytes = None
extract_key_sections = None

try:
    from backend.app.utils.document_parser import (
        parse_document_bytes,
        parse_pdf_bytes,
        parse_docx_bytes,
        parse_txt_bytes,
        extract_key_sections,
        parse_document_with_extraction,
    )
    DOCUMENT_PARSER_AVAILABLE = True
    _document_parser_available = True
except ImportError:
    # Document parser not available - define placeholder functions
    def parse_document_bytes(*args, **kwargs):
        raise ImportError("Document parser not available. Install pypdf and python-docx.")
    
    def extract_key_sections(*args, **kwargs):
        raise ImportError("Document parser not available. Install pypdf and python-docx.")
    
    DOCUMENT_PARSER_AVAILABLE = False


# Now define __all__ after all imports
__all__ = [
    # Logger
    "get_logger",
    
    # Validators
    "validate_subject",
    "validate_question_type",
    "validate_difficulty_level",
    "validate_bloom_level",
    "validate_num_questions",
    "validate_topic_focus",
    "sanitize_input",
    "sanitize_document_text",
    "validate_all",
    
    # Helpers
    "generate_question_id",
    "parse_llm_response",
    "format_question_response",
    "chunk_list",
    "get_current_timestamp",
    "retry_with_backoff",
    "ensure_code_blocks",
    "format_question_content",
    "format_all_questions",
    "fix_latex_backslashes",
    "normalize_latex_delimiters",
    "fix_question_latex",
    
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
    "render_visual",
    "attach_rendered_visual",
    
    # Document parser
    "parse_document_bytes",
    "extract_key_sections",
    "DOCUMENT_PARSER_AVAILABLE",
]

# Also add parse_pdf_bytes and others if they were successfully imported
if DOCUMENT_PARSER_AVAILABLE:
    try:
        from backend.app.utils.document_parser import (
            parse_pdf_bytes,
            parse_docx_bytes,
            parse_txt_bytes,
            parse_document_with_extraction,
        )
        __all__.extend([
            "parse_pdf_bytes",
            "parse_docx_bytes",
            "parse_txt_bytes",
            "parse_document_with_extraction",
        ])
    except ImportError:
        pass