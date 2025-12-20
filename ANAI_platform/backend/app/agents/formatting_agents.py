"""
Formatting Agents for Question Generation.

This module contains specialized agents that ensure proper formatting
for different question types:
- CodeFormatterAgent: Ensures code answers have code blocks + descriptions
- LaTeXFormatterAgent: Ensures numerical answers have proper LaTeX
- DiagramFormatterAgent: Ensures diagram answers use correct format (Mermaid/ASCII)
"""

import re
import json
from typing import Dict, Any, List, Optional
from backend.app.llm_client import get_llm_client
from backend.app.utils import get_logger

logger = get_logger(__name__)


class CodeFormatterAgent:
    """
    Agent to ensure code-related questions have proper formatting.
    
    Ensures:
    - Code blocks with proper syntax (```python)
    - Text descriptions explaining the code
    - Line numbers and proper indentation
    """
    
    SYSTEM_PROMPT = """You are a code formatting specialist. Your job is to ensure 
code answers are properly formatted with:
1. Code blocks using ```python syntax
2. Clear text descriptions before/after code explaining what it does
3. Proper indentation and structure
4. Comments within code for clarity

If the answer already has proper formatting, return it unchanged.
If it needs formatting, reformat it properly.

Always return valid JSON with the formatted content."""

    FORMAT_PROMPT = """Review and format this code-related answer to ensure it has:
1. Code wrapped in ```python code blocks
2. A brief text description explaining the code (before or after)
3. Proper indentation

Input Answer:
{answer}

Input Explanation:
{explanation}

Return a JSON object with:
{{
    "expected_answer": "properly formatted answer with code blocks and description",
    "explanation": "properly formatted explanation"
}}

If already well-formatted, return as-is. Ensure code is in ```python blocks."""

    def __init__(self):
        """Initialize the code formatter agent."""
        self.llm_client = get_llm_client()
        logger.info("CodeFormatterAgent initialized")
    
    def format_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a code-related question to ensure proper code formatting.
        
        Args:
            question: Question dict with expected_answer and explanation
            
        Returns:
            Question dict with properly formatted answer and explanation
        """
        answer = question.get("expected_answer", "")
        explanation = question.get("explanation", "")
        
        # Check if already has code blocks
        has_code_block = "```" in str(answer)
        has_description = any(word in str(answer).lower() for word in 
                            ["this", "the", "function", "code", "implementation", "solution"])
        
        # If already well-formatted, return as-is
        if has_code_block and has_description:
            logger.debug("Answer already well-formatted, skipping")
            return question
        
        try:
            prompt = self.FORMAT_PROMPT.format(answer=answer, explanation=explanation)
            
            response = self.llm_client.generate_json_message(
                prompt,
                system_message=self.SYSTEM_PROMPT
            )
            
            # Parse response
            if isinstance(response, str):
                response = json.loads(response)
            
            if isinstance(response, dict):
                question["expected_answer"] = response.get("expected_answer", answer)
                question["explanation"] = response.get("explanation", explanation)
                logger.info("Successfully formatted code answer")
            
        except Exception as e:
            logger.error(f"Error formatting code answer: {e}")
            # Return original if formatting fails
        
        return question


class LaTeXFormatterAgent:
    """
    Agent to ensure numerical/math questions have proper LaTeX formatting.
    
    Ensures:
    - Mathematical formulas use LaTeX notation ($..$ or $$..$$)
    - Inline math for simple expressions
    - Block math for complex equations
    - Proper LaTeX commands (\frac, \sum, \sqrt, etc.)
    """
    
    SYSTEM_PROMPT = """You are a LaTeX formatting specialist for mathematical content.
Your job is to ensure mathematical answers use proper LaTeX notation:
1. Inline math: $expression$ for simple formulas
2. Block math: $$expression$$ for complex equations
3. Proper LaTeX commands: \\frac{}{}, \\sum, \\sqrt{}, \\times, etc.
4. Clear step-by-step solutions with each step in proper LaTeX

If the answer already has proper LaTeX, return it unchanged.
If it needs LaTeX formatting, add proper notation.

Always return valid JSON with the formatted content."""

    FORMAT_PROMPT = """Review and format this numerical/mathematical answer to ensure it has:
1. Mathematical expressions in LaTeX notation ($ for inline, $$ for blocks)
2. Proper LaTeX commands (\\frac, \\sum, \\sqrt, \\times, etc.)
3. Step-by-step solution with LaTeX for each calculation

Input Answer:
{answer}

Input Explanation:
{explanation}

Return a JSON object with:
{{
    "expected_answer": "answer with proper LaTeX formatting",
    "explanation": "explanation with proper LaTeX for all math"
}}

