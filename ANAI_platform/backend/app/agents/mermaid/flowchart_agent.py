"""
Mermaid Flowchart Agent - Specialized agent for creating and validating flowcharts.

Supports:
- Top-to-bottom (TD/TB)
- Bottom-to-top (BT)
- Left-to-right (LR)
- Right-to-left (RL)
- Various node shapes
- Subgraphs
- Styling
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


class MermaidFlowchartAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js flowchart diagrams.
    
    Creates interactive flowcharts with:
    - Multiple direction support (TD, TB, BT, LR, RL)
    - Various node shapes (rectangles, diamonds, circles, etc.)
    - Arrow types (solid, dotted, with labels)
    - Subgraphs for grouping
    - Styling and theming
    """
    
    # Node shape syntax
    NODE_SHAPES = {
        "rectangle": ("[", "]"),      # [text]
        "rounded": ("(", ")"),         # (text)
        "stadium": ("([", "])"),       # ([text])
        "subroutine": ("[[", "]]"),    # [[text]]
        "cylinder": ("[(", ")]"),      # [(text)]
        "circle": ("((", "))"),        # ((text))
        "asymmetric": (">", "]"),      # >text]
        "rhombus": ("{", "}"),         # {text}
        "hexagon": ("{{", "}}"),       # {{text}}
        "parallelogram": ("[/", "/]"), # [/text/]
        "parallelogram_alt": ("[\\", "\\]"),
        "trapezoid": ("[/", "\\]"),    # [/text\]
        "trapezoid_alt": ("[\\", "/]"),
        "double_circle": ("(((", ")))"), # (((text)))
    }
    
    # Arrow types
    ARROW_TYPES = {
        "solid": "-->",
        "solid_text": "-->|text|",
        "dotted": "-.-",
        "dotted_text": "-.-|text|",
        "thick": "==>",
        "thick_text": "==>|text|",
        "invisible": "~~~",
        "open": "---",
        "arrow_circle": "--o",
        "arrow_cross": "--x",
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidFlowchartAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js flowchart specialist. Your role is to:

1. CREATE valid Mermaid flowchart diagrams from text descriptions
2. VALIDATE and FIX existing Mermaid flowchart syntax
3. ENSURE proper node definitions and connections
4. APPLY appropriate styling for readability

MERMAID FLOWCHART SYNTAX RULES:
================================

1. DIRECTION DECLARATION (first line):
   - flowchart TD (top-down) - DEFAULT for hierarchical flows
   - flowchart TB (top-bottom) - same as TD
   - flowchart BT (bottom-top) - for reverse flows
   - flowchart LR (left-right) - for horizontal processes
   - flowchart RL (right-left) - for reverse horizontal

2. NODE DEFINITIONS:
   - A[Rectangle] - standard process/step
   - B(Rounded) - start/end terminals  
   - C{Diamond} - decision points
   - D((Circle)) - connectors
   - E>Asymmetric] - input/output
   - F[[Subroutine]] - subprocess
   - G[(Database)] - storage
   - H{{Hexagon}} - preparation
   
3. NODE IDs:
   - Use meaningful IDs: start, process1, decision, end
   - Avoid special characters except underscore
   - Case-sensitive: Start ≠ start

4. CONNECTIONS (Arrows):
   - A --> B (solid arrow)
   - A --> |label| B (labeled connection)
   - A -.-> B (dotted arrow)
   - A ==> B (thick arrow)
   - A --- B (open link, no arrow)
   - A --x B (cross end)
   - A --o B (circle end)

5. SUBGRAPHS (for grouping):
   ```
   subgraph title
       direction LR
       A --> B
   end
   ```

6. STYLING:
   - style A fill:#f9f,stroke:#333
   - classDef className fill:#f9f
   - class A,B className

