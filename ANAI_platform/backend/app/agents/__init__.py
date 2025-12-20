"""
Agents package initialization.

Exports agent classes and factory functions from modular structure.

Package Structure:
==================

agents/
├── base/                    # Base agent classes
│   └── base_agent.py        # BaseFormattingAgent, AgentConfig, AgentResult
│
├── mermaid/                 # Mermaid diagram agents
│   ├── flowchart_agent.py   # MermaidFlowchartAgent
│   ├── sequence_agent.py    # MermaidSequenceAgent
│   ├── class_agent.py       # MermaidClassAgent
│   ├── state_agent.py       # MermaidStateAgent
│   ├── er_agent.py          # MermaidERDAgent
│   ├── gantt_agent.py       # MermaidGanttAgent
│   ├── pie_agent.py         # MermaidPieAgent
│   └── mindmap_agent.py     # MermaidMindmapAgent
│
├── ascii/                   # ASCII art agents
│   ├── flowchart_agent.py   # ASCIIFlowchartAgent
│   ├── box_agent.py         # ASCIIBoxAgent
│   ├── table_agent.py       # ASCIITableAgent
│   └── tree_agent.py        # ASCIITreeAgent
│
├── latex/                   # LaTeX/math agents
│   ├── inline_agent.py      # InlineLaTeXAgent
│   ├── block_agent.py       # BlockLaTeXAgent
│   ├── math_agent.py        # MathExpressionAgent
│   └── equation_agent.py    # EquationArrayAgent
│
├── code/                    # Code formatting agents
│   ├── python_agent.py      # PythonCodeAgent
│   ├── multi_lang_agent.py  # MultiLanguageCodeAgent
│   └── explained_code_agent.py  # ExplainedCodeAgent
│
├── orchestration/           # Orchestration & supervision
│   ├── orchestrator_agent.py    # OrchestratorAgent
│   ├── supervisor_agent.py      # SupervisorAgent
│   └── quality_control_agent.py # QualityControlAgent
│
├── question_generator.py    # QuestionGenerationAgent
├── formatting_agents.py     # Legacy formatting pipeline
└── specialized_agents.py    # Legacy specialized agents
"""

# Core question generation
from backend.app.agents.question_generator import (
    QuestionGenerationAgent,
    get_agent,
)

# Legacy formatting agents (for backward compatibility)
from backend.app.agents.formatting_agents import (
    CodeFormatterAgent,
    LaTeXFormatterAgent,
    DiagramFormatterAgent,
    FormattingPipeline,
)

# Base agent classes
from backend.app.agents.base import (
    BaseFormattingAgent,
    AgentConfig,
    AgentResult,
    ContentType,
    ValidationLevel,
)

# Mermaid diagram agents
from backend.app.agents.mermaid import (
    MermaidFlowchartAgent,
    MermaidSequenceAgent,
    MermaidClassAgent,
    MermaidStateAgent,
    MermaidERDAgent,
    MermaidGanttAgent,
    MermaidPieAgent,
    MermaidMindmapAgent,
)

# ASCII art agents
from backend.app.agents.ascii import (
    ASCIIFlowchartAgent,
    ASCIIBoxAgent,
    ASCIITableAgent,
    ASCIITreeAgent,
)

# LaTeX/math agents
from backend.app.agents.latex import (
    InlineLaTeXAgent,
    BlockLaTeXAgent,
    MathExpressionAgent,
    EquationArrayAgent,
)

# Code formatting agents
from backend.app.agents.code import (
    PythonCodeAgent,
    MultiLanguageCodeAgent,
    ExplainedCodeAgent,
)

# Orchestration agents
from backend.app.agents.orchestration import (
    OrchestratorAgent,
    SupervisorAgent,
    QualityControlAgent,
)

# Legacy imports for backward compatibility
try:
    from backend.app.agents.specialized_agents import (
        MarkdownTableAgent,
        MarkdownDiagramAgent,
        ImageDescriptionAgent,
        MasterFormattingOrchestrator,
    )