Examples of LaTeX formatting:
- "x = 5" → "$x = 5$"
- "1/2" → "$\\frac{{1}}{{2}}$"
- "sum of x" → "$\\sum x$"
- "sqrt(n)" → "$\\sqrt{{n}}$"
- "O(n^2)" → "$O(n^2)$"
- "2 * 3" → "$2 \\times 3$"

Ensure all mathematical expressions use LaTeX notation."""

    def __init__(self):
        """Initialize the LaTeX formatter agent."""
        self.llm_client = get_llm_client()
        logger.info("LaTeXFormatterAgent initialized")
    
    def format_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a numerical question to ensure proper LaTeX formatting.
        
        Args:
            question: Question dict with expected_answer and explanation
            
        Returns:
            Question dict with properly LaTeX-formatted answer and explanation
        """
        answer = question.get("expected_answer", "")
        explanation = question.get("explanation", "")
        
        # Check if already has LaTeX
        has_latex = "$" in str(answer) or "$" in str(explanation)
        
        # Check for math content that needs LaTeX
        math_patterns = [r'\d+\s*[+\-*/]\s*\d+', r'\d+\^', r'sqrt', r'sum', r'frac']
        needs_latex = any(re.search(p, str(answer), re.IGNORECASE) for p in math_patterns)
        
        # If already has LaTeX or no math content, return as-is
        if has_latex or not needs_latex:
            logger.debug("Answer already has LaTeX or no math content")
            return question
        
        try:
            prompt = self.FORMAT_PROMPT.format(answer=answer, explanation=explanation)
            
            response = self.llm_client.generate_json_message(
                prompt,
                system_message=self.SYSTEM_PROMPT
            )
            
            # Parse response
            if isinstance(response, str):
                response = json.loads(response)
            
            if isinstance(response, dict):
                question["expected_answer"] = response.get("expected_answer", answer)
                question["explanation"] = response.get("explanation", explanation)
                logger.info("Successfully formatted LaTeX answer")
            
        except Exception as e:
            logger.error(f"Error formatting LaTeX answer: {e}")
            # Return original if formatting fails
        
        return question


class DiagramFormatterAgent:
    """
    Agent to ensure diagram questions use the correct format.
    
    Supports:
    - Mermaid.js: Interactive flowcharts, sequence diagrams, etc.
    - ASCII Art: Text-based diagrams using box characters
    """
    
    MERMAID_SYSTEM_PROMPT = """You are a Mermaid.js diagram specialist.
Your job is to ensure diagram answers use proper Mermaid.js syntax:
1. Wrap diagrams in ```mermaid code blocks
2. Use correct Mermaid syntax (flowchart TD, sequenceDiagram, classDiagram, etc.)
3. Proper node definitions and connections
4. Clear labels and styling

Convert any ASCII or text diagrams to Mermaid.js format.
Always return valid JSON with the formatted content."""

    ASCII_SYSTEM_PROMPT = """You are an ASCII diagram specialist.
Your job is to ensure diagram answers use proper ASCII art:
1. Use box drawing characters (┌ ─ ┐ │ └ ┘ ├ ┤ ┬ ┴ ┼)
2. Clear structure with proper alignment
3. Arrow indicators (→ ← ↑ ↓ ──► ◄──)
4. Labels inside or beside boxes

Convert any Mermaid or text descriptions to ASCII art format.
Always return valid JSON with the formatted content."""

    MERMAID_FORMAT_PROMPT = """Convert this diagram content to Mermaid.js format:

Input Question:
{question}

Input Answer:
{answer}

Return a JSON object with:
{{
    "question_text": "question with ```mermaid diagram block",
    "expected_answer": "answer explaining the diagram with Mermaid if needed",
    "explanation": "detailed explanation"
}}

Mermaid.js examples:
```mermaid
flowchart TD
    A[Start] --> B{{Decision}}
    B -->|Yes| C[Process]
    B -->|No| D[End]
```

```mermaid
sequenceDiagram
    Client->>Server: Request
    Server-->>Client: Response
```

Ensure all diagrams use proper Mermaid.js syntax in ```mermaid blocks."""

    ASCII_FORMAT_PROMPT = """Convert this diagram content to ASCII art format:

Input Question:
{question}

Input Answer:
{answer}

Return a JSON object with:
{{
    "question_text": "question with ASCII diagram",
    "expected_answer": "answer explaining the diagram",
    "explanation": "detailed explanation"
}}

ASCII art example:
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Input     │ ──► │  Process    │ ──► │   Output    │
│   Layer     │     │   Layer     │     │   Layer     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                  │                   │
       ▼                  ▼                   ▼
   128 neurons        64 neurons          10 neurons
```

Ensure diagrams use proper box drawing characters and alignment."""

    def __init__(self):
        """Initialize the diagram formatter agent."""
        self.llm_client = get_llm_client()
        logger.info("DiagramFormatterAgent initialized")
    
    def format_question(
        self, 
        question: Dict[str, Any], 
        diagram_format: str = "mermaid"
    ) -> Dict[str, Any]:
        """
        Format a diagram question to use the specified format.
        
        Args:
            question: Question dict
            diagram_format: "mermaid" or "ascii"
            
        Returns:
            Question dict with properly formatted diagrams
        """
        question_text = question.get("question_text", "")
        answer = question.get("expected_answer", "")
        
        # Determine current format
        has_mermaid = "```mermaid" in str(question_text).lower() or "```mermaid" in str(answer).lower()
        has_ascii = any(c in str(question_text) for c in ['┌', '─', '┐', '│', '└', '┘', '├', '┤'])
        
        # Check if conversion is needed
        if diagram_format.lower() == "mermaid":
            if has_mermaid:
                logger.debug("Already has Mermaid format")
                return question
            system_prompt = self.MERMAID_SYSTEM_PROMPT
            format_prompt = self.MERMAID_FORMAT_PROMPT
        else:  # ascii
            if has_ascii and not has_mermaid:
                logger.debug("Already has ASCII format")
                return question
            system_prompt = self.ASCII_SYSTEM_PROMPT
            format_prompt = self.ASCII_FORMAT_PROMPT
        
        try:
            prompt = format_prompt.format(question=question_text, answer=answer)
            
            response = self.llm_client.generate_json_message(
                prompt,
                system_message=system_prompt
            )
            
            # Parse response
            if isinstance(response, str):
                response = json.loads(response)
            
            if isinstance(response, dict):
                question["question_text"] = response.get("question_text", question_text)
                question["expected_answer"] = response.get("expected_answer", answer)
                question["explanation"] = response.get("explanation", question.get("explanation", ""))
                logger.info(f"Successfully formatted diagram to {diagram_format}")
            
        except Exception as e:
            logger.error(f"Error formatting diagram: {e}")
            # Return original if formatting fails
        
        return question


