"""
Multi-Language Code Agent - Handles code formatting for multiple programming languages.

Features:
- Language detection
- Language-specific formatting
- Syntax highlighting hints
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from backend.app.agents.base.base_agent import (
    BaseFormattingAgent,
    AgentConfig,
    AgentResult,
    ContentType,
    ValidationLevel,
)
from backend.app.utils import get_logger

logger = get_logger(__name__)


class MultiLanguageCodeAgent(BaseFormattingAgent):
    """
    Handles code formatting for multiple programming languages.
    """
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        "python": [
            r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+', r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import', r'if\s+__name__\s*==',
            r':\s*$', r'\bself\.'
        ],
        "javascript": [
            r'\bconst\s+\w+', r'\blet\s+\w+', r'\bvar\s+\w+',
            r'\bfunction\s+\w+\s*\(', r'=>', r'\bconsole\.log',
            r'\bexport\s+(default\s+)?', r'\bimport\s+.*\s+from'
        ],
        "typescript": [
            r':\s*(string|number|boolean|any|void)', r'\binterface\s+\w+',
            r'\btype\s+\w+\s*=', r'<\w+>', r'\bas\s+\w+'
        ],
        "java": [
            r'\bpublic\s+class', r'\bprivate\s+', r'\bprotected\s+',
            r'\bstatic\s+void\s+main', r'System\.out\.println',
            r'\bnew\s+\w+\s*\(', r'@Override'
        ],
        "c": [
            r'#include\s*<', r'\bint\s+main\s*\(', r'\bprintf\s*\(',
            r'\bscanf\s*\(', r'\bmalloc\s*\(', r'\bfree\s*\(',
            r'\bstruct\s+\w+'
        ],
        "cpp": [
            r'#include\s*<iostream>', r'\bstd::', r'\bcout\s*<<',
            r'\bcin\s*>>', r'\bclass\s+\w+\s*\{', r'\bvirtual\s+',
            r'\btemplate\s*<'
        ],
        "sql": [
            r'\bSELECT\s+', r'\bFROM\s+', r'\bWHERE\s+',
            r'\bINSERT\s+INTO', r'\bUPDATE\s+', r'\bDELETE\s+',
            r'\bCREATE\s+TABLE', r'\bJOIN\s+'
        ],
        "html": [
            r'<html', r'<head>', r'<body>', r'<div\s*',
            r'</\w+>', r'<!DOCTYPE'
        ],
        "css": [
            r'\{[\s\S]*?\}', r':\s*[\w#]+;', r'\.\w+\s*\{',
            r'#\w+\s*\{', r'@media'
        ],
        "bash": [
            r'^#!/bin/bash', r'\becho\s+', r'\$\{?\w+\}?',
            r'\bif\s+\[', r'\bfi\b', r'\bdone\b', r'\bfor\s+\w+\s+in'
        ],
        "go": [
            r'\bpackage\s+\w+', r'\bfunc\s+\w+\s*\(',
            r'\bfmt\.Print', r'\bgo\s+func', r':='
        ],
        "rust": [
            r'\bfn\s+\w+\s*\(', r'\blet\s+mut\s+', r'\bimpl\s+',
            r'\b->.*\{', r'println!\s*\(', r'\bpub\s+fn'
        ],
    }
    
    # Language formatting guidelines
    FORMATTING_GUIDELINES = {
        "python": "4 spaces, PEP 8, snake_case",
        "javascript": "2 spaces, camelCase, semicolons optional",
        "typescript": "2 spaces, interfaces, strict types",
        "java": "4 spaces, PascalCase classes, camelCase methods",
        "c": "4 spaces, snake_case, braces on same line",
        "cpp": "4 spaces, PascalCase classes, camelCase methods",
        "sql": "Uppercase keywords, 2-4 spaces",
        "html": "2 spaces, lowercase tags",
        "css": "2 spaces, BEM naming",
        "bash": "2 spaces, UPPER_CASE for env vars",
        "go": "tabs, gofmt style",
        "rust": "4 spaces, snake_case, rustfmt style",
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MultiLanguageCodeAgent",
            content_type=ContentType.CODE,
            max_retries=2,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a multi-language code formatting specialist.

SUPPORTED LANGUAGES:
====================
- Python: PEP 8, 4 spaces, snake_case
- JavaScript/TypeScript: 2 spaces, camelCase
- Java: 4 spaces, PascalCase classes
- C/C++: 4 spaces, structured programming
- SQL: Uppercase keywords
- HTML/CSS: 2 spaces, semantic markup
- Go: tabs, gofmt standard
- Rust: 4 spaces, rustfmt standard
- Bash: 2 spaces, shell conventions

FORMATTING RULES:
=================

1. Always wrap code in appropriate markdown:
   ```language
   code
   ```

2. Detect language automatically if not specified

3. Apply language-specific conventions:
   - Indentation style
   - Naming conventions
   - Bracket placement
   - Comment style

4. Add syntax highlighting hints

Return properly formatted code with correct language tag."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        language = kwargs.get("language", "auto")
        
        return f"""Format this code with proper language-specific conventions.

INPUT CODE:
{content}

LANGUAGE: {language} (auto-detect if not specified)

Return JSON with:
{{
    "formatted_content": "code in ```language block",
    "detected_language": "the language",
    "improvements": ["list of improvements"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate formatted code."""
        errors = []
        
        # Check for code block
        if '```' not in content:
            errors.append("Missing code block wrapper")
        
        # Check for language tag
        if not re.search(r'```\w+', content):
            errors.append("Missing language tag in code block")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already formatted."""
        return bool(re.search(r'```\w+[\s\S]*```', content))
    
    def detect_language(self, code: str) -> str:
        """Detect programming language from code patterns."""
        scores = {}
        
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                    score += 1
            scores[lang] = score
        
        if not scores or max(scores.values()) == 0:
            return "text"
        
        return max(scores, key=scores.get)
    
    def format_code(
        self,
        code: str,
        language: Optional[str] = None,
    ) -> AgentResult:
        """Format code with auto-detection."""
        if language is None or language == "auto":
            language = self.detect_language(code)
        
        # Clean existing markers
        code = re.sub(r'```\w*\s*', '', code)
        code = code.replace('```', '').strip()
        
        formatted = f"```{language}\n{code}\n```"
        
        return AgentResult(
            success=True,
            content=formatted,
            original_content=code,
            agent_name=self.config.name,
            metadata={
                "language": language,
                "guidelines": self.FORMATTING_GUIDELINES.get(language, "Standard formatting"),
            }
        )