except ImportError:
    # These may be moved to new structure
    MarkdownTableAgent = None
    MarkdownDiagramAgent = None
    ImageDescriptionAgent = None
    MasterFormattingOrchestrator = None


__all__ = [
    # ==========================================
    # CORE AGENTS
    # ==========================================
    "QuestionGenerationAgent",
    "get_agent",
    
    # ==========================================
    # BASE CLASSES
    # ==========================================
    "BaseFormattingAgent",
    "AgentConfig",
    "AgentResult",
    "ContentType",
    "ValidationLevel",
    
    # ==========================================
    # MERMAID DIAGRAM AGENTS
    # ==========================================
    "MermaidFlowchartAgent",
    "MermaidSequenceAgent",
    "MermaidClassAgent",
    "MermaidStateAgent",
    "MermaidERDAgent",
    "MermaidGanttAgent",
    "MermaidPieAgent",
    "MermaidMindmapAgent",
    
    # ==========================================
    # ASCII ART AGENTS
    # ==========================================
    "ASCIIFlowchartAgent",
    "ASCIIBoxAgent",
    "ASCIITableAgent",
    "ASCIITreeAgent",
    
    # ==========================================
    # LATEX/MATH AGENTS
    # ==========================================
    "InlineLaTeXAgent",
    "BlockLaTeXAgent",
    "MathExpressionAgent",
    "EquationArrayAgent",
    
    # ==========================================
    # CODE FORMATTING AGENTS
    # ==========================================
    "PythonCodeAgent",
    "MultiLanguageCodeAgent",
    "ExplainedCodeAgent",
    
    # ==========================================
    # ORCHESTRATION AGENTS
    # ==========================================
    "OrchestratorAgent",
    "SupervisorAgent",
    "QualityControlAgent",
    
    # ==========================================
    # LEGACY FORMATTING (backward compatibility)
    # ==========================================
    "CodeFormatterAgent",
    "LaTeXFormatterAgent",
    "DiagramFormatterAgent",
    "FormattingPipeline",
    "MarkdownTableAgent",
    "MarkdownDiagramAgent",
    "ImageDescriptionAgent",
    "MasterFormattingOrchestrator",
]


# Factory function for creating agent instances
def create_agent(agent_type: str, llm_client=None):
    """
    Factory function to create agent instances.
    
    Args:
        agent_type: Type of agent to create
        llm_client: Optional LLM client instance
        
    Returns:
        Agent instance
    """
    agent_map = {
        # Mermaid agents
        "mermaid_flowchart": MermaidFlowchartAgent,
        "mermaid_sequence": MermaidSequenceAgent,
        "mermaid_class": MermaidClassAgent,
        "mermaid_state": MermaidStateAgent,
        "mermaid_er": MermaidERDAgent,
        "mermaid_gantt": MermaidGanttAgent,
        "mermaid_pie": MermaidPieAgent,
        "mermaid_mindmap": MermaidMindmapAgent,
        # ASCII agents
        "ascii_flowchart": ASCIIFlowchartAgent,
        "ascii_box": ASCIIBoxAgent,
        "ascii_table": ASCIITableAgent,
        "ascii_tree": ASCIITreeAgent,
        # LaTeX agents
        "latex_inline": InlineLaTeXAgent,
        "latex_block": BlockLaTeXAgent,
        "latex_math": MathExpressionAgent,
        "latex_equation": EquationArrayAgent,
        # Code agents
        "code_python": PythonCodeAgent,
        "code_multi": MultiLanguageCodeAgent,
        "code_explained": ExplainedCodeAgent,
        # Orchestration
        "orchestrator": OrchestratorAgent,
        "supervisor": SupervisorAgent,
        "quality_control": QualityControlAgent,
    }
    
    agent_class = agent_map.get(agent_type.lower())
    if agent_class is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(llm_client=llm_client)
