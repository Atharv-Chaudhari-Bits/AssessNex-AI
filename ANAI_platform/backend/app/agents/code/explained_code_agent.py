"""
Explained Code Agent - Combines code with detailed explanations.

Features:
- Code with inline comments
- Step-by-step explanations
- Line-by-line breakdown
- Summary sections
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


class ExplainedCodeAgent(BaseFormattingAgent):
    """
    Creates code with detailed explanations and comments.
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="ExplainedCodeAgent",
            content_type=ContentType.CODE,
            max_retries=2,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a code explanation specialist. Your role is to:

1. ADD clear comments to code
2. PROVIDE step-by-step explanations
3. EXPLAIN complex logic
4. INCLUDE summary sections

EXPLANATION FORMAT:
===================

1. CODE WITH INLINE COMMENTS:
   ```python
   # Calculate the factorial using recursion
   def factorial(n):
       # Base case: factorial of 0 or 1 is 1
       if n <= 1:
           return 1
       # Recursive case: n * factorial(n-1)
       return n * factorial(n - 1)
   ```

2. BLOCK EXPLANATIONS:
   **Explanation:**
   This function calculates factorial using recursion...

3. LINE-BY-LINE BREAKDOWN:
   | Line | Code | Explanation |
   |------|------|-------------|
   | 1 | def factorial(n): | Function definition... |

4. COMPLEXITY ANALYSIS:
   **Time Complexity:** $O(n)$
   **Space Complexity:** $O(n)$ due to recursion stack

Return code with comprehensive explanations."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        explanation_level = kwargs.get("level", "detailed")
        include_complexity = kwargs.get("complexity", True)
        
        return f"""Add explanations to this code.

INPUT CODE:
{content}

REQUIREMENTS:
- Explanation level: {explanation_level}
- Include complexity analysis: {include_complexity}
- Add inline comments
- Provide summary

Return JSON with:
{{
    "formatted_content": "code with explanations",
    "summary": "brief overview"
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate explained code."""
        errors = []
        
        has_code = '```' in content
        has_explanation = any(x in content.lower() for x in ['explanation', '#', '//'])
        
        if not has_code:
            errors.append("Missing code block")
        if not has_explanation:
            errors.append("Missing explanations")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already has explanations."""
        has_code = '```' in content
        has_comments = '#' in content or '//' in content
        has_explanation = 'explanation' in content.lower()
        return has_code and (has_comments or has_explanation)
    
    def create_explained_code(
        self,
        code: str,
        language: str = "python",
        explanations: List[Dict[str, str]] = None,
        summary: str = None,
        complexity: Dict[str, str] = None,
    ) -> AgentResult:
        """
        Create code with explanations.
        
        Args:
            code: The code to explain
            language: Programming language
            explanations: List of {"line": int, "explanation": str}
            summary: Overall summary
            complexity: {"time": "O(n)", "space": "O(1)"}
        """
        lines = []
        
        # Add summary if provided
        if summary:
            lines.append("**Overview:**")
            lines.append(summary)
            lines.append("")
        
        # Add code block
        lines.append(f"```{language}")
        
        code_lines = code.strip().split('\n')
        
        # Add explanations as comments if provided
        if explanations:
            exp_map = {e.get("line", 0): e.get("explanation", "") for e in explanations}
            for i, code_line in enumerate(code_lines, 1):
                if i in exp_map:
                    comment_char = "#" if language == "python" else "//"
                    lines.append(f"{comment_char} {exp_map[i]}")
                lines.append(code_line)
        else:
            lines.extend(code_lines)
        
        lines.append("```")
        
        # Add complexity if provided
        if complexity:
            lines.append("")
            lines.append("**Complexity Analysis:**")
            if "time" in complexity:
                lines.append(f"- Time Complexity: ${complexity['time']}$")
            if "space" in complexity:
                lines.append(f"- Space Complexity: ${complexity['space']}$")
        
        content = "\n".join(lines)
        
        return AgentResult(
            success=True,
            content=content,
            original_content=code,
            agent_name=self.config.name,
            metadata={
                "language": language,
                "has_explanations": explanations is not None,
                "has_complexity": complexity is not None,
            }
        )
