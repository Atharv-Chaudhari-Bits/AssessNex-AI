"""
ASCII Flowchart Agent - Creates flowcharts using box drawing characters.

Features:
- Box drawing characters (┌ ─ ┐ │ └ ┘ etc.)
- Multiple arrow styles
- Decision diamonds
- Proper alignment
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


class ASCIIFlowchartAgent(BaseFormattingAgent):
    """
    Specialized agent for ASCII flowchart diagrams.
    
    Creates text-based flowcharts using:
    - Box drawing characters
    - Arrow indicators
    - Decision diamonds
    - Proper spacing and alignment
    """
    
    # Box drawing characters
    BOX_CHARS = {
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "horizontal": "─",
        "vertical": "│",
        "t_down": "┬",
        "t_up": "┴",
        "t_right": "├",
        "t_left": "┤",
        "cross": "┼",
    }
    
    # Arrow characters
    ARROWS = {
        "down": "▼",
        "up": "▲",
        "left": "◄",
        "right": "►",
        "line_down": "│",
        "line_right": "──►",
        "line_left": "◄──",
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="ASCIIFlowchartAgent",
            content_type=ContentType.ASCII,
            max_retries=3,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert ASCII flowchart specialist. Your role is to:

1. CREATE ASCII flowcharts using box drawing characters
2. VALIDATE and FIX existing ASCII diagrams
3. ENSURE proper alignment and spacing
4. USE consistent styling throughout

ASCII FLOWCHART SYNTAX RULES:
=============================

1. BOX DRAWING CHARACTERS:
   ┌──────────────┐
   │   Process    │
   └──────────────┘
   
   Use these characters:
   ┌ ─ ┐ │ └ ┘ ├ ┤ ┬ ┴ ┼

2. ARROW CHARACTERS:
   Down:  │ or ▼
   Up:    │ or ▲  
   Right: ──► or →
   Left:  ◄── or ←

3. DECISION DIAMONDS (approximation):
        ┌───┐
       /     \\
      │ Yes? │
       \\     /
        └───┘
   
   OR simpler:
   ┌─────────┐
   │ Decision│
   └────┬────┘
    Yes │ No
        ▼

4. VERTICAL FLOW:
   ┌──────────┐
   │  Start   │
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │ Process  │
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │   End    │
   └──────────┘

5. HORIZONTAL FLOW:
   ┌──────┐     ┌──────┐     ┌──────┐
   │ A    │ ──► │ B    │ ──► │ C    │
   └──────┘     └──────┘     └──────┘

6. BRANCHING:
        ┌──────────┐
        │ Decision │
        └────┬─────┘
             │
        ┌────┴────┐
        │         │
        ▼         ▼
   ┌────────┐ ┌────────┐
   │  Yes   │ │   No   │
   └────────┘ └────────┘

7. SIMPLE ALTERNATIVE (+ - |):
   +----------+
   |  Start   |
   +----+-----+
        |
        v
   +----------+
   | Process  |
   +----------+

BEST PRACTICES:
===============
- Keep consistent box widths
- Align boxes properly
- Use clear arrow directions
- Add labels to branches
- Limit to 80 characters width
- Use monospace font display

Return content in a code block for proper display."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        style = kwargs.get("style", "unicode")  # unicode or simple
        direction = kwargs.get("direction", "vertical")
        max_width = kwargs.get("max_width", 80)
        
        return f"""Convert the following flow description into an ASCII flowchart.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Style: {style} (unicode = ┌┐└┘│─, simple = +-|)
- Direction: {direction}
- Maximum width: {max_width} characters
- Use arrows to show flow direction
- Add labels where needed

EXPECTED OUTPUT FORMAT:
```
┌─────────────────┐
│     Start       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Process Step   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Check?  │
    └────┬────┘
    Yes  │  No
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ Path A│ │ Path B│
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│      End        │
└─────────────────┘
```

Return a JSON object with:
{{
    "formatted_content": "the complete ASCII diagram in a code block",
    "diagram_type": "ascii_flowchart",
    "box_count": number_of_boxes,
    "width": actual_width,
    "height": number_of_lines,
    "validation_notes": ["any notes"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate ASCII flowchart."""
        errors = []
        
        # Check for box-like structures
        has_boxes = any(char in content for char in ['┌', '┐', '└', '┘', '+'])
        if not has_boxes:
            errors.append("No box structures found")
        
        # Check for flow indicators
        has_arrows = any(char in content for char in ['▼', '▲', '►', '◄', '→', '←', 'v', '^', '>', '<', '|', '│'])
        if not has_arrows:
            errors.append("No flow indicators (arrows) found")
        
        # Check line width consistency
        lines = content.split('\n')
        if lines:
            # Filter non-empty lines
            non_empty = [l for l in lines if l.strip()]
            if non_empty:
                widths = set(len(l.rstrip()) for l in non_empty if any(c in l for c in ['─', '-', '│', '|']))
                # Some variation is okay, but extreme variation suggests issues
                if widths and max(widths) - min(widths) > 30:
                    errors.append("Inconsistent line widths (possible alignment issue)")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already an ASCII flowchart."""
        box_chars = ['┌', '┐', '└', '┘', '+', '─', '|', '│']
        has_structure = sum(1 for c in box_chars if c in content) >= 3
        return has_structure
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """Create a basic ASCII flowchart from text."""
        style = kwargs.get("style", "unicode")
        
        if style == "unicode":
            tl, tr, bl, br, h, v = "┌", "┐", "└", "┘", "─", "│"
        else:
            tl, tr, bl, br, h, v = "+", "+", "+", "+", "-", "|"
        
        lines = content.strip().split('\n')
        steps = [line.strip() for line in lines if line.strip()]
        
        if not steps:
            return content
        
        # Find max width
        max_len = max(len(s) for s in steps)
        box_width = max_len + 4
        
        result = []
        for i, step in enumerate(steps):
            # Top of box
            result.append(f"{tl}{h * box_width}{tr}")
            # Content (centered)
            padding = box_width - len(step)
            left_pad = padding // 2
            right_pad = padding - left_pad
            result.append(f"{v}{' ' * left_pad}{step}{' ' * right_pad}{v}")
            # Bottom of box
            result.append(f"{bl}{h * box_width}{br}")
            
            # Arrow to next (if not last)
            if i < len(steps) - 1:
                center = (box_width + 2) // 2
                result.append(" " * center + v)
                result.append(" " * center + "▼" if style == "unicode" else " " * center + "v")
        
        return "```\n" + "\n".join(result) + "\n```"
    
    def create_flowchart(
        self,
        steps: List[str],
        style: str = "unicode",
        direction: str = "vertical",
    ) -> AgentResult:
        """
        Create an ASCII flowchart from steps.
        
        Args:
            steps: List of step descriptions
            style: "unicode" or "simple"
            direction: "vertical" or "horizontal"
            
        Returns:
            AgentResult with the generated flowchart
        """
        content = self._get_best_effort("\n".join(steps), style=style)
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(steps),
            agent_name=self.config.name,
            metadata={
                "style": style,
                "direction": direction,
                "step_count": len(steps),
            }
        )
