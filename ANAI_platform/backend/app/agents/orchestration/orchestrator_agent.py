"""
Orchestrator Agent - Routes content to appropriate specialized agents.

Features:
- Content type detection
- Agent selection
- Parallel processing coordination
- Result aggregation
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Type
from enum import Enum

from backend.app.agents.base.base_agent import (
    BaseFormattingAgent,
    AgentConfig,
    AgentResult,
    ContentType,
    ValidationLevel,
)
from backend.app.llm_client import get_llm_client
from backend.app.utils import get_logger

logger = get_logger(__name__)


class DetectedContentType(Enum):
    """Types of content that can be detected."""
    MERMAID_FLOWCHART = "mermaid_flowchart"
    MERMAID_SEQUENCE = "mermaid_sequence"
    MERMAID_CLASS = "mermaid_class"
    MERMAID_STATE = "mermaid_state"
    MERMAID_ER = "mermaid_er"
    MERMAID_GANTT = "mermaid_gantt"
    MERMAID_PIE = "mermaid_pie"
    MERMAID_MINDMAP = "mermaid_mindmap"
    ASCII_FLOWCHART = "ascii_flowchart"
    ASCII_BOX = "ascii_box"
    ASCII_TABLE = "ascii_table"
    ASCII_TREE = "ascii_tree"
    LATEX_INLINE = "latex_inline"
    LATEX_BLOCK = "latex_block"
    LATEX_MATH = "latex_math"
    LATEX_EQUATION = "latex_equation"
    CODE_PYTHON = "code_python"
    CODE_JAVASCRIPT = "code_javascript"
    CODE_JAVA = "code_java"
    CODE_CPP = "code_cpp"
    CODE_SQL = "code_sql"
    CODE_OTHER = "code_other"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


# Detection patterns for content types
CONTENT_PATTERNS: Dict[DetectedContentType, List[re.Pattern]] = {
    DetectedContentType.MERMAID_FLOWCHART: [
        re.compile(r'```mermaid\s*\n\s*(graph|flowchart)\s+(TB|TD|BT|RL|LR)', re.IGNORECASE),
        re.compile(r'flowchart\s+(TB|TD|BT|RL|LR)', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_SEQUENCE: [
        re.compile(r'```mermaid\s*\n\s*sequenceDiagram', re.IGNORECASE),
        re.compile(r'sequenceDiagram', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_CLASS: [
        re.compile(r'```mermaid\s*\n\s*classDiagram', re.IGNORECASE),
        re.compile(r'classDiagram', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_STATE: [
        re.compile(r'```mermaid\s*\n\s*stateDiagram', re.IGNORECASE),
        re.compile(r'stateDiagram', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_ER: [
        re.compile(r'```mermaid\s*\n\s*erDiagram', re.IGNORECASE),
        re.compile(r'erDiagram', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_GANTT: [
        re.compile(r'```mermaid\s*\n\s*gantt', re.IGNORECASE),
        re.compile(r'gantt\s+title', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_PIE: [
        re.compile(r'```mermaid\s*\n\s*pie', re.IGNORECASE),
        re.compile(r'pie\s+(title|showData)', re.IGNORECASE),
    ],
    DetectedContentType.MERMAID_MINDMAP: [
        re.compile(r'```mermaid\s*\n\s*mindmap', re.IGNORECASE),
        re.compile(r'mindmap\s+root', re.IGNORECASE),
    ],
    DetectedContentType.ASCII_TABLE: [
        re.compile(r'[┌┬┐├┼┤└┴┘│─]+'),
        re.compile(r'\+[-+]+\+'),
        re.compile(r'\|.*\|.*\|'),
    ],
    DetectedContentType.ASCII_TREE: [
        re.compile(r'[├└]──'),
        re.compile(r'[│\s]+[├└]'),
    ],
    DetectedContentType.ASCII_BOX: [
        re.compile(r'[┌┐└┘]'),
        re.compile(r'\+---+\+'),
    ],
    DetectedContentType.LATEX_BLOCK: [
        re.compile(r'\$\$[\s\S]+?\$\$'),
        re.compile(r'\\begin\{(equation|align|gather)\}'),
    ],
    DetectedContentType.LATEX_INLINE: [
        re.compile(r'(?<!\$)\$(?!\$)[^$]+\$(?!\$)'),
    ],
    DetectedContentType.LATEX_EQUATION: [
        re.compile(r'\\begin\{(cases|matrix|bmatrix|pmatrix|array)\}'),
    ],
    DetectedContentType.CODE_PYTHON: [
        re.compile(r'```python', re.IGNORECASE),
        re.compile(r'def\s+\w+\s*\('),
        re.compile(r'import\s+\w+'),
        re.compile(r'from\s+\w+\s+import'),
    ],
    DetectedContentType.CODE_JAVASCRIPT: [
        re.compile(r'```javascript', re.IGNORECASE),
        re.compile(r'```js', re.IGNORECASE),
        re.compile(r'const\s+\w+\s*='),
        re.compile(r'function\s+\w+\s*\('),
        re.compile(r'=>'),
    ],
    DetectedContentType.CODE_JAVA: [
        re.compile(r'```java', re.IGNORECASE),
        re.compile(r'public\s+class\s+\w+'),
        re.compile(r'public\s+static\s+void\s+main'),
    ],
    DetectedContentType.CODE_SQL: [
        re.compile(r'```sql', re.IGNORECASE),
        re.compile(r'SELECT\s+.*\s+FROM', re.IGNORECASE),
        re.compile(r'CREATE\s+TABLE', re.IGNORECASE),
    ],
}


class OrchestratorAgent(BaseFormattingAgent):
    """
    Master orchestrator that routes content to appropriate specialized agents.
    
    Responsibilities:
    1. Detect content types in input
    2. Select appropriate specialized agents
    3. Coordinate parallel processing
    4. Aggregate and return results
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="OrchestratorAgent",
            content_type=ContentType.MIXED,
            max_retries=1,
            validation_level=ValidationLevel.BASIC,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a content orchestration specialist. Your role is to:

