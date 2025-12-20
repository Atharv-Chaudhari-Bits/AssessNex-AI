"""
Block LaTeX Agent - Specialized agent for display/block mathematical expressions.

Features:
- Block math ($$...$$)
- Complex equations
- Fractions and integrals
- Sums and products
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


class BlockLaTeXAgent(BaseFormattingAgent):
    """
    Specialized agent for block/display LaTeX expressions.
    
    Handles:
    - Complex mathematical expressions
    - Multi-line equations
    - Fractions, integrals, sums
    - Matrices and arrays
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="BlockLaTeXAgent",
            content_type=ContentType.LATEX,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a LaTeX display math specialist. Your role is to:

1. CONVERT complex math to block LaTeX ($$...$$)
2. VALIDATE block LaTeX syntax
3. FORMAT equations for clear display
4. USE appropriate LaTeX environments

BLOCK LATEX RULES:
==================

1. DELIMITERS:
   $$expression$$  - Display/block math

2. FRACTIONS:
   $$\\frac{numerator}{denominator}$$
   $$\\frac{a + b}{c - d}$$
   $$\\frac{\\partial f}{\\partial x}$$  - Partial derivatives

3. ROOTS:
   $$\\sqrt{x}$$
   $$\\sqrt[n]{x}$$  - nth root
   $$\\sqrt{a^2 + b^2}$$

4. SUMS AND PRODUCTS:
   $$\\sum_{i=1}^{n} x_i$$
   $$\\sum_{k=0}^{\\infty} a_k$$
   $$\\prod_{i=1}^{n} x_i$$

5. INTEGRALS:
   $$\\int_a^b f(x) dx$$
   $$\\int_{-\\infty}^{\\infty} e^{-x^2} dx$$
   $$\\iint_D f(x,y) dA$$  - Double integral
   $$\\oint_C F \\cdot dr$$  - Line integral

6. LIMITS:
   $$\\lim_{x \\to \\infty} f(x)$$
   $$\\lim_{n \\to \\infty} \\left(1 + \\frac{1}{n}\\right)^n = e$$

7. FUNCTIONS:
   $$\\sin(x)$$, $$\\cos(x)$$, $$\\tan(x)$$
   $$\\log(x)$$, $$\\ln(x)$$, $$\\exp(x)$$

8. BRACKETS (auto-sizing):
   $$\\left( \\frac{a}{b} \\right)$$
   $$\\left[ \\sum_{i} x_i \\right]$$
   $$\\left\\{ x : x > 0 \\right\\}$$
   $$\\left| x \\right|$$  - Absolute value

9. MATRICES:
   $$\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$$  - Parentheses
   $$\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}$$  - Brackets
   $$\\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix}$$  - Determinant

10. SPECIAL NOTATIONS:
    $$O(n^2)$$, $$\\Theta(n\\log n)$$, $$\\Omega(n)$$  - Big-O notation
    $$\\binom{n}{k}$$  - Binomial coefficient
    $$\\forall x \\in S$$, $$\\exists y$$  - Quantifiers

BEST PRACTICES:
===============
- Use \\left and \\right for auto-sizing brackets
- Add spacing: \\, (thin), \\; (medium), \\quad (large)
- Break long equations into multiple lines
- Use \\text{} for text within equations

Return the complete formatted expression."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        return f"""Convert this mathematical content to block LaTeX.

INPUT:
{content}

REQUIREMENTS:
- Use $$...$$ for display math
- Use appropriate LaTeX commands
- Add proper spacing for readability
- Use \\left/\\right for auto-sizing brackets

EXAMPLES:
- "integral from 0 to infinity of e^(-x) dx" →
  $$\\int_0^{{\\infty}} e^{{-x}} dx$$

- "sum of x_i for i=1 to n" →
  $$\\sum_{{i=1}}^{{n}} x_i$$

- "fraction a+b over c-d" →
  $$\\frac{{a+b}}{{c-d}}$$

Return JSON with:
{{
    "formatted_content": "the block LaTeX expression",
    "complexity": "simple/medium/complex"
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate block LaTeX."""
        errors = []
        
        # Check for $$ delimiters
        double_dollar_count = content.count('$$')
        if double_dollar_count % 2 != 0:
            errors.append("Unbalanced $$ delimiters")
        
        # Check for unclosed braces
        brace_count = content.count('{') - content.count('}')
        if brace_count != 0:
            errors.append(f"Unbalanced braces: {'+' if brace_count > 0 else ''}{brace_count}")
        
        # Check for \\begin without \\end
        begin_count = len(re.findall(r'\\begin\{(\w+)\}', content))
        end_count = len(re.findall(r'\\end\{(\w+)\}', content))
        if begin_count != end_count:
            errors.append("Unbalanced \\begin/\\end environments")
        
        # Check for \\left without \\right
        left_count = content.count('\\left')
        right_count = content.count('\\right')
        if left_count != right_count:
            errors.append("Unbalanced \\left/\\right delimiters")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content already has block LaTeX."""
        return '$$' in content
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """Convert to block LaTeX."""
        result = content.strip()
        
        # Common conversions
        replacements = [
            # Fractions
            (r'(\w+)\s*/\s*(\w+)', r'\\frac{\1}{\2}'),
            # Square roots
            (r'sqrt\(([^)]+)\)', r'\\sqrt{\1}'),
            # Powers
            (r'\^(\d+)', r'^{\1}'),
            # Subscripts
            (r'_(\d+)', r'_{\1}'),
        ]
        
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)
        
        # Wrap in $$ if not already
        if not result.startswith('$$'):
            result = f'$$\n{result}\n$$'
        
        return result
    
    def format_block(self, expression: str) -> str:
        """Format a single expression as block LaTeX."""
        result = expression.strip()
        
        # Remove inline $ if present
        if result.startswith('$') and not result.startswith('$$'):
            result = result[1:]
        if result.endswith('$') and not result.endswith('$$'):
            result = result[:-1]
        
        # Wrap in $$
        if not result.startswith('$$'):
            result = f'$$\n{result}\n$$'
        
        return result
    
    def create_fraction(self, numerator: str, denominator: str) -> str:
        """Create a LaTeX fraction."""
        return f'$$\\frac{{{numerator}}}{{{denominator}}}$$'
    
    def create_sum(self, expression: str, lower: str = "i=1", upper: str = "n") -> str:
        """Create a LaTeX sum."""
        return f'$$\\sum_{{{lower}}}^{{{upper}}} {expression}$$'
    
    def create_integral(self, expression: str, lower: str = "a", upper: str = "b", var: str = "x") -> str:
        """Create a LaTeX integral."""
        return f'$$\\int_{{{lower}}}^{{{upper}}} {expression} \\, d{var}$$'
