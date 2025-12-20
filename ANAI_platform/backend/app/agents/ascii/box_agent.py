"""
ASCII Box Agent - Creates simple box diagrams using ASCII characters.

Features:
- Simple rectangular boxes
- Labels and descriptions
- Connection lines
- Multiple box styles
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


class ASCIIBoxAgent(BaseFormattingAgent):
    """
    Specialized agent for ASCII box diagrams.
    
    Creates simple box-based diagrams for:
    - Component diagrams
    - Architecture overviews
    - Simple layouts
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="ASCIIBoxAgent",
            content_type=ContentType.ASCII,
            max_retries=2,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert ASCII box diagram specialist. Create clean, aligned box diagrams.

ASCII BOX STYLES:
=================

1. UNICODE STYLE:
   ┌───────────────┐
   │    Label      │
   │  Description  │
   └───────────────┘

2. SIMPLE STYLE:
   +---------------+
   |    Label      |
   |  Description  |
   +---------------+

3. DOUBLE LINE:
   ╔═══════════════╗
   ║    Label      ║
   ║  Description  ║
   ╚═══════════════╝

4. CONNECTIONS:
   ┌───────┐     ┌───────┐
   │   A   │ ──► │   B   │
   └───────┘     └───────┘
        │
        ▼
   ┌───────┐
   │   C   │
   └───────┘

5. NESTED BOXES:
   ┌─────────────────────────┐
   │  Container             │
   │  ┌─────┐   ┌─────┐    │
   │  │ A   │──►│ B   │    │
   │  └─────┘   └─────┘    │
   └─────────────────────────┘

BEST PRACTICES:
- Consistent box widths in groups
- Clear alignment
- Readable labels
- Proper spacing between boxes

Return content in a code block."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        style = kwargs.get("style", "unicode")
        
        return f"""Convert this into an ASCII box diagram.

INPUT:
{content}

STYLE: {style}
- unicode: ┌┐└┘│─
- simple: +-|
- double: ╔╗╚╝║═

Create clean, aligned boxes with proper connections.

Return JSON with:
{{
    "formatted_content": "the diagram in a code block",
    "box_count": number
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate ASCII box diagram."""
        errors = []
        
        box_chars = ['┌', '┐', '└', '┘', '+', '╔', '╗', '╚', '╝']
        has_boxes = any(c in content for c in box_chars)
        
        if not has_boxes:
            errors.append("No box structures found")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already formatted."""
        box_chars = ['┌', '┐', '└', '┘', '+', '╔', '╗', '╚', '╝']
        return sum(1 for c in box_chars if c in content) >= 2
    
    def create_box(
        self,
        label: str,
        description: str = "",
        style: str = "unicode",
        width: Optional[int] = None,
    ) -> str:
        """Create a single ASCII box."""
        if style == "unicode":
            tl, tr, bl, br, h, v = "┌", "┐", "└", "┘", "─", "│"
        elif style == "double":
            tl, tr, bl, br, h, v = "╔", "╗", "╚", "╝", "═", "║"
        else:
            tl, tr, bl, br, h, v = "+", "+", "+", "+", "-", "|"
        
        content_lines = [label]
        if description:
            content_lines.extend(description.split('\n'))
        
        if width is None:
            width = max(len(line) for line in content_lines) + 4
        
        lines = [f"{tl}{h * width}{tr}"]
        for line in content_lines:
            padding = width - len(line)
            left_pad = padding // 2
            right_pad = padding - left_pad
            lines.append(f"{v}{' ' * left_pad}{line}{' ' * right_pad}{v}")
        lines.append(f"{bl}{h * width}{br}")
        
        return "\n".join(lines)
    
    def create_box_diagram(
        self,
        boxes: List[Dict[str, str]],
        layout: str = "horizontal",
        style: str = "unicode",
    ) -> AgentResult:
        """
        Create a diagram with multiple boxes.
        
        Args:
            boxes: List of {"label": str, "description": str}
            layout: "horizontal" or "vertical"
            style: "unicode", "simple", or "double"
        """
        if not boxes:
            return AgentResult(
                success=False,
                content="",
                original_content="",
                errors=["No boxes provided"],
                agent_name=self.config.name,
            )
        
        box_strings = [
            self.create_box(
                b.get("label", ""),
                b.get("description", ""),
                style
            )
            for b in boxes
        ]
        
        if layout == "horizontal":
            # Combine boxes side by side
            all_lines = [b.split('\n') for b in box_strings]
            max_height = max(len(lines) for lines in all_lines)
            
            # Pad to same height
            for lines in all_lines:
                width = len(lines[0]) if lines else 0
                while len(lines) < max_height:
                    lines.append(" " * width)
            
            # Join horizontally
            result_lines = []
            for i in range(max_height):
                row_parts = [lines[i] for lines in all_lines]
                result_lines.append("  ".join(row_parts))
            
            content = "```\n" + "\n".join(result_lines) + "\n```"
        else:
            # Stack vertically with arrows
            arrow = "     │\n     ▼" if style == "unicode" else "     |\n     v"
            content = "```\n" + f"\n{arrow}\n".join(box_strings) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(boxes),
            agent_name=self.config.name,
            metadata={
                "box_count": len(boxes),
                "layout": layout,
                "style": style,
            }
        )
