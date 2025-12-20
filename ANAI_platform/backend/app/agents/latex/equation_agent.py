"""
Equation Array Agent - Handles arrays and matrices in LaTeX.

Features:
- Matrices (pmatrix, bmatrix, vmatrix)
- Arrays with alignment
- Systems of equations
- Augmented matrices
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


class EquationArrayAgent(BaseFormattingAgent):
    """
    Specialized agent for LaTeX arrays and matrices.
    
    Handles:
    - Various matrix types
    - Equation systems
    - Tables within math
    """
    
    # Matrix types
    MATRIX_TYPES = {
        "pmatrix": ("(", ")"),   # Parentheses
        "bmatrix": ("[", "]"),   # Brackets
        "Bmatrix": ("{", "}"),   # Braces
        "vmatrix": ("|", "|"),   # Vertical bars (determinant)
        "Vmatrix": ("||", "||"), # Double bars (norm)
        "matrix": ("", ""),      # No delimiters
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="EquationArrayAgent",
            content_type=ContentType.LATEX,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a LaTeX matrix and array specialist. Your role is to:

1. CREATE properly formatted matrices and arrays
2. VALIDATE matrix/array syntax
3. HANDLE systems of equations
4. FORMAT tables within math mode

MATRIX AND ARRAY RULES:
=======================

1. MATRIX TYPES:
   - pmatrix: parentheses ( )
   - bmatrix: brackets [ ]
   - Bmatrix: braces { }
   - vmatrix: vertical bars | | (determinant)
   - Vmatrix: double bars || || (norm)
   - matrix: no delimiters

2. BASIC MATRIX:
   $$
   \\begin{pmatrix}
   a & b \\\\
   c & d
   \\end{pmatrix}
   $$

3. LARGER MATRIX:
   $$
   A = \\begin{bmatrix}
   1 & 2 & 3 \\\\
   4 & 5 & 6 \\\\
   7 & 8 & 9
   \\end{bmatrix}
   $$

4. AUGMENTED MATRIX (for systems):
   $$
   \\left[
   \\begin{array}{ccc|c}
   1 & 2 & 3 & 4 \\\\
   5 & 6 & 7 & 8 \\\\
   9 & 10 & 11 & 12
   \\end{array}
   \\right]
   $$

5. SYSTEM OF EQUATIONS:
   $$
   \\begin{cases}
   2x + 3y = 5 \\\\
   4x - y = 3
   \\end{cases}
   $$

6. ARRAY WITH ALIGNMENT:
   $$
   \\begin{array}{lcr}
   \\text{left} & \\text{center} & \\text{right} \\\\
   a & b & c
   \\end{array}
   $$
   
   Column specs: l (left), c (center), r (right)

7. DETERMINANT:
   $$
   \\det(A) = \\begin{vmatrix}
   a & b \\\\
   c & d
   \\end{vmatrix} = ad - bc
   $$

8. IDENTITY MATRIX:
   $$
   I_n = \\begin{pmatrix}
   1 & 0 & \\cdots & 0 \\\\
   0 & 1 & \\cdots & 0 \\\\
   \\vdots & \\vdots & \\ddots & \\vdots \\\\
   0 & 0 & \\cdots & 1
   \\end{pmatrix}
   $$

BEST PRACTICES:
===============
- Use appropriate matrix type for context
- Align columns consistently
- Use \\cdots, \\vdots, \\ddots for ellipsis
- Name matrices with uppercase letters
- Use & for column separation, \\\\ for row separation

Return properly formatted LaTeX."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        matrix_type = kwargs.get("matrix_type", "bmatrix")
        
        return f"""Convert this to a LaTeX matrix or array.

INPUT:
{content}

MATRIX TYPE: {matrix_type}

