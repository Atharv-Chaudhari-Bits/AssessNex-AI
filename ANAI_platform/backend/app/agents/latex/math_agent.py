"""
Math Expression Agent - Handles step-by-step mathematical solutions.

Features:
- Multi-step solutions
- Aligned equations
- Explanation with math
- Proper step formatting
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


class MathExpressionAgent(BaseFormattingAgent):
    """
    Specialized agent for multi-step mathematical solutions.
    
    Handles:
    - Step-by-step solutions
    - Aligned equation chains
    - Mixed text and math
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MathExpressionAgent",
            content_type=ContentType.LATEX,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a mathematical solution formatting specialist. Your role is to:

1. FORMAT step-by-step mathematical solutions
2. ALIGN equations properly
3. MIX explanatory text with LaTeX
4. ENSURE clarity and readability

STEP-BY-STEP SOLUTION FORMAT:
=============================

1. NUMBERED STEPS:
   **Step 1:** Set up the equation
   $$ax^2 + bx + c = 0$$
   
   **Step 2:** Apply the quadratic formula
   $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$
   
   **Step 3:** Substitute values
   $$x = \\frac{-5 \\pm \\sqrt{25 - 24}}{2}$$

2. ALIGNED EQUATIONS:
   $$
   \\begin{align}
   2x + 3 &= 11 \\\\
   2x &= 11 - 3 \\\\
   2x &= 8 \\\\
   x &= 4
   \\end{align}
   $$

3. EQUATION CHAINS (for simple derivations):
   $$f(x) = x^2 + 2x + 1 = (x+1)^2$$

4. CASES:
   $$
   f(x) = \\begin{cases}
   x^2 & \\text{if } x \\geq 0 \\\\
   -x^2 & \\text{if } x < 0
   \\end{cases}
   $$

5. MIXED TEXT AND MATH:
   Given that $a = 3$ and $b = 4$, we can find $c$ using:
   $$c = \\sqrt{a^2 + b^2} = \\sqrt{9 + 16} = \\sqrt{25} = 5$$

BEST PRACTICES:
===============
- Number all steps clearly
- Add brief explanations between equations
- Use alignment for multi-step derivations
- Highlight final answers
- Use \\text{} for words in equations

Return formatted solution with proper structure."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        return f"""Format this mathematical solution with proper steps and LaTeX.

INPUT:
{content}

REQUIREMENTS:
- Number each step
- Use proper LaTeX for all math
- Add brief explanations
- Align related equations
- Highlight the final answer

Return JSON with:
{{
    "formatted_content": "the complete formatted solution",
    "step_count": number_of_steps,
    "has_final_answer": true/false
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate math solution."""
        errors = []
        
        # Check LaTeX balance
        if content.count('$$') % 2 != 0:
            errors.append("Unbalanced $$ delimiters")
        
        # Check for step structure
        has_steps = bool(re.search(r'(step|Step|\*\*Step)', content))
        has_numbers = bool(re.search(r'\d[\.\)]', content))
        
        if not has_steps and not has_numbers:
            errors.append("No clear step structure found")
        
        # Check braces
        if content.count('{') != content.count('}'):
            errors.append("Unbalanced braces")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already formatted."""
        has_latex = '$$' in content or '$' in content
        has_structure = 'Step' in content or re.search(r'\d[\.\)]', content)
        return has_latex and has_structure
    
    def create_solution(
        self,
        steps: List[Dict[str, str]],
        final_answer: Optional[str] = None,
    ) -> AgentResult:
        """
        Create a formatted multi-step solution.
        
        Args:
            steps: List of {"explanation": str, "math": str}
            final_answer: Optional final answer to highlight
        """
        lines = []
        
        for i, step in enumerate(steps, 1):
            explanation = step.get("explanation", "")
            math = step.get("math", "")
            
            lines.append(f"**Step {i}:** {explanation}")
            if math:
                lines.append(f"$${math}$$")
            lines.append("")
        
        if final_answer:
            lines.append("**Final Answer:**")
            lines.append(f"$${final_answer}$$")
        
        content = "\n".join(lines)
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(steps),
            agent_name=self.config.name,
            metadata={
                "step_count": len(steps),
                "has_final_answer": final_answer is not None,
            }
        )
    
    def create_aligned_equations(
        self,
        equations: List[str],
        align_at: str = "=",
    ) -> str:
        """Create aligned equation block."""
        lines = ["$$", "\\begin{align}"]
        
        for eq in equations:
            # Add alignment marker
            if align_at in eq:
                eq = eq.replace(align_at, f"&{align_at}", 1)
            lines.append(f"    {eq} \\\\")
        
        lines[-1] = lines[-1].rstrip(" \\\\")  # Remove trailing \\
        lines.extend(["\\end{align}", "$$"])
        
        return "\n".join(lines)
