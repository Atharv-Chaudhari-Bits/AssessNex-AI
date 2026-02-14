"""
Agents package initialization.

Exports agent classes and factory functions from modular structure.
"""

# ==========================================
# CORE QUESTION GENERATION - LEGACY
# ==========================================
from backend.app.agents.question_generator import (
    QuestionGenerationAgent,
    get_agent,
)

# ==========================================
# NEW: CUSTOMIZED QUESTION MODULE WITH BLOOM'S TAXONOMY
# ==========================================
from backend.app.agents.customized_question_module import (
    CustomizedQuestionAgent,
    get_customized_agent,
)

# ==========================================
# NEW: ASSIGNMENT GENERATION AGENT WITH BLOOM'S TAXONOMY
# ==========================================
from backend.app.agents.assignment_agent import (
    AssignmentGenerationAgent,
)

# ==========================================
# LEGACY FORMATTING AGENTS
# ==========================================
from backend.app.agents.formatting_agents import (
    CodeFormatterAgent,
    LaTeXFormatterAgent,
    DiagramFormatterAgent,
    FormattingPipeline,
)

# ==========================================
# BASE AGENT CLASSES
# ==========================================
from backend.app.agents.base import (
    BaseFormattingAgent,
    AgentConfig,
    AgentResult,
    ContentType,
    ValidationLevel,
)

# ==========================================
# MERMAID DIAGRAM AGENTS
# ==========================================
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

# ==========================================
# ASCII ART AGENTS
# ==========================================
from backend.app.agents.ascii import (
    ASCIIFlowchartAgent,
    ASCIIBoxAgent,
    ASCIITableAgent,
    ASCIITreeAgent,
)

# ==========================================
# LATEX/MATH AGENTS
# ==========================================
from backend.app.agents.latex import (
    InlineLaTeXAgent,
    BlockLaTeXAgent,
    MathExpressionAgent,
    EquationArrayAgent,
)

# ==========================================
# CODE FORMATTING AGENTS
# ==========================================
from backend.app.agents.code import (
    PythonCodeAgent,
    MultiLanguageCodeAgent,
    ExplainedCodeAgent,
)

# ==========================================
# ORCHESTRATION AGENTS
# ==========================================
from backend.app.agents.orchestration import (
    OrchestratorAgent,
    SupervisorAgent,
    QualityControlAgent,
)

# ==========================================
# LEGACY SPECIALIZED AGENTS
# ==========================================
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


# ==========================================
# BLOOM'S TAXONOMY CONSTANTS
# ==========================================
BLOOM_TAXONOMY_LEVELS = [
    "Remember",
    "Understand", 
    "Apply",
    "Analyze",
    "Evaluate",
    "Create"
]


__all__ = [
    # ==========================================
    # CORE AGENTS - LEGACY
    # ==========================================
    "QuestionGenerationAgent",
    "get_agent",
    
    # ==========================================
    # CUSTOMIZED QUESTION AGENTS - NEW (BLOOM'S TAXONOMY)
    # ==========================================
    "CustomizedQuestionAgent",
    "get_customized_agent",
    
    # ==========================================
    # ASSIGNMENT GENERATION AGENT - NEW
    # ==========================================
    "AssignmentGenerationAgent",
    
    # ==========================================
    # BLOOM'S TAXONOMY CONSTANTS
    # ==========================================
    "BLOOM_TAXONOMY_LEVELS",
    
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
    # LEGACY FORMATTING
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


# ==========================================
# FACTORY FUNCTIONS
# ==========================================

def create_agent(agent_type: str, llm_client=None):
    """
    Factory function to create agent instances.
    
    Args:
        agent_type: Type of agent to create
        llm_client: Optional LLM client instance
        
    Returns:
        Agent instance
        
    Raises:
        ValueError: If agent_type is unknown
    """
    agent_map = {
        # Question generation agents
        "question_generator": QuestionGenerationAgent,
        "customized_question": CustomizedQuestionAgent,
        "assignment_generator": AssignmentGenerationAgent,
        
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


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def get_question_agent(use_customized: bool = False):
    """
    Get appropriate question generation agent.
    
    Args:
        use_customized: If True, returns customized agent with Bloom's taxonomy.
                       If False, returns legacy question generator.
    
    Returns:
        Agent instance for question generation
    """
    if use_customized:
        return get_customized_agent()
    return get_agent()


def get_assignment_agent(prompt_builder=None):
    """
    Get assignment generation agent.
    
    Args:
        prompt_builder: Optional PromptBuilder instance
        
    Returns:
        AssignmentGenerationAgent instance
    """
    from backend.app.prompts.prompt_manager import PromptBuilder
    from backend.app.agents.assignment_agent import AssignmentGenerationAgent
    
    if prompt_builder is None:
        prompt_builder = PromptBuilder()
    
    return AssignmentGenerationAgent(prompt_builder)


# ==========================================
# MODULE METADATA
# ==========================================

__version__ = "2.1.0"
__author__ = "MTech Assessment Team"
__description__ = "Agent-based question generation with Bloom's taxonomy calibration and assignment generation"