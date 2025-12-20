"""
ASCII Table Agent - Creates formatted tables using ASCII characters.

Features:
- Multiple table styles
- Column alignment
- Headers and separators
- Auto-width calculation
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


class ASCIITableAgent(BaseFormattingAgent):
    """
    Specialized agent for ASCII table formatting.
    
    Creates formatted tables with:
    - Clean borders
    - Proper alignment
    - Consistent column widths
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="ASCIITableAgent",
            content_type=ContentType.TABLE,
            max_retries=2,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an ASCII table formatting specialist.

TABLE STYLES:
=============

1. UNICODE STYLE:
   ┌──────────┬──────────┬──────────┐
   │  Header  │  Header  │  Header  │
   ├──────────┼──────────┼──────────┤
   │  Data    │  Data    │  Data    │
   │  Data    │  Data    │  Data    │
   └──────────┴──────────┴──────────┘

2. SIMPLE STYLE:
   +----------+----------+----------+
   |  Header  |  Header  |  Header  |
   +----------+----------+----------+
   |  Data    |  Data    |  Data    |
   +----------+----------+----------+

3. MARKDOWN STYLE:
   | Header | Header | Header |
   |--------|--------|--------|
   | Data   | Data   | Data   |

ALIGNMENT:
- Left: pad right
- Right: pad left  
- Center: pad both

Return tables in code blocks for proper display."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        style = kwargs.get("style", "unicode")
        alignment = kwargs.get("alignment", "center")
        
        return f"""Format this data as an ASCII table.

INPUT:
{content}

STYLE: {style}
ALIGNMENT: {alignment}

Return JSON with:
{{
    "formatted_content": "the table in a code block",
    "row_count": number,
    "column_count": number
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate ASCII table."""
        errors = []
        
        # Check for table structure
        has_separators = any(c in content for c in ['─', '-', '|', '│'])
        if not has_separators:
            errors.append("No table structure found")
        
        # Check row consistency
        lines = [l for l in content.split('\n') if '|' in l or '│' in l]
        if lines:
            col_counts = [l.count('|') + l.count('│') for l in lines]
            if len(set(col_counts)) > 1:
                errors.append("Inconsistent column count across rows")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already a formatted table."""
        table_chars = ['┌', '┬', '┐', '├', '┼', '┤', '└', '┴', '┘', '+']
        return sum(1 for c in table_chars if c in content) >= 2
    
    def create_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        style: str = "unicode",
        alignment: str = "center",
    ) -> AgentResult:
        """
        Create a formatted ASCII table.
        
        Args:
            headers: List of column headers
            rows: List of rows, each row is a list of cell values
            style: "unicode", "simple", or "markdown"
            alignment: "left", "right", or "center"
        """
        if not headers:
            return AgentResult(
                success=False,
                content="",
                original_content="",
                errors=["No headers provided"],
                agent_name=self.config.name,
            )
        
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Add padding
        col_widths = [w + 2 for w in col_widths]
        
        # Style characters
        if style == "unicode":
            chars = {
                "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
                "h": "─", "v": "│",
                "tj": "┬", "bj": "┴", "lj": "├", "rj": "┤", "cross": "┼"
            }
        elif style == "simple":
            chars = {
                "tl": "+", "tr": "+", "bl": "+", "br": "+",
                "h": "-", "v": "|",
                "tj": "+", "bj": "+", "lj": "+", "rj": "+", "cross": "+"
            }
        else:  # markdown
            chars = {"h": "-", "v": "|"}
        
        def align_cell(text: str, width: int) -> str:
            text = str(text)
            if alignment == "left":
                return " " + text.ljust(width - 1)
            elif alignment == "right":
                return text.rjust(width - 1) + " "
            else:  # center
                padding = width - len(text)
                left_pad = padding // 2
                right_pad = padding - left_pad
                return " " * left_pad + text + " " * right_pad
        
        lines = []
        
        if style != "markdown":
            # Top border
            top_line = chars["tl"] + chars["tj"].join(chars["h"] * w for w in col_widths) + chars["tr"]
            lines.append(top_line)
        
        # Header row
        header_cells = [align_cell(h, col_widths[i]) for i, h in enumerate(headers)]
        lines.append(chars["v"] + chars["v"].join(header_cells) + chars["v"])
        
        # Header separator
        if style == "markdown":
            sep_line = "|" + "|".join("-" * w for w in col_widths) + "|"
        else:
            sep_line = chars["lj"] + chars["cross"].join(chars["h"] * w for w in col_widths) + chars["rj"]
        lines.append(sep_line)
        
        # Data rows
        for row in rows:
            # Pad row if needed
            padded_row = list(row) + [""] * (len(headers) - len(row))
            cells = [align_cell(str(c), col_widths[i]) for i, c in enumerate(padded_row[:len(headers)])]
            lines.append(chars["v"] + chars["v"].join(cells) + chars["v"])
        
        if style != "markdown":
            # Bottom border
            bottom_line = chars["bl"] + chars["bj"].join(chars["h"] * w for w in col_widths) + chars["br"]
            lines.append(bottom_line)
        
        content = "```\n" + "\n".join(lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str({"headers": headers, "rows": rows}),
            agent_name=self.config.name,
            metadata={
                "row_count": len(rows) + 1,
                "column_count": len(headers),
                "style": style,
            }
        )