class FormattingPipeline:
    """
    Pipeline to apply appropriate formatting agents based on question type.
    
    CRITICAL: Only applies formatting to TECHNICAL question types.
    TEXT types (MCQ, True/False, Essay, etc.) are returned UNCHANGED.
    """
    
    # TEXT TYPES - NO FORMATTING APPLIED
    TEXT_TYPES = ["Multiple Choice", "True/False", "Short Answer", "Long Answer", "Essay", "Fill in the Blank"]
    
    # TECHNICAL TYPES - Formatting applied
    CODE_TYPES = ["Code Implementation", "Code Output Prediction", "Coding", "Coding Problem"]
    MATH_TYPES = ["Numerical Problem", "Numerical", "Complexity Analysis", "Algorithm Complexity"]
    DIAGRAM_TYPES = ["Diagram-Based", "Diagram", "Flowchart", "Data Flow", "UML Diagram", "Architecture Diagram"]
    SCENARIO_TYPES = ["Scenario-Based"]
    
    def __init__(self, use_specialized_agents: bool = True):
        """
        Initialize the formatting pipeline with all agents.
        
        Args:
            use_specialized_agents: If True, uses specialized agents for enhanced formatting
        """
        # Basic formatting agents
        self.code_formatter = CodeFormatterAgent()
        self.latex_formatter = LaTeXFormatterAgent()
        self.diagram_formatter = DiagramFormatterAgent()
        
        # Specialized agents (imported from specialized_agents module)
        self.use_specialized = use_specialized_agents
        if use_specialized_agents:
            try:
                from backend.app.agents.specialized_agents import MasterFormattingOrchestrator
                self.orchestrator = MasterFormattingOrchestrator()
                logger.info("FormattingPipeline initialized with specialized agents")
            except ImportError as e:
                logger.warning(f"Could not load specialized agents: {e}")
                self.use_specialized = False
                self.orchestrator = None
        else:
            self.orchestrator = None
        
        logger.info("FormattingPipeline initialized")
    
    def format_questions(
        self,
        questions: List[Dict[str, Any]],
        question_type: str,
        diagram_format: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply appropriate formatting to a list of questions.
        
        CRITICAL: TEXT types are returned UNCHANGED - no formatting pipeline applied.
        
        Args:
            questions: List of question dicts
            question_type: Type of questions
            diagram_format: Optional diagram format for diagram questions
            
        Returns:
            List of properly formatted questions
        """
        # TEXT TYPES: Return unchanged - NO formatting pipeline
        if question_type in self.TEXT_TYPES:
            logger.info(f"Text type '{question_type}': Skipping formatting pipeline for {len(questions)} questions")
            return questions
        
        formatted_questions = []
        
        for question in questions:
            try:
                formatted_question = self._format_single_question(
                    question, question_type, diagram_format
                )
                formatted_questions.append(formatted_question)
                
            except Exception as e:
                logger.error(f"Error formatting question: {e}")
                formatted_questions.append(question)  # Add original if error
        
        logger.info(f"Formatted {len(formatted_questions)} questions of type '{question_type}'")
        return formatted_questions
    
    def _format_single_question(
        self,
        question: Dict[str, Any],
        question_type: str,
        diagram_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a single question using the appropriate agent(s).
        
        Args:
            question: Question dict
            question_type: Type of question
            diagram_format: Optional diagram format
            
        Returns:
            Formatted question dict
        """
        # TEXT TYPES should never reach here (handled in format_questions)
        # but add safety check
        if question_type in self.TEXT_TYPES:
            return question
        
        # Try specialized agents first if available
        if self.use_specialized and self.orchestrator:
            return self._format_with_orchestrator(question, question_type, diagram_format)
        
        # Fall back to basic agents
        return self._format_with_basic_agents(question, question_type, diagram_format)
    
    def _format_with_orchestrator(
        self,
        question: Dict[str, Any],
        question_type: str,
        diagram_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format question using the MasterFormattingOrchestrator for enhanced formatting.
        """
        try:
            # Format answer
            answer = question.get("expected_answer", "")
            if answer:
                formatted_answer = self.orchestrator.format_content(
                    content=answer,
                    content_type=self._get_content_type(question_type),
                    question_type=question_type,
                    diagram_format=diagram_format or "mermaid"
                )
                question["expected_answer"] = formatted_answer
            
            # Format explanation
            explanation = question.get("explanation", "")
            if explanation:
                formatted_explanation = self.orchestrator.format_content(
                    content=explanation,
                    content_type=self._get_content_type(question_type),
                    question_type=question_type,
                    diagram_format=diagram_format or "mermaid"
                )
                question["explanation"] = formatted_explanation
            
            # Format question text (especially for diagrams)
            if question_type in self.DIAGRAM_TYPES:
                question_text = question.get("question_text", "")
                if question_text:
                    formatted_text = self.orchestrator.format_content(
                        content=question_text,
                        content_type="diagram",
                        question_type=question_type,
                        diagram_format=diagram_format or "mermaid"
                    )
                    question["question_text"] = formatted_text
            
            return question
            
        except Exception as e:
            logger.warning(f"Orchestrator formatting failed, falling back to basic: {e}")
            return self._format_with_basic_agents(question, question_type, diagram_format)
    
    def _format_with_basic_agents(
        self,
        question: Dict[str, Any],
        question_type: str,
        diagram_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format question using basic formatting agents.
        """
        if question_type in self.CODE_TYPES:
            question = self.code_formatter.format_question(question)
        elif question_type in self.MATH_TYPES:
            question = self.latex_formatter.format_question(question)
        elif question_type in self.DIAGRAM_TYPES:
            fmt = "mermaid" if diagram_format and "mermaid" in diagram_format.lower() else "ascii"
            question = self.diagram_formatter.format_question(question, fmt)
        
        return question
    
    def _get_content_type(self, question_type: str) -> str:
        """
        Map question type to content type for the orchestrator.
        """
        if question_type in self.CODE_TYPES:
            return "code"
        elif question_type in self.MATH_TYPES:
            return "latex"
        elif question_type in self.DIAGRAM_TYPES:
            return "diagram"
        else:
            return "text"
    
    def format_with_specific_agent(
        self,
        content: str,
        agent_type: str,
        **kwargs
    ) -> str:
        """
        Format content with a specific specialized agent.
        
        Args:
            content: Content to format
            agent_type: Type of agent to use (e.g., "mermaid_flowchart", "latex_block")
            **kwargs: Additional arguments for the agent
            
        Returns:
            Formatted content
        """
        if not self.use_specialized or not self.orchestrator:
            logger.warning("Specialized agents not available")
            return content
        
        try:
            return self.orchestrator.format_with_agent(content, agent_type, **kwargs)
        except Exception as e:
            logger.error(f"Error using specialized agent {agent_type}: {e}")
            return content
