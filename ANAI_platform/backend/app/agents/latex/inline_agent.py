"""
Inline LaTeX Agent - Specialized agent for inline mathematical expressions.

Features:
- Simple inline math ($...$)
- Variable formatting
- Simple operations
- Greek letters
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


class InlineLaTeXAgent(BaseFormattingAgent):
    """
    Specialized agent for inline LaTeX expressions.
    
    Handles:
    - Simple mathematical expressions
    - Variable and constant formatting
    - Basic operators
    - Greek letters and symbols
    """
    
    # Common LaTeX commands for inline use
    INLINE_COMMANDS = {
        # Greek letters
        "alpha": "\\alpha", "beta": "\\beta", "gamma": "\\gamma",
        "delta": "\\delta", "epsilon": "\\epsilon", "theta": "\\theta",
        "lambda": "\\lambda", "mu": "\\mu", "pi": "\\pi",
        "sigma": "\\sigma", "omega": "\\omega", "phi": "\\phi",
        # Operators
        "times": "\\times", "div": "\\div", "cdot": "\\cdot",
        "pm": "\\pm", "mp": "\\mp",
        # Relations
        "leq": "\\leq", "geq": "\\geq", "neq": "\\neq",
        "approx": "\\approx", "equiv": "\\equiv",
        # Sets
        "in": "\\in", "notin": "\\notin", "subset": "\\subset",
        # Misc
        "infty": "\\infty", "partial": "\\partial", "nabla": "\\nabla",
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="InlineLaTeXAgent",
            content_type=ContentType.LATEX,
            max_retries=2,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a LaTeX inline math specialist. Your role is to:

1. CONVERT plain text math to inline LaTeX ($...$)
2. VALIDATE inline LaTeX syntax
3. USE appropriate LaTeX commands for clarity
4. KEEP inline expressions simple and readable

INLINE LATEX RULES:
===================

1. DELIMITERS:
   $expression$  - Inline math
   
2. VARIABLES AND CONSTANTS:
   $x$, $y$, $n$, $i$ - Single variables
   $x_1$, $x_n$ - Subscripts
   $x^2$, $x^n$ - Superscripts
   $x_i^2$ - Both

3. BASIC OPERATIONS:
   $a + b$, $a - b$
   $a \\times b$, $a \\cdot b$ (multiplication)
   $\\frac{a}{b}$ or $a / b$ (division)

4. COMPARISONS:
   $x = 5$, $x \\neq 0$
   $x < y$, $x > y$
   $x \\leq y$, $x \\geq y$
   $x \\approx y$

5. GREEK LETTERS:
   $\\alpha$, $\\beta$, $\\gamma$, $\\delta$
   $\\theta$, $\\lambda$, $\\mu$, $\\pi$
   $\\sigma$, $\\omega$, $\\phi$

6. SETS AND LOGIC:
   $x \\in S$, $x \\notin S$
   $A \\subset B$, $A \\cup B$, $A \\cap B$

7. SPECIAL SYMBOLS:
   $\\infty$ - Infinity
   $\\partial$ - Partial derivative
   $\\nabla$ - Nabla/del

WHEN TO USE INLINE vs BLOCK:
- Inline: Simple expressions that flow with text
- Block: Complex fractions, integrals, sums, matrices

Return ONLY the formatted text with inline LaTeX."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        return f"""Convert mathematical expressions in this text to inline LaTeX.

INPUT:
{content}

RULES:
- Wrap math expressions in $...$
- Keep expressions simple (use block $$..$$ for complex ones)
- Use \\times for multiplication, not *
- Use proper LaTeX commands for symbols

EXAMPLES:
- "x equals 5" → "$x = 5$"
- "a squared" → "$a^2$"
- "sum from i=1 to n" → "$\\sum_{{i=1}}^{{n}}$"
- "square root of x" → "$\\sqrt{{x}}$"

Return JSON with:
{{
    "formatted_content": "text with inline LaTeX",
    "latex_count": number_of_latex_expressions
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate inline LaTeX."""
        errors = []
        
        # Count $ signs (should be even for balanced)
        dollar_count = content.count('$') - content.count('\\$')
        if dollar_count % 2 != 0:
            errors.append("Unbalanced $ delimiters")
        
        # Check for unclosed braces within $...$
        inline_pattern = r'\$([^\$]+)\$'
        for match in re.finditer(inline_pattern, content):
            expr = match.group(1)
            if expr.count('{') != expr.count('}'):
                errors.append(f"Unbalanced braces in: ${expr[:30]}...$")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content already has inline LaTeX."""
        # Has balanced $ and contains typical LaTeX
        has_dollars = '$' in content
        has_latex = any(cmd in content for cmd in ['\\frac', '\\sum', '\\alpha', '\\times', '^', '_'])
        return has_dollars and has_latex
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """Convert obvious math to inline LaTeX."""
        result = content
        
        # Simple patterns to convert
        patterns = [
            # Variables with subscripts: x1, x_1 → $x_1$
            (r'\b([a-zA-Z])(\d)\b', r'$\1_\2$'),
            # Powers: x^2, x**2 → $x^2$
            (r'\b([a-zA-Z])\^(\d+)\b', r'$\1^\2$'),
            (r'\b([a-zA-Z])\*\*(\d+)\b', r'$\1^\2$'),
            # Simple equations not already in $: x = 5
            (r'(?<!\$)\b([a-zA-Z])\s*=\s*(\d+)\b(?!\$)', r'$\1 = \2$'),
        ]
        
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def format_inline(self, expression: str) -> str:
        """Format a single expression as inline LaTeX."""
        # Already wrapped
        if expression.startswith('$') and expression.endswith('$'):
            return expression
        
        # Apply common replacements
        formatted = expression
        formatted = formatted.replace('*', ' \\times ')
        formatted = formatted.replace('>=', ' \\geq ')
        formatted = formatted.replace('<=', ' \\leq ')
        formatted = formatted.replace('!=', ' \\neq ')
        formatted = formatted.replace('~=', ' \\approx ')
        
        # Wrap in $ if not already
        if not formatted.startswith('$'):
            formatted = f'${formatted.strip()}$'
        
        return formatted