BEST PRACTICES:
===============
- Keep node text concise (max 4-5 words)
- Use consistent ID naming convention
- Add labels to decision branches (Yes/No, True/False)
- Group related nodes in subgraphs
- Limit to 10-15 nodes for readability
- Use appropriate shapes for node types

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        direction = kwargs.get("direction", "TD")
        include_styling = kwargs.get("include_styling", True)
        
        return f"""Convert the following content into a properly formatted Mermaid flowchart diagram.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Direction: {direction}
- Include styling: {include_styling}
- Use appropriate node shapes for different step types
- Add clear labels to connections where needed
- Include proper decision branches with Yes/No labels

EXPECTED OUTPUT FORMAT:
```mermaid
flowchart {direction}
    start([Start])
    step1[Process Step]
    decision{{Decision Point}}
    step2[Another Step]
    endNode([End])
    
    start --> step1
    step1 --> decision
    decision -->|Yes| step2
    decision -->|No| endNode
    step2 --> endNode
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "flowchart",
    "node_count": number_of_nodes,
    "has_subgraphs": true/false,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid flowchart syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            # Check if content is raw mermaid without code blocks
            if not content.strip().startswith(('flowchart', 'graph')):
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check direction declaration
        first_line = lines[0].strip() if lines else ""
        if not re.match(r'^(flowchart|graph)\s+(TD|TB|BT|LR|RL)', first_line):
            errors.append("Missing or invalid direction declaration (use: flowchart TD/TB/BT/LR/RL)")
        
        # Check for node definitions
        node_pattern = r'[A-Za-z_][A-Za-z0-9_]*\s*[\[\(\{\<\>]'
        if not re.search(node_pattern, diagram):
            errors.append("No valid node definitions found")
        
        # Check for connections
        arrow_pattern = r'--[>\-\.]|==>'
        if not re.search(arrow_pattern, diagram):
            errors.append("No connections/arrows found between nodes")
        
        # Check for balanced brackets in nodes
        bracket_pairs = {'[': ']', '(': ')', '{': '}', '<': '>'}
        for line in lines[1:]:
            if '-->' in line or '---' in line or '==>' in line:
                continue  # Skip connection lines
            for open_b, close_b in bracket_pairs.items():
                if line.count(open_b) != line.count(close_b):
                    errors.append(f"Unbalanced brackets in: {line[:50]}...")
                    break
        
        # Check for common syntax errors
        if '->' in diagram and '-->' not in diagram:
            errors.append("Use --> instead of -> for arrows")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid Mermaid flowchart."""
        if '```mermaid' not in content.lower():
            return False
        
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """Create a basic flowchart from text content."""
        direction = kwargs.get("direction", "TD")
        
        # Try to extract steps from numbered list or bullet points
        lines = content.strip().split('\n')
        nodes = []
        
        for i, line in enumerate(lines):
            # Clean line
            line = re.sub(r'^[\d\.\-\*\#]+\s*', '', line.strip())
            if line:
                node_id = f"step{i+1}"
                # Truncate long text
                text = line[:50] + "..." if len(line) > 50 else line
                nodes.append((node_id, text))
        
        if not nodes:
            return content
        
        # Build flowchart
        diagram_lines = [f"flowchart {direction}"]
        
        # Add nodes
        for node_id, text in nodes:
            diagram_lines.append(f"    {node_id}[{text}]")
        
        # Add connections
        diagram_lines.append("")
        for i in range(len(nodes) - 1):
            diagram_lines.append(f"    {nodes[i][0]} --> {nodes[i+1][0]}")
        
        return "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
    
    def create_flowchart(
        self,
        steps: List[str],
        direction: str = "TD",
        decisions: Optional[Dict[int, Dict[str, int]]] = None,
        title: Optional[str] = None,
    ) -> AgentResult:
        """
        Create a flowchart from a list of steps.
        
        Args:
            steps: List of step descriptions
            direction: Flow direction (TD, TB, BT, LR, RL)
            decisions: Dict mapping step index to {label: target_index}
            title: Optional title for the diagram
            
        Returns:
            AgentResult with the generated flowchart
        """
        diagram_lines = [f"flowchart {direction}"]
        
        if title:
            diagram_lines.append(f"    subgraph {title}")
        
        # Create nodes
        for i, step in enumerate(steps):
            node_id = f"step{i}"
            # Determine node shape based on content
            if i == 0:
                diagram_lines.append(f"    {node_id}([{step}])")  # Start - rounded
            elif i == len(steps) - 1:
                diagram_lines.append(f"    {node_id}([{step}])")  # End - rounded
            elif decisions and i in decisions:
                diagram_lines.append(f"    {node_id}{{{step}}}")  # Decision - diamond
            else:
                diagram_lines.append(f"    {node_id}[{step}]")    # Process - rectangle
        
        if title:
            diagram_lines.append("    end")
        
        # Create connections
        diagram_lines.append("")
        for i in range(len(steps) - 1):
            if decisions and i in decisions:
                # Add decision branches
                for label, target in decisions[i].items():
                    diagram_lines.append(f"    step{i} -->|{label}| step{target}")
            else:
                diagram_lines.append(f"    step{i} --> step{i+1}")
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(steps),
            agent_name=self.config.name,
            metadata={
                "direction": direction,
                "node_count": len(steps),
                "has_decisions": decisions is not None,
            }
        )
