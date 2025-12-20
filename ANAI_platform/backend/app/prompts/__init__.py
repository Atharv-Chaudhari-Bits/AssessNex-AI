"""
AssessNex AI - Organized Prompts Package

Folder Structure (Category-Based):
prompts/
  ├── base/                  - Core system and few-shot prompts
  ├── standard/              - Standard question types (MCQ, T/F, Fill-blank, etc.)
  ├── specialized/           - Specialized types (Coding, Image, Assignment)
  ├── advanced/              - Advanced features (Paper generation, Plagiarism check)
  └── formatting/            - Formatting agents prompts (Mermaid, ASCII, LaTeX, Code)
"""

# Base prompts
from .base import (
    SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
)

# Standard prompts
from .standard import (
    TRUE_FALSE_PROMPT,
    FILL_IN_BLANK_PROMPT,
    CODING_PROMPT,
    SCENARIO_PROMPT,
    COMPLEXITY_PROMPT,
    CODE_OUTPUT_PROMPT,
    QUESTION_TYPE_PROMPTS,
)

# Specialized prompts
from .specialized import (
    CODING_BASIC_PROMPT,
    CODING_INTERMEDIATE_PROMPT,
    CODING_ADVANCED_PROMPT,
    CODING_WITH_TESTS_PROMPT,
    CODING_TYPE_PROMPTS,
    IMAGE_BASED_PROMPT,
    ALGORITHM_FLOW_PROMPT,
    ANT_COLONY_VISUALIZATION,
    GRAPH_ALGORITHM_VISUALIZATION,
    IMAGE_QUESTION_TYPES,
    ASSIGNMENT_BASIC_PROMPT,
    ASSIGNMENT_INTERMEDIATE_PROMPT,
    ASSIGNMENT_ADVANCED_PROMPT,
    PROJECT_SETUP_TEMPLATE,
    ASSIGNMENT_TYPES,
)

# Advanced prompts
from .advanced import (
    QUESTION_PAPER_GENERATION,
    BALANCED_PAPER_TEMPLATE,
    PAPER_ARRANGEMENT_STRATEGIES,
    ANSWER_KEY_GENERATION,
    PLAGIARISM_CHECK_PROMPT,
    PAPER_GENERATION_TYPES,
    ADVANCED_TYPES,
)

# Formatting prompts
from .formatting import (
    # Mermaid prompts
    MERMAID_SYSTEM_PROMPT,
    MERMAID_FLOWCHART_PROMPT,
    MERMAID_SEQUENCE_PROMPT,
    MERMAID_CLASS_PROMPT,
    MERMAID_STATE_PROMPT,
    MERMAID_ER_PROMPT,
    MERMAID_GANTT_PROMPT,
    MERMAID_PIE_PROMPT,
    MERMAID_MINDMAP_PROMPT,
    MERMAID_VALIDATION_PROMPT,
    # ASCII prompts
    ASCII_SYSTEM_PROMPT,
    ASCII_FLOWCHART_PROMPT,
    ASCII_BOX_PROMPT,
    ASCII_TABLE_PROMPT,
    ASCII_TREE_PROMPT,
    ASCII_VALIDATION_PROMPT,
    # LaTeX prompts
    LATEX_SYSTEM_PROMPT,
    LATEX_INLINE_PROMPT,
    LATEX_BLOCK_PROMPT,
    LATEX_MATH_PROMPT,
    LATEX_EQUATION_PROMPT,
    LATEX_VALIDATION_PROMPT,
    # Code prompts
    CODE_SYSTEM_PROMPT,
    CODE_PYTHON_PROMPT,
    CODE_JAVASCRIPT_PROMPT,
    CODE_JAVA_PROMPT,
    CODE_SQL_PROMPT,
    CODE_EXPLAINED_PROMPT,
    CODE_VALIDATION_PROMPT,
    # Orchestration prompts
    ORCHESTRATOR_SYSTEM_PROMPT,
    CONTENT_DETECTION_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT,
    VALIDATION_PROMPT,
    QUALITY_CONTROL_PROMPT,
    REGENERATION_PROMPT,
)

