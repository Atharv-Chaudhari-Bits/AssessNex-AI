"""
Mermaid Pie Chart Agent - Specialized agent for pie chart diagrams.

Supports:
- Simple pie charts
- Custom titles
- Value labels
- Percentage display
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


class MermaidPieAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js pie charts.
    
    Creates pie charts showing:
    - Data distribution
    - Percentage breakdown
    - Category comparisons
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidPieAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js pie chart specialist. Your role is to:

1. CREATE valid Mermaid pie charts from data
2. VALIDATE and FIX existing pie chart syntax
3. PRESENT data clearly with labels

MERMAID PIE CHART SYNTAX RULES:
===============================

1. DECLARATION:
   pie

2. TITLE (optional):
   pie title Chart Title
   
   OR with showData:
   pie showData title Chart Title

3. DATA ENTRIES:
   "Label" : value
   
   Example:
   pie title Browser Market Share
       "Chrome" : 65
       "Firefox" : 15
       "Safari" : 12
       "Edge" : 5
       "Other" : 3

4. SHOW DATA:
   pie showData
   Shows the actual values on the chart

5. THEME:
   %%{init: {'theme': 'base', 'themeVariables': { 'pie1': '#ff0000'}}}%%
   pie
       "Category" : 100

BEST PRACTICES:
===============
- Keep labels short and clear
- Limit to 5-7 categories
- Values should be positive numbers
- Use showData for numerical display
- Consider grouping small values as "Other"
- Use meaningful category names

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        show_data = kwargs.get("show_data", True)
        title = kwargs.get("title", "")
        
        return f"""Convert the following data into a Mermaid pie chart.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Show data values: {show_data}
- Title: {title if title else '(derive from content)'}
- Use clear, concise labels
- Values should be numeric

EXPECTED OUTPUT FORMAT:
```mermaid
pie {'showData ' if show_data else ''}title {title if title else 'Data Distribution'}
    "Category A" : 40
    "Category B" : 30
    "Category C" : 20
    "Category D" : 10
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "pie",
    "category_count": number_of_categories,
    "total_value": sum_of_all_values,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid pie chart syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if not content.strip().startswith('pie'):
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any(line.strip().startswith('pie') for line in lines[:2]):
            errors.append("Missing 'pie' declaration")
        
        # Check for data entries
        data_pattern = r'"[^"]+"\s*:\s*\d+'
        has_data = any(re.search(data_pattern, line) for line in lines)
        
        if not has_data:
            errors.append("No data entries found (use format: \"Label\" : value)")
        
        # Validate data entry syntax
        for line in lines:
            if ':' in line and '"' in line:
                if not re.search(data_pattern, line):
                    errors.append(f"Invalid data entry syntax: {line[:50]}")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid pie chart."""
        if '```mermaid' not in content.lower() and not content.strip().startswith('pie'):
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def create_pie_chart(
        self,
        title: str,
        data: Dict[str, float],
        show_data: bool = True,
    ) -> AgentResult:
        """
        Create a pie chart from data.
        
        Args:
            title: Chart title
            data: Dict mapping labels to values
            show_data: Whether to show data values
            
        Returns:
            AgentResult with the generated chart
        """
        show_data_str = "showData " if show_data else ""
        diagram_lines = [f"pie {show_data_str}title {title}"]
        
        for label, value in data.items():
            diagram_lines.append(f'    "{label}" : {value}')
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(data),
            agent_name=self.config.name,
            metadata={
                "category_count": len(data),
                "total_value": sum(data.values()),
            }
        )
