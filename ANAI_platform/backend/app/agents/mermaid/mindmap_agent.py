"""
Mermaid Mindmap Agent - Specialized agent for mind map diagrams.

Supports:
- Hierarchical thought organization
- Multiple branches
- Icons and shapes
- Different node styles
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


class MermaidMindmapAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js mind maps.
    
    Creates mind maps showing:
    - Central topic with branches
    - Hierarchical idea organization
    - Visual thought mapping
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidMindmapAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js mind map specialist. Your role is to:

1. CREATE valid Mermaid mind maps from concepts
2. VALIDATE and FIX existing mind map syntax
3. ORGANIZE ideas hierarchically
4. USE appropriate node shapes and icons

MERMAID MINDMAP SYNTAX RULES:
=============================

1. DECLARATION:
   mindmap

2. ROOT NODE (required):
   mindmap
     root((Central Topic))

3. HIERARCHY (indentation-based):
   mindmap
     root((Main Idea))
       Branch 1
         Sub-branch 1.1
         Sub-branch 1.2
       Branch 2
         Sub-branch 2.1

4. NODE SHAPES:
   root - Default square
   root(Round edges)
   root((Circle))
   root))Bang((
   root)Cloud(
   root{{Hexagon}}

5. ICONS:
   root((Topic))
     ::icon(fa fa-book)
     Branch with icon

6. EXAMPLE:
   mindmap
     root((Programming))
       Languages
         Python
           ::icon(fa fa-snake)
           Web Development
           Data Science
           Machine Learning
         JavaScript
           Frontend
           Backend Node.js
         Java
           Enterprise
           Android
       Concepts
         OOP
           Classes
           Inheritance
           Polymorphism
         Functional
           Pure Functions
           Immutability
       Tools
         IDEs
           VS Code
           PyCharm
         Version Control
           Git
           GitHub

BEST PRACTICES:
===============
- Start with clear central topic
- Use consistent indentation (2 or 4 spaces)
- Keep branch labels concise
- Limit depth to 3-4 levels
- Group related concepts
- Use shapes to differentiate types

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        root_shape = kwargs.get("root_shape", "circle")
        max_depth = kwargs.get("max_depth", 4)
        
        shape_syntax = {
            "square": "",
            "rounded": "()",
            "circle": "(())",
            "bang": "))((",
            "cloud": ")(", 
            "hexagon": "{{}}"
        }
        
        return f"""Convert the following concept/topic into a Mermaid mind map.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Root shape: {root_shape}
- Maximum depth: {max_depth} levels
- Organize ideas logically
- Keep labels concise (2-4 words max)

EXPECTED OUTPUT FORMAT:
```mermaid
mindmap
    root{shape_syntax.get(root_shape, "(())")}Central Topic{shape_syntax.get(root_shape, "(())")[::-1] if root_shape != "square" else ""}
        Main Branch 1
            Sub-topic 1.1
            Sub-topic 1.2
        Main Branch 2
            Sub-topic 2.1
                Detail 2.1.1
            Sub-topic 2.2
        Main Branch 3
            Sub-topic 3.1
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "mindmap",
    "branch_count": number_of_main_branches,
    "max_depth": maximum_depth_reached,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid mind map syntax."""
        errors = []
        
        # Extract diagram content  
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if 'mindmap' not in content.lower():
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any('mindmap' in line.lower() for line in lines[:2]):
            errors.append("Missing 'mindmap' declaration")
        
        # Check for root
        has_root = any('root' in line.lower() for line in lines)
        if not has_root:
            errors.append("Missing root node")
        
        # Check indentation consistency
        indents = []
        for line in lines:
            if line.strip() and not line.strip().startswith('mindmap'):
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indents.append(leading_spaces)
        
        if indents:
            # Check if indents are consistent (all multiples of the same base)
            min_indent = min(indents) if indents else 2
            inconsistent = [i for i in indents if i % min_indent != 0]
            if inconsistent:
                errors.append("Inconsistent indentation detected")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid mind map."""
        if '```mermaid' not in content.lower() and 'mindmap' not in content.lower():
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def create_mindmap(
        self,
        root: str,
        branches: Dict[str, Any],
        root_shape: str = "circle",
    ) -> AgentResult:
        """
        Create a mind map from a hierarchical structure.
        
        Args:
            root: Central topic
            branches: Nested dict representing the hierarchy
            root_shape: Shape for root node
            
        Returns:
            AgentResult with the generated mind map
        """
        shape_map = {
            "square": ("", ""),
            "rounded": ("(", ")"),
            "circle": ("((", "))"),
            "bang": ("))", "(("),
            "cloud": (")", "("),
            "hexagon": ("{{", "}}"),
        }
        
        open_shape, close_shape = shape_map.get(root_shape, ("((", "))"))
        
        diagram_lines = ["mindmap", f"    root{open_shape}{root}{close_shape}"]
        
        def add_branches(branch_dict: Dict, indent: int = 2):
            for key, value in branch_dict.items():
                diagram_lines.append("    " * indent + key)
                if isinstance(value, dict):
                    add_branches(value, indent + 1)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            add_branches(item, indent + 1)
                        else:
                            diagram_lines.append("    " * (indent + 1) + str(item))
        
        add_branches(branches)
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=root,
            agent_name=self.config.name,
            metadata={
                "root": root,
                "branch_count": len(branches),
            }
        )