__all__ = [
    # ==========================================
    # BASE PROMPTS
    # ==========================================
    'SYSTEM_PROMPT',
    'FEW_SHOT_EXAMPLES',
    
    # ==========================================
    # STANDARD QUESTION PROMPTS
    # ==========================================
    'TRUE_FALSE_PROMPT',
    'FILL_IN_BLANK_PROMPT',
    'CODING_PROMPT',
    'SCENARIO_PROMPT',
    'COMPLEXITY_PROMPT',
    'CODE_OUTPUT_PROMPT',
    'QUESTION_TYPE_PROMPTS',
    
    # ==========================================
    # CODING PROMPTS
    # ==========================================
    'CODING_BASIC_PROMPT',
    'CODING_INTERMEDIATE_PROMPT',
    'CODING_ADVANCED_PROMPT',
    'CODING_WITH_TESTS_PROMPT',
    'CODING_TYPE_PROMPTS',
    
    # ==========================================
    # IMAGE PROMPTS
    # ==========================================
    'IMAGE_BASED_PROMPT',
    'ALGORITHM_FLOW_PROMPT',
    'ANT_COLONY_VISUALIZATION',
    'GRAPH_ALGORITHM_VISUALIZATION',
    'IMAGE_QUESTION_TYPES',
    
    # ==========================================
    # ASSIGNMENT PROMPTS
    # ==========================================
    'ASSIGNMENT_BASIC_PROMPT',
    'ASSIGNMENT_INTERMEDIATE_PROMPT',
    'ASSIGNMENT_ADVANCED_PROMPT',
    'PROJECT_SETUP_TEMPLATE',
    'ASSIGNMENT_TYPES',
    
    # ==========================================
    # ADVANCED PROMPTS
    # ==========================================
    'QUESTION_PAPER_GENERATION',
    'BALANCED_PAPER_TEMPLATE',
    'PAPER_ARRANGEMENT_STRATEGIES',
    'ANSWER_KEY_GENERATION',
    'PLAGIARISM_CHECK_PROMPT',
    'PAPER_GENERATION_TYPES',
    'ADVANCED_TYPES',
    
    # ==========================================
    # MERMAID FORMATTING PROMPTS
    # ==========================================
    'MERMAID_SYSTEM_PROMPT',
    'MERMAID_FLOWCHART_PROMPT',
    'MERMAID_SEQUENCE_PROMPT',
    'MERMAID_CLASS_PROMPT',
    'MERMAID_STATE_PROMPT',
    'MERMAID_ER_PROMPT',
    'MERMAID_GANTT_PROMPT',
    'MERMAID_PIE_PROMPT',
    'MERMAID_MINDMAP_PROMPT',
    'MERMAID_VALIDATION_PROMPT',
    
    # ==========================================
    # ASCII FORMATTING PROMPTS
    # ==========================================
    'ASCII_SYSTEM_PROMPT',
    'ASCII_FLOWCHART_PROMPT',
    'ASCII_BOX_PROMPT',
    'ASCII_TABLE_PROMPT',
    'ASCII_TREE_PROMPT',
    'ASCII_VALIDATION_PROMPT',
    
    # ==========================================
    # LATEX FORMATTING PROMPTS
    # ==========================================
    'LATEX_SYSTEM_PROMPT',
    'LATEX_INLINE_PROMPT',
    'LATEX_BLOCK_PROMPT',
    'LATEX_MATH_PROMPT',
    'LATEX_EQUATION_PROMPT',
    'LATEX_VALIDATION_PROMPT',
    
    # ==========================================
    # CODE FORMATTING PROMPTS
    # ==========================================
    'CODE_SYSTEM_PROMPT',
    'CODE_PYTHON_PROMPT',
    'CODE_JAVASCRIPT_PROMPT',
    'CODE_JAVA_PROMPT',
    'CODE_SQL_PROMPT',
    'CODE_EXPLAINED_PROMPT',
    'CODE_VALIDATION_PROMPT',
    
    # ==========================================
    # ORCHESTRATION PROMPTS
    # ==========================================
    'ORCHESTRATOR_SYSTEM_PROMPT',
    'CONTENT_DETECTION_PROMPT',
    'SUPERVISOR_SYSTEM_PROMPT',
    'VALIDATION_PROMPT',
    'QUALITY_CONTROL_PROMPT',
    'REGENERATION_PROMPT',
]