Return JSON with:
{{
    "formatted_content": "the LaTeX matrix",
    "rows": number_of_rows,
    "columns": number_of_columns
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate matrix/array LaTeX."""
        errors = []
        
        # Check for begin/end balance
        begin_count = len(re.findall(r'\\begin\{(\w+)\}', content))
        end_count = len(re.findall(r'\\end\{(\w+)\}', content))
        
        if begin_count != end_count:
            errors.append("Unbalanced \\begin/\\end")
        
        # Check brace balance
        if content.count('{') != content.count('}'):
            errors.append("Unbalanced braces")
        
        # Check for consistent columns in matrix
        env_match = re.search(r'\\begin\{(\w*matrix)\}([\s\S]*?)\\end\{\1\}', content)
        if env_match:
            matrix_content = env_match.group(2)
            rows = matrix_content.split('\\\\')
            col_counts = [row.count('&') + 1 for row in rows if row.strip()]
            if len(set(col_counts)) > 1:
                errors.append("Inconsistent column count in matrix rows")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already a matrix/array."""
        return '\\begin{' in content and ('matrix' in content or 'array' in content)
    
    def create_matrix(
        self,
        data: List[List[Any]],
        matrix_type: str = "bmatrix",
        name: Optional[str] = None,
    ) -> AgentResult:
        """
        Create a LaTeX matrix.
        
        Args:
            data: 2D list of values
            matrix_type: Type of matrix (pmatrix, bmatrix, etc.)
            name: Optional matrix name (A = ...)
        """
        if not data or not data[0]:
            return AgentResult(
                success=False,
                content="",
                original_content="",
                errors=["Empty matrix data"],
                agent_name=self.config.name,
            )
        
        rows = len(data)
        cols = len(data[0])
        
        lines = ["$$"]
        if name:
            lines.append(f"{name} = ")
        
        lines.append(f"\\begin{{{matrix_type}}}")
        
        for i, row in enumerate(data):
            # Pad row if needed
            padded = list(row) + [""] * (cols - len(row))
            row_str = " & ".join(str(x) for x in padded[:cols])
            if i < rows - 1:
                row_str += " \\\\"
            lines.append(row_str)
        
        lines.append(f"\\end{{{matrix_type}}}")
        lines.append("$$")
        
        content = "\n".join(lines)
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(data),
            agent_name=self.config.name,
            metadata={
                "rows": rows,
                "columns": cols,
                "matrix_type": matrix_type,
            }
        )
    
    def create_augmented_matrix(
        self,
        coefficients: List[List[Any]],
        constants: List[Any],
    ) -> AgentResult:
        """Create an augmented matrix for systems of equations."""
        if not coefficients:
            return AgentResult(
                success=False,
                content="",
                original_content="",
                errors=["Empty coefficient matrix"],
                agent_name=self.config.name,
            )
        
        rows = len(coefficients)
        cols = len(coefficients[0])
        
        # Column specification with vertical bar
        col_spec = "c" * cols + "|c"
        
        lines = [
            "$$",
            "\\left[",
            f"\\begin{{array}}{{{col_spec}}}"
        ]
        
        for i, row in enumerate(coefficients):
            const = constants[i] if i < len(constants) else ""
            row_str = " & ".join(str(x) for x in row) + f" & {const}"
            if i < rows - 1:
                row_str += " \\\\"
            lines.append(row_str)
        
        lines.extend([
            "\\end{array}",
            "\\right]",
            "$$"
        ])
        
        content = "\n".join(lines)
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str({"coefficients": coefficients, "constants": constants}),
            agent_name=self.config.name,
            metadata={
                "rows": rows,
                "columns": cols + 1,
                "type": "augmented",
            }
        )
    
    def create_system(
        self,
        equations: List[str],
    ) -> AgentResult:
        """Create a system of equations using cases."""
        if not equations:
            return AgentResult(
                success=False,
                content="",
                original_content="",
                errors=["No equations provided"],
                agent_name=self.config.name,
            )
        
        lines = [
            "$$",
            "\\begin{cases}"
        ]
        
        for i, eq in enumerate(equations):
            if i < len(equations) - 1:
                lines.append(f"{eq} \\\\")
            else:
                lines.append(eq)
        
        lines.extend([
            "\\end{cases}",
            "$$"
        ])
        
        content = "\n".join(lines)
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(equations),
            agent_name=self.config.name,
            metadata={
                "equation_count": len(equations),
            }
        )