1. ANALYZE content to identify types (code, diagrams, math, etc.)
2. DETECT multiple content types in mixed documents
3. ROUTE each section to the appropriate formatter
4. COORDINATE the formatting pipeline

CONTENT TYPES YOU CAN IDENTIFY:
================================

DIAGRAMS:
- Mermaid: flowchart, sequence, class, state, ER, gantt, pie, mindmap
- ASCII: flowcharts, boxes, tables, trees

MATH/LATEX:
- Inline: $...$
- Block: $$...$$
- Equations: matrices, systems

CODE:
- Python, JavaScript, Java, C++, SQL, etc.

Return a structured analysis of content types found."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        return f"""Analyze this content and identify all content types present.

CONTENT:
{content}

Return JSON with:
{{
    "detected_types": ["type1", "type2"],
    "sections": [
        {{"type": "...", "start": 0, "end": 100, "content": "..."}}
    ],
    "recommended_agents": ["Agent1", "Agent2"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate orchestrator output."""
        return True, []
    
    def _is_already_formatted(self, content: str) -> bool:
        """Orchestrator always processes."""
        return False
    
    def detect_content_types(self, content: str) -> List[DetectedContentType]:
        """
        Detect all content types present in the input.
        
        Args:
            content: The content to analyze
            
        Returns:
            List of detected content types
        """
        detected = []
        
        for content_type, patterns in CONTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(content):
                    if content_type not in detected:
                        detected.append(content_type)
                    break
        
        if not detected:
            detected.append(DetectedContentType.PLAIN_TEXT)
        
        logger.debug(f"Detected content types: {[ct.value for ct in detected]}")
        return detected
    
    def get_agent_for_type(self, content_type: DetectedContentType) -> Optional[str]:
        """
        Get the appropriate agent name for a content type.
        
        Args:
            content_type: The detected content type
            
        Returns:
            Agent class name or None
        """
        agent_mapping = {
            DetectedContentType.MERMAID_FLOWCHART: "MermaidFlowchartAgent",
            DetectedContentType.MERMAID_SEQUENCE: "MermaidSequenceAgent",
            DetectedContentType.MERMAID_CLASS: "MermaidClassAgent",
            DetectedContentType.MERMAID_STATE: "MermaidStateAgent",
            DetectedContentType.MERMAID_ER: "MermaidERDAgent",
            DetectedContentType.MERMAID_GANTT: "MermaidGanttAgent",
            DetectedContentType.MERMAID_PIE: "MermaidPieAgent",
            DetectedContentType.MERMAID_MINDMAP: "MermaidMindmapAgent",
            DetectedContentType.ASCII_FLOWCHART: "ASCIIFlowchartAgent",
            DetectedContentType.ASCII_BOX: "ASCIIBoxAgent",
            DetectedContentType.ASCII_TABLE: "ASCIITableAgent",
            DetectedContentType.ASCII_TREE: "ASCIITreeAgent",
            DetectedContentType.LATEX_INLINE: "InlineLaTeXAgent",
            DetectedContentType.LATEX_BLOCK: "BlockLaTeXAgent",
            DetectedContentType.LATEX_MATH: "MathExpressionAgent",
            DetectedContentType.LATEX_EQUATION: "EquationArrayAgent",
            DetectedContentType.CODE_PYTHON: "PythonCodeAgent",
            DetectedContentType.CODE_JAVASCRIPT: "MultiLanguageCodeAgent",
            DetectedContentType.CODE_JAVA: "MultiLanguageCodeAgent",
            DetectedContentType.CODE_CPP: "MultiLanguageCodeAgent",
            DetectedContentType.CODE_SQL: "MultiLanguageCodeAgent",
            DetectedContentType.CODE_OTHER: "MultiLanguageCodeAgent",
        }
        
        return agent_mapping.get(content_type)
    
    def split_content_by_type(self, content: str) -> List[Dict[str, Any]]:
        """
        Split content into sections by type.
        
        Args:
            content: The content to split
            
        Returns:
            List of {"type": ..., "content": ..., "agent": ...}
        """
        sections = []
        
        # Pattern to find code blocks
        code_block_pattern = re.compile(r'(```\w*\n[\s\S]*?```)')
        
        # Pattern to find mermaid blocks
        mermaid_pattern = re.compile(r'(```mermaid\n[\s\S]*?```)')
        
        # Pattern to find latex blocks
        latex_block_pattern = re.compile(r'(\$\$[\s\S]*?\$\$)')
        
        # Split and identify
        parts = code_block_pattern.split(content)
        
        for part in parts:
            if not part.strip():
                continue
                
            detected = self.detect_content_types(part)
            primary_type = detected[0] if detected else DetectedContentType.PLAIN_TEXT
            
            sections.append({
                "type": primary_type,
                "content": part,
                "agent": self.get_agent_for_type(primary_type),
                "detected_types": [dt.value for dt in detected],
            })
        
        return sections
    
    async def orchestrate_formatting(
        self,
        content: str,
        agent_instances: Dict[str, BaseFormattingAgent] = None,
    ) -> AgentResult:
        """
        Orchestrate the formatting of mixed content.
        
        Args:
            content: The content to format
            agent_instances: Dict mapping agent names to instances
            
        Returns:
            AgentResult with formatted content
        """
        if agent_instances is None:
            agent_instances = {}
        
        sections = self.split_content_by_type(content)
        formatted_sections = []
        
        for section in sections:
            agent_name = section.get("agent")
            section_content = section.get("content", "")
            
            if agent_name and agent_name in agent_instances:
                agent = agent_instances[agent_name]
                result = await agent.format_content(section_content)
                if result.success:
                    formatted_sections.append(result.content)
                else:
                    formatted_sections.append(section_content)
            else:
                # No specific agent, keep as is
                formatted_sections.append(section_content)
        
        final_content = "\n\n".join(formatted_sections)
        
        return AgentResult(
            success=True,
            content=final_content,
            original_content=content,
            agent_name=self.config.name,
            metadata={
                "sections_processed": len(sections),
                "agents_used": [s.get("agent") for s in sections if s.get("agent")],
            }
        )
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Provide detailed analysis of content.
        
        Args:
            content: The content to analyze
            
        Returns:
            Analysis dictionary
        """
        detected_types = self.detect_content_types(content)
        sections = self.split_content_by_type(content)
        
        return {
            "total_length": len(content),
            "detected_types": [dt.value for dt in detected_types],
            "num_sections": len(sections),
            "sections": [
                {
                    "type": s["type"].value,
                    "length": len(s["content"]),
                    "agent": s["agent"],
                }
                for s in sections
            ],
            "recommended_pipeline": [
                s["agent"] for s in sections if s["agent"]
            ],
        }
