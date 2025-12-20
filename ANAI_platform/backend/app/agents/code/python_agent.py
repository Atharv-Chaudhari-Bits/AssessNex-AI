"""
Python Code Agent - Specialized agent for Python code formatting.

Features:
- PEP 8 style formatting
- Proper indentation
- Docstrings
- Type hints
- Code organization
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


class PythonCodeAgent(BaseFormattingAgent):
    """
    Specialized agent for Python code formatting and validation.
    
    Ensures:
    - PEP 8 compliance
    - Proper indentation (4 spaces)
    - Docstrings
    - Type hints
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="PythonCodeAgent",
            content_type=ContentType.CODE,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a Python code formatting specialist following PEP 8.

PYTHON CODE FORMATTING RULES:
=============================

1. CODE BLOCK WRAPPER:
   Always wrap Python code in:
   ```python
   code here
   ```

2. INDENTATION:
   - Use 4 spaces (not tabs)
   - Consistent indentation in blocks

3. NAMING CONVENTIONS:
   - snake_case for functions and variables
   - PascalCase for classes
   - UPPER_CASE for constants
   - _private for internal use

4. DOCSTRINGS:
   def function_name(param: type) -> return_type:
       \"\"\"
       Brief description.
       
       Args:
           param: Description of parameter.
           
       Returns:
           Description of return value.
       \"\"\"
       pass

5. TYPE HINTS:
   def add(a: int, b: int) -> int:
       return a + b
   
   from typing import List, Dict, Optional
   def process(items: List[str]) -> Dict[str, int]:
       pass

6. IMPORTS:
   # Standard library
   import os
   import sys
   
   # Third party
   import numpy as np
   
   # Local
   from . import module

7. LINE LENGTH:
   - Max 79 characters for code
   - Max 72 for docstrings/comments

8. BLANK LINES:
   - 2 blank lines before/after class/function definitions
   - 1 blank line between methods

9. SPACING:
   - Space after commas: func(a, b, c)
   - Space around operators: x = y + z
   - No space inside brackets: list[0]

10. COMMENTS:
    - Inline: x = x + 1  # Increment x
    - Block: 
    # This is a longer explanation
    # that spans multiple lines

Return properly formatted Python code in a code block."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        include_docstrings = kwargs.get("docstrings", True)
        include_type_hints = kwargs.get("type_hints", True)
        
        return f"""Format this Python code following PEP 8 guidelines.

INPUT CODE:
{content}

REQUIREMENTS:
- Use 4-space indentation
- Add docstrings: {include_docstrings}
- Add type hints: {include_type_hints}
- Follow PEP 8 naming conventions
- Wrap in ```python code block

Return JSON with:
{{
    "formatted_content": "the formatted code in ```python block",
    "improvements": ["list of improvements made"],
    "warnings": ["any potential issues"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Python code."""
        errors = []
        
        # Check for code block wrapper
        if '```python' not in content and '```' not in content:
            errors.append("Missing code block wrapper")
        
        # Extract code
        code_match = re.search(r'```(?:python)?\s*([\s\S]*?)```', content)
        if not code_match:
            return len(errors) == 0, errors
        
        code = code_match.group(1)
        
        # Check basic syntax
        lines = code.split('\n')
        
        # Check indentation consistency
        indent_chars = set()
        for line in lines:
            if line.strip() and line[0] in ' \t':
                # Get leading whitespace
                leading = len(line) - len(line.lstrip())
                if '\t' in line[:leading]:
                    indent_chars.add('tab')
                else:
                    indent_chars.add('space')
        
        if len(indent_chars) > 1:
            errors.append("Mixed tabs and spaces in indentation")
        
        # Check for common Python syntax issues
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Missing colon after def/class/if/for/while/etc
            keywords = ['def ', 'class ', 'if ', 'elif ', 'else', 'for ', 'while ', 'try', 'except', 'finally', 'with ']
            for kw in keywords:
                if stripped.startswith(kw) and not stripped.endswith(':') and not stripped.endswith(':\\'):
                    if kw in ['else', 'try', 'finally'] and stripped == kw.strip():
                        errors.append(f"Line {i}: Missing colon after '{kw.strip()}'")
                    elif kw not in ['else', 'try', 'finally']:
                        # More complex check for multi-line statements
                        if not stripped.endswith('\\') and ':' not in stripped:
                            pass  # Could be multi-line, skip
        
        # Check bracket balance
        brackets = {'(': 0, '[': 0, '{': 0}
        closers = {')': '(', ']': '[', '}': '{'}
        
        for char in code:
            if char in brackets:
                brackets[char] += 1
            elif char in closers:
                brackets[closers[char]] -= 1
        
        for bracket, count in brackets.items():
            if count != 0:
                errors.append(f"Unbalanced '{bracket}' brackets")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if code is already formatted."""
        has_block = '```python' in content
        has_proper_indent = bool(re.search(r'\n    \w', content))
        return has_block and has_proper_indent
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """Basic Python formatting."""
        code = content.strip()
        
        # Remove existing code block markers
        code = re.sub(r'```\w*\s*', '', code)
        code = code.replace('```', '')
        
        # Normalize indentation to 4 spaces
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # Count leading whitespace
                leading = len(line) - len(line.lstrip())
                # Convert tabs to 4 spaces
                if '\t' in line[:leading]:
                    line = line.replace('\t', '    ')
                formatted_lines.append(line)
            else:
                formatted_lines.append('')
        
        formatted_code = '\n'.join(formatted_lines)
        
        return f"```python\n{formatted_code}\n```"
    
    def format_function(
        self,
        name: str,
        params: List[Tuple[str, str]],  # (name, type)
        return_type: str,
        body: str,
        docstring: Optional[str] = None,
    ) -> str:
        """Format a Python function with proper structure."""
        # Build parameter string
        param_strs = [f"{p[0]}: {p[1]}" for p in params]
        params_str = ", ".join(param_strs)
        
        lines = [f"def {name}({params_str}) -> {return_type}:"]
        
        if docstring:
            lines.append('    """')
            for doc_line in docstring.split('\n'):
                lines.append(f"    {doc_line}")
            lines.append('    """')
        
        # Add body with proper indentation
        for body_line in body.split('\n'):
            lines.append(f"    {body_line}")
        
        return "```python\n" + "\n".join(lines) + "\n```"
    
    def format_class(
        self,
        name: str,
        methods: List[Dict[str, Any]],
        docstring: Optional[str] = None,
        base_classes: Optional[List[str]] = None,
    ) -> str:
        """Format a Python class with proper structure."""
        bases = f"({', '.join(base_classes)})" if base_classes else ""
        
        lines = [f"class {name}{bases}:"]
        
        if docstring:
            lines.append('    """')
            for doc_line in docstring.split('\n'):
                lines.append(f"    {doc_line}")
            lines.append('    """')
        
        if not methods:
            lines.append("    pass")
        else:
            for method in methods:
                lines.append("")
                method_code = self.format_function(**method)
                # Remove wrapper and adjust indentation
                method_lines = method_code.replace('```python\n', '').replace('\n```', '').split('\n')
                for ml in method_lines:
                    lines.append(f"    {ml}")
        
        return "```python\n" + "\n".join(lines) + "\n```"
