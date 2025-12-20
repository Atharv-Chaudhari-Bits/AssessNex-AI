"""
ASCII Tree Agent - Creates tree structures using ASCII characters.

Features:
- File/folder tree structures
- Hierarchical data visualization
- Multiple tree styles
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Union

from backend.app.agents.base.base_agent import (
    BaseFormattingAgent,
    AgentConfig,
    AgentResult,
    ContentType,
    ValidationLevel,
)
from backend.app.utils import get_logger

logger = get_logger(__name__)


class ASCIITreeAgent(BaseFormattingAgent):
    """
    Specialized agent for ASCII tree diagrams.
    
    Creates tree structures for:
    - Directory/file listings
    - Organizational hierarchies
    - Data structures
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="ASCIITreeAgent",
            content_type=ContentType.ASCII,
            max_retries=2,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an ASCII tree diagram specialist.

TREE STYLES:
============

1. UNICODE STYLE:
   root/
   ├── folder1/
   │   ├── file1.txt
   │   └── file2.txt
   ├── folder2/
   │   └── subfolder/
   │       └── file3.txt
   └── file4.txt

2. SIMPLE STYLE:
   root/
   |-- folder1/
   |   |-- file1.txt
   |   +-- file2.txt
   |-- folder2/
   |   +-- subfolder/
   |       +-- file3.txt
   +-- file4.txt

CHARACTERS:
- ├── : Branch (more items follow)
- └── : Last branch
- │   : Vertical line (continuation)
- ──  : Horizontal connector

Return trees in code blocks."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        style = kwargs.get("style", "unicode")
        
        return f"""Convert this hierarchy into an ASCII tree.

INPUT:
{content}

STYLE: {style}

Return JSON with:
{{
    "formatted_content": "the tree in a code block",
    "depth": max_depth,
    "node_count": total_nodes
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate ASCII tree."""
        errors = []
        
        tree_chars = ['├', '└', '│', '─', '|', '+', '-']
        has_structure = any(c in content for c in tree_chars)
        
        if not has_structure:
            errors.append("No tree structure found")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if already a tree."""
        tree_chars = ['├', '└', '│', '|--', '+--']
        return any(c in content for c in tree_chars)
    
    def create_tree(
        self,
        root: str,
        structure: Union[Dict, List],
        style: str = "unicode",
    ) -> AgentResult:
        """
        Create an ASCII tree from a hierarchical structure.
        
        Args:
            root: Root node name
            structure: Dict or List representing hierarchy
            style: "unicode" or "simple"
        """
        if style == "unicode":
            branch = "├── "
            last_branch = "└── "
            vertical = "│   "
            space = "    "
        else:
            branch = "|-- "
            last_branch = "+-- "
            vertical = "|   "
            space = "    "
        
        lines = [root]
        node_count = 1
        max_depth = 0
        
        def add_items(items: Union[Dict, List], prefix: str = "", depth: int = 0):
            nonlocal node_count, max_depth
            max_depth = max(max_depth, depth)
            
            if isinstance(items, dict):
                item_list = list(items.items())
            elif isinstance(items, list):
                item_list = [(item, None) for item in items]
            else:
                return
            
            for i, (name, children) in enumerate(item_list):
                is_last = i == len(item_list) - 1
                connector = last_branch if is_last else branch
                
                lines.append(f"{prefix}{connector}{name}")
                node_count += 1
                
                if children:
                    new_prefix = prefix + (space if is_last else vertical)
                    add_items(children, new_prefix, depth + 1)
        
        add_items(structure)
        
        content = "```\n" + "\n".join(lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=root,
            agent_name=self.config.name,
            metadata={
                "root": root,
                "node_count": node_count,
                "max_depth": max_depth,
                "style": style,
            }
        )
