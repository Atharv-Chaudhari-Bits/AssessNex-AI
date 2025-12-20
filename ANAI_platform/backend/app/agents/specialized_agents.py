"""
Specialized Formatting Agents for AssessNex AI.

This module contains highly specialized agents for different content types:
- Diagram Agents: Mermaid, ASCII, Flowchart, Sequence, Class, State, ER diagrams
- Math Agents: LaTeX, Inline Math, Block Math
- Code Agents: Python, Multi-language, Syntax Validation
- Markdown Agents: Tables, Lists, Formatted Text
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from backend.app.llm_client import get_llm_client
from backend.app.utils import get_logger

logger = get_logger(__name__)


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseFormattingAgent(ABC):
    """Base class for all formatting agents."""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.agent_name = self.__class__.__name__
        logger.info(f"{self.agent_name} initialized")
    
    @abstractmethod
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        """Validate content format. Returns (is_valid, list_of_issues)."""
        pass
    
    @abstractmethod
    def format(self, content: str) -> str:
        """Format content to proper specification."""
        pass
    
    def process(self, content: str) -> str:
        """Validate and format content."""
        is_valid, issues = self.validate(content)
        if not is_valid:
            logger.info(f"{self.agent_name}: Found {len(issues)} issues, reformatting...")
            return self.format(content)
        return content


# =============================================================================
# DIAGRAM AGENTS
# =============================================================================

class MermaidFlowchartAgent(BaseFormattingAgent):
    """Agent for Mermaid Flowchart diagrams."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js flowchart specialist. Convert content to valid Mermaid flowchart syntax.
    
Rules:
- Start with 'flowchart TD' (top-down) or 'flowchart LR' (left-right)
- Nodes: A[Rectangle], B(Rounded), C{Diamond}, D((Circle)), E[[Subroutine]]
- Connections: -->, ---, -.->. -.->, ==>
- Labels: A -->|label| B
- Subgraphs: subgraph title ... end

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for mermaid code block
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        # Check for flowchart declaration
        if not re.search(r'flowchart\s+(TD|TB|BT|RL|LR)', content, re.IGNORECASE):
            issues.append("Missing flowchart direction declaration")
        
        # Check for valid node definitions
        if not re.search(r'[A-Za-z_]\w*\s*[\[\(\{\<]', content):
            issues.append("No valid node definitions found")
        
        # Check for connections
        if not re.search(r'--[->]|==>', content):
            issues.append("No connections found")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid flowchart:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks. No explanations."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidFlowchartAgent format error: {e}")
            return content


class MermaidSequenceAgent(BaseFormattingAgent):
    """Agent for Mermaid Sequence diagrams."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js sequence diagram specialist.
    
Rules:
- Start with 'sequenceDiagram'
- Participants: participant A as Alice
- Messages: A->>B: Message (sync), A-->>B: Response (async)
- Notes: Note over A,B: Text
- Loops: loop Label ... end
- Alt: alt Condition ... else ... end

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        if 'sequenceDiagram' not in content:
            issues.append("Missing sequenceDiagram declaration")
        
        if not re.search(r'->>|-->>|->|-->', content):
            issues.append("No message arrows found")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid sequence diagram:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidSequenceAgent format error: {e}")
            return content


class MermaidClassAgent(BaseFormattingAgent):
    """Agent for Mermaid Class diagrams."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js class diagram specialist.
    
Rules:
- Start with 'classDiagram'
- Classes: class ClassName { +method() -attribute }
- Visibility: + public, - private, # protected, ~ package
- Relationships: <|-- inheritance, *-- composition, o-- aggregation, --> association
- Labels: A "1" --> "*" B : has

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        if 'classDiagram' not in content:
            issues.append("Missing classDiagram declaration")
        
        if not re.search(r'class\s+\w+|<\|--|--\*|--o|-->', content):
            issues.append("No class definitions or relationships found")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid class diagram:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidClassAgent format error: {e}")
            return content


class MermaidStateAgent(BaseFormattingAgent):
    """Agent for Mermaid State diagrams."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js state diagram specialist.
    
Rules:
- Start with 'stateDiagram-v2'
- States: state "Description" as s1
- Transitions: s1 --> s2 : event
- Start/End: [*] --> s1 and s1 --> [*]
- Composite: state CompositeState { ... }
- Fork/Join: state fork_state <<fork>>

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        if 'stateDiagram' not in content:
            issues.append("Missing stateDiagram declaration")
        
        if not re.search(r'\[\*\]|-->', content):
            issues.append("No state transitions found")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid state diagram:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidStateAgent format error: {e}")
            return content


class MermaidERAgent(BaseFormattingAgent):
    """Agent for Mermaid Entity-Relationship diagrams."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js ER diagram specialist.
    
Rules:
- Start with 'erDiagram'
- Entities with attributes: ENTITY { type name }
- Relationships: ENTITY1 ||--o{ ENTITY2 : relationship
- Cardinality: || one, |{ many, o| zero-or-one, o{ zero-or-many

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        if 'erDiagram' not in content:
            issues.append("Missing erDiagram declaration")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid ER diagram:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidERAgent format error: {e}")
            return content


class ASCIIDiagramAgent(BaseFormattingAgent):
    """Agent for ASCII art diagrams."""
    
    SYSTEM_PROMPT = """You are an ASCII diagram specialist.
    
Rules:
- Use box drawing characters: ┌ ─ ┐ │ └ ┘ ├ ┤ ┬ ┴ ┼
- Arrows: → ← ↑ ↓ ↔ ↕ ──► ◄── ▲ ▼
- Corners: ╭ ╮ ╰ ╯ (rounded)
- Double lines: ╔ ═ ╗ ║ ╚ ╝
- Proper alignment and spacing
- Labels centered in boxes

Create clear, well-aligned ASCII diagrams."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        ascii_chars = ['┌', '─', '┐', '│', '└', '┘', '├', '┤', '┬', '┴', '┼',
                       '╔', '═', '╗', '║', '╚', '╝', '→', '←', '↑', '↓', '►', '◄']
        
        has_ascii = any(c in content for c in ascii_chars)
        
        if not has_ascii:
            issues.append("No ASCII box drawing characters found")
        
        # Check for alignment (lines should have consistent structure)
        lines = content.split('\n')
        if len(lines) < 3:
            issues.append("Diagram appears too simple")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a proper ASCII diagram using box drawing characters:

{content}

Use characters like: ┌ ─ ┐ │ └ ┘ ├ ┤ → ← ↑ ↓ ──►
Return ONLY the ASCII diagram. No explanations."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"ASCIIDiagramAgent format error: {e}")
            return content


class MermaidGanttAgent(BaseFormattingAgent):
    """Agent for Mermaid Gantt charts."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js Gantt chart specialist.
    
Rules:
- Start with 'gantt'
- Title: title Chart Title
- Date format: dateFormat YYYY-MM-DD
- Sections: section Section Name
- Tasks: Task Name :id, start_date, duration (or end_date)
- Dependencies: Task :after id, duration

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        if 'gantt' not in content.lower():
            issues.append("Missing gantt declaration")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid Gantt chart:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidGanttAgent format error: {e}")
            return content


class MermaidPieAgent(BaseFormattingAgent):
    """Agent for Mermaid Pie charts."""
    
    SYSTEM_PROMPT = """You are a Mermaid.js pie chart specialist.
    
Rules:
- Start with 'pie showData' or 'pie'
- Title: title Chart Title
- Data: "Label" : value

Always wrap in ```mermaid code blocks."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```mermaid' not in content.lower():
            issues.append("Missing ```mermaid code block")
        
        if 'pie' not in content.lower():
            issues.append("Missing pie declaration")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Convert this to a valid Mermaid pie chart:

{content}

Return ONLY the Mermaid code wrapped in ```mermaid blocks."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MermaidPieAgent format error: {e}")
            return content


# =============================================================================
# LATEX / MATH AGENTS
# =============================================================================

class LaTeXBlockAgent(BaseFormattingAgent):
    """Agent for block LaTeX equations ($$...$$)."""
    
    SYSTEM_PROMPT = """You are a LaTeX mathematical notation specialist.
    
Rules for BLOCK equations ($$...$$):
- Use $$ delimiters for display math
- Proper commands: \\frac{}{}, \\sum_{}, \\int_{}, \\prod_{}
- Matrices: \\begin{bmatrix}...\\end{bmatrix}
- Aligned equations: \\begin{aligned}...\\end{aligned}
- Greek letters: \\alpha, \\beta, \\gamma, etc.
- Operators: \\times, \\div, \\cdot, \\pm

Return properly formatted LaTeX."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for block math delimiters
        if '$$' not in content:
            issues.append("No block math delimiters ($$) found")
        
        # Check for balanced delimiters
        count = content.count('$$')
        if count % 2 != 0:
            issues.append("Unbalanced $$ delimiters")
        
        # Check for common LaTeX issues
        if '\\\\' in content and '\\begin' not in content:
            # Double backslash without environment might be an error
            pass
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Format this mathematical content with proper LaTeX block notation:

{content}

Use $$ delimiters for display equations. Return the formatted content."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"LaTeXBlockAgent format error: {e}")
            return content


class LaTeXInlineAgent(BaseFormattingAgent):
    """Agent for inline LaTeX expressions ($...$)."""
    
    SYSTEM_PROMPT = """You are a LaTeX inline notation specialist.
    
Rules for INLINE equations ($...$):
- Use single $ delimiters
- Keep expressions concise
- Common: $x^2$, $\\frac{a}{b}$, $\\sqrt{n}$
- Variables: $x$, $y$, $n$
- Subscripts/superscripts: $x_i$, $x^2$, $x_i^2$

Return text with properly formatted inline LaTeX."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for inline math
        inline_pattern = r'(?<!\$)\$(?!\$)[^\$]+\$(?!\$)'
        if not re.search(inline_pattern, content):
            # Check if there's math content that should be wrapped
            math_indicators = [r'\d+\s*[+\-*/=]\s*\d+', r'[a-z]\s*=', r'x\^', r'n\^']
            has_math = any(re.search(p, content) for p in math_indicators)
            if has_math:
                issues.append("Math content found but not wrapped in $ delimiters")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Add proper inline LaTeX notation ($...$) to mathematical expressions:

{content}

Wrap variables, equations, and math symbols in single $ delimiters.
Return the formatted content."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"LaTeXInlineAgent format error: {e}")
            return content


class MathExpressionAgent(BaseFormattingAgent):
    """Agent for complete mathematical expression formatting."""
    
    SYSTEM_PROMPT = """You are a comprehensive mathematical notation specialist.
    
Your job is to ensure ALL mathematical content is properly formatted:
1. Simple expressions: $x + y = z$
2. Fractions: $\\frac{numerator}{denominator}$
3. Roots: $\\sqrt{x}$, $\\sqrt[n]{x}$
4. Sums/Products: $\\sum_{i=1}^{n}$, $\\prod_{i=1}^{n}$
5. Integrals: $\\int_{a}^{b} f(x) dx$
6. Limits: $\\lim_{x \\to \\infty}$
7. Matrices: Use \\begin{bmatrix}...\\end{bmatrix}
8. Greek: $\\alpha, \\beta, \\gamma, \\theta, \\lambda$
9. Complexity: $O(n^2)$, $O(n \\log n)$
10. Probability: $P(A|B)$, $E[X]$

Use $ for inline, $$ for block equations."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Patterns that indicate unformatted math
        unformatted_patterns = [
            (r'(?<!\$)\b\d+\s*[+\-*/]\s*\d+\b(?!\$)', "Arithmetic without LaTeX"),
            (r'(?<!\$)\bO\(n', "Complexity notation without LaTeX"),
            (r'(?<!\$)\bsqrt\(', "sqrt without LaTeX"),
            (r'(?<!\$)\bsum\b', "sum without LaTeX"),
            (r'(?<!\$)\bfrac\b', "frac without LaTeX"),
        ]
        
        for pattern, msg in unformatted_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(msg)
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Format ALL mathematical content with proper LaTeX:

{content}

Rules:
- Wrap inline math in $...$
- Wrap block equations in $$...$$
- Use proper LaTeX commands
- Preserve non-math text

Return the fully formatted content."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MathExpressionAgent format error: {e}")
            return content


# =============================================================================
# CODE AGENTS
# =============================================================================

class PythonCodeAgent(BaseFormattingAgent):
    """Agent for Python code formatting."""
    
    SYSTEM_PROMPT = """You are a Python code formatting specialist.
    
Rules:
1. Wrap code in ```python blocks
2. Proper indentation (4 spaces)
3. PEP 8 style guidelines
4. Docstrings for functions/classes
5. Type hints where appropriate
6. Comments for complex logic
7. Proper imports at top

Return properly formatted Python code."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for code block
        if '```python' not in content.lower() and '```' not in content:
            if any(kw in content for kw in ['def ', 'class ', 'import ', 'from ']):
                issues.append("Python code not wrapped in ```python block")
        
        # Check indentation
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('\t'):
                issues.append(f"Line {i+1}: Uses tabs instead of spaces")
                break
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Format this Python code properly:

{content}

Rules:
- Wrap in ```python blocks
- Use 4-space indentation
- Add docstrings if missing
- Follow PEP 8

Return the formatted code."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"PythonCodeAgent format error: {e}")
            return content


class MultiLanguageCodeAgent(BaseFormattingAgent):
    """Agent for multi-language code formatting."""
    
    LANGUAGE_HINTS = {
        'javascript': ['function ', 'const ', 'let ', 'var ', '=>', 'console.log'],
        'java': ['public class', 'public static void', 'System.out'],
        'cpp': ['#include', 'std::', 'cout', 'int main()'],
        'sql': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE'],
        'python': ['def ', 'class ', 'import ', 'from ', 'print('],
    }
    
    def detect_language(self, content: str) -> str:
        """Detect programming language from content."""
        for lang, hints in self.LANGUAGE_HINTS.items():
            if any(hint in content for hint in hints):
                return lang
        return 'python'  # Default
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if '```' not in content:
            # Check if it looks like code
            code_indicators = ['def ', 'function ', 'class ', 'import ', 'SELECT ', '#include']
            if any(ind in content for ind in code_indicators):
                issues.append("Code not wrapped in ``` blocks")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            lang = self.detect_language(content)
            prompt = f"""Format this {lang} code properly:

{content}

Wrap in ```{lang} blocks with proper formatting.
Return the formatted code."""
            
            response = self.llm_client.generate_message(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"MultiLanguageCodeAgent format error: {e}")
            return content


class CodeWithDescriptionAgent(BaseFormattingAgent):
    """Agent to ensure code has proper descriptions."""
    
    SYSTEM_PROMPT = """You are a code documentation specialist.
    
Ensure code answers have:
1. Brief description BEFORE the code explaining what it does
2. Code wrapped in appropriate ``` blocks
3. Comments within code for complex parts
4. Brief note AFTER about time/space complexity if relevant

Format: Description → Code Block → Notes (optional)"""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        has_code = '```' in content
        
        if has_code:
            # Check for description before code
            code_start = content.find('```')
            before_code = content[:code_start].strip()
            
            if len(before_code) < 20:
                issues.append("Missing or too short description before code")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Add proper description to this code:

{content}

Format:
1. Add a clear description before the code (2-3 sentences)
2. Keep the code in ``` blocks
3. Add brief notes about complexity if relevant

Return the complete formatted answer."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"CodeWithDescriptionAgent format error: {e}")
            return content


# =============================================================================
# MARKDOWN AGENTS
# =============================================================================

class MarkdownTableAgent(BaseFormattingAgent):
    """Agent for Markdown table formatting."""
    
    SYSTEM_PROMPT = """You are a Markdown table specialist.
    
Rules:
- Header row with | separators
- Separator row with dashes: |---|---|
- Alignment: :--- left, :---: center, ---: right
- Consistent column widths
- Proper escaping of | in content

Create well-formatted, aligned tables."""

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for table structure
        if '|' in content:
            lines = [l for l in content.split('\n') if '|' in l]
            if len(lines) >= 2:
                # Check for separator row
                if not any(re.match(r'\|[\s\-:]+\|', l) for l in lines):
                    issues.append("Missing table separator row")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Format this as a proper Markdown table:

{content}

Use | for columns, add header separator row.
Return the formatted table."""
            
            response = self.llm_client.generate_message(prompt, system_message=self.SYSTEM_PROMPT)
            return response.strip()
        except Exception as e:
            logger.error(f"MarkdownTableAgent format error: {e}")
            return content


class MarkdownListAgent(BaseFormattingAgent):
    """Agent for Markdown list formatting."""
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for list markers
        list_patterns = [r'^\s*[-*+]\s', r'^\s*\d+\.\s']
        has_list = any(re.search(p, content, re.MULTILINE) for p in list_patterns)
        
        if has_list:
            # Check for consistent markers
            lines = content.split('\n')
            markers = set()
            for line in lines:
                if re.match(r'^\s*[-*+]\s', line):
                    markers.add(line.strip()[0])
            
            if len(markers) > 1:
                issues.append("Inconsistent list markers")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        try:
            prompt = f"""Format this as a proper Markdown list:

{content}

Use consistent markers (- for unordered, 1. 2. 3. for ordered).
Proper indentation for nested items.
Return the formatted list."""
            
            response = self.llm_client.generate_message(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"MarkdownListAgent format error: {e}")
            return content


class MarkdownFormattingAgent(BaseFormattingAgent):
    """Agent for general Markdown formatting (bold, italic, headers, etc.)."""
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        issues = []
        
        # Check for unbalanced formatting
        bold_count = len(re.findall(r'\*\*', content))
        if bold_count % 2 != 0:
            issues.append("Unbalanced ** (bold) markers")
        
        italic_count = len(re.findall(r'(?<!\*)\*(?!\*)', content))
        if italic_count % 2 != 0:
            issues.append("Unbalanced * (italic) markers")
        
        return len(issues) == 0, issues
    
    def format(self, content: str) -> str:
        # Simple fixes for common issues
        # Balance bold markers
        content = re.sub(r'\*\*([^*]+)$', r'**\1**', content)
        return content


# =============================================================================
# MASTER ORCHESTRATOR
# =============================================================================

class DiagramAgentOrchestrator:
    """Orchestrates all diagram-related agents."""
    
    def __init__(self):
        self.flowchart_agent = MermaidFlowchartAgent()
        self.sequence_agent = MermaidSequenceAgent()
        self.class_agent = MermaidClassAgent()
        self.state_agent = MermaidStateAgent()
        self.er_agent = MermaidERAgent()
        self.gantt_agent = MermaidGanttAgent()
        self.pie_agent = MermaidPieAgent()
        self.ascii_agent = ASCIIDiagramAgent()
        logger.info("DiagramAgentOrchestrator initialized with all diagram agents")
    
    def detect_diagram_type(self, content: str) -> str:
        """Detect the type of diagram from content."""
        content_lower = content.lower()
        
        if 'sequencediagram' in content_lower or '->>':
            return 'sequence'
        elif 'classdiagram' in content_lower:
            return 'class'
        elif 'statediagram' in content_lower:
            return 'state'
        elif 'erdiagram' in content_lower:
            return 'er'
        elif 'gantt' in content_lower:
            return 'gantt'
        elif 'pie' in content_lower:
            return 'pie'
        elif any(c in content for c in ['┌', '─', '│', '└', '├']):
            return 'ascii'
        else:
            return 'flowchart'  # Default
    
    def process(self, content: str, preferred_format: str = "mermaid") -> str:
        """Process content with appropriate diagram agent."""
        if preferred_format.lower() == "ascii":
            return self.ascii_agent.process(content)
        
        diagram_type = self.detect_diagram_type(content)
        
        agent_map = {
            'flowchart': self.flowchart_agent,
            'sequence': self.sequence_agent,
            'class': self.class_agent,
            'state': self.state_agent,
            'er': self.er_agent,
            'gantt': self.gantt_agent,
            'pie': self.pie_agent,
            'ascii': self.ascii_agent,
        }
        
        agent = agent_map.get(diagram_type, self.flowchart_agent)
        return agent.process(content)


class MathAgentOrchestrator:
    """Orchestrates all math/LaTeX agents."""
    
    def __init__(self):
        self.block_agent = LaTeXBlockAgent()
        self.inline_agent = LaTeXInlineAgent()
        self.expression_agent = MathExpressionAgent()
        logger.info("MathAgentOrchestrator initialized with all math agents")
    
    def process(self, content: str) -> str:
        """Process content with appropriate math formatting."""
        # Use the comprehensive expression agent for all math content
        return self.expression_agent.process(content)


class CodeAgentOrchestrator:
    """Orchestrates all code formatting agents."""
    
    def __init__(self):
        self.python_agent = PythonCodeAgent()
        self.multi_lang_agent = MultiLanguageCodeAgent()
        self.description_agent = CodeWithDescriptionAgent()
        logger.info("CodeAgentOrchestrator initialized with all code agents")
    
    def process(self, content: str, ensure_description: bool = True) -> str:
        """Process content with appropriate code formatting."""
        # First ensure proper code formatting
        lang = self.multi_lang_agent.detect_language(content)
        
        if lang == 'python':
            content = self.python_agent.process(content)
        else:
            content = self.multi_lang_agent.process(content)
        
        # Then ensure description exists
        if ensure_description:
            content = self.description_agent.process(content)
        
        return content


class MarkdownAgentOrchestrator:
    """Orchestrates all markdown formatting agents."""
    
    def __init__(self):
        self.table_agent = MarkdownTableAgent()
        self.list_agent = MarkdownListAgent()
        self.formatting_agent = MarkdownFormattingAgent()
        logger.info("MarkdownAgentOrchestrator initialized")
    
    def process(self, content: str) -> str:
        """Process content with markdown formatting."""
        # Apply formatting fixes
        content = self.formatting_agent.process(content)
        
        # Check for tables
        if '|' in content:
            content = self.table_agent.process(content)
        
        # Check for lists
        if re.search(r'^\s*[-*+\d]\s', content, re.MULTILINE):
            content = self.list_agent.process(content)
        
        return content


# =============================================================================
# MASTER FORMATTING ORCHESTRATOR
# =============================================================================

class MasterFormattingOrchestrator:
    """
    Master orchestrator that coordinates all formatting agents.
    
    This is the main entry point for formatting any content type.
    It automatically detects content type and routes to appropriate agents.
    """
    
    def __init__(self):
        """Initialize all sub-orchestrators."""
        self.diagram_orchestrator = DiagramAgentOrchestrator()
        self.math_orchestrator = MathAgentOrchestrator()
        self.code_orchestrator = CodeAgentOrchestrator()
        self.markdown_orchestrator = MarkdownAgentOrchestrator()
        
        # Individual agents for direct access
        self.agents = {
            # Mermaid diagram agents
            "mermaid_flowchart": MermaidFlowchartAgent(),
            "mermaid_sequence": MermaidSequenceAgent(),
            "mermaid_class": MermaidClassAgent(),
            "mermaid_state": MermaidStateAgent(),
            "mermaid_er": MermaidERAgent(),
            "mermaid_gantt": MermaidGanttAgent(),
            "mermaid_pie": MermaidPieAgent(),
            "ascii_diagram": ASCIIDiagramAgent(),
            # Math agents
            "latex_block": LaTeXBlockAgent(),
            "latex_inline": LaTeXInlineAgent(),
            "math_expression": MathExpressionAgent(),
            # Code agents
            "code_python": PythonCodeAgent(),
            "code_multi": MultiLanguageCodeAgent(),
            "code_with_description": CodeWithDescriptionAgent(),
            # Markdown agents
            "markdown_table": MarkdownTableAgent(),
            "markdown_list": MarkdownListAgent(),
        }
        
        logger.info("MasterFormattingOrchestrator initialized with all agents")
    
    def detect_content_type(self, content: str) -> str:
        """
        Auto-detect the primary content type.
        
        Returns: 'diagram', 'code', 'latex', 'markdown', or 'text'
        """
        content_lower = content.lower()
        
        # Check for diagrams
        if '```mermaid' in content_lower or any(kw in content_lower for kw in 
            ['flowchart', 'sequencediagram', 'classdiagram', 'statediagram', 'erdiagram', 'gantt', 'pie']):
            return 'diagram'
        
        # Check for ASCII diagrams
        if any(c in content for c in ['┌', '─', '│', '└', '├', '┬', '┤']):
            return 'diagram'
        
        # Check for code blocks
        if '```' in content and re.search(r'```(?:python|javascript|java|cpp|sql|bash|typescript)', content_lower):
            return 'code'
        
        # Check for code patterns without blocks
        if re.search(r'\bdef\s+\w+\s*\(|\bclass\s+\w+|\bfunction\s+\w+', content):
            return 'code'
        
        # Check for LaTeX/math
        if '$' in content or '\\frac' in content or '\\sum' in content:
            return 'latex'
        
        # Check for math expressions
        if re.search(r'\d+\s*[+\-*/^]\s*\d+|sqrt|sum|integral', content_lower):
            return 'latex'
        
        # Check for markdown tables
        if '|' in content and re.search(r'\|[-:]+\|', content):
            return 'markdown'
        
        return 'text'
    
    def format_content(
        self,
        content: str,
        content_type: Optional[str] = None,
        question_type: Optional[str] = None,
        diagram_format: str = "mermaid",
        ensure_description: bool = True,
    ) -> str:
        """
        Format content using appropriate agents.
        
        Args:
            content: The content to format
            content_type: Override auto-detection ('diagram', 'code', 'latex', 'markdown')
            question_type: The type of question (for context)
            diagram_format: Preferred diagram format ('mermaid' or 'ascii')
            ensure_description: For code, ensure text description exists
            
        Returns:
            Formatted content
        """
        if not content or not content.strip():
            return content
        
        # Auto-detect if not specified
        if content_type is None:
            content_type = self.detect_content_type(content)
        
        try:
            if content_type == 'diagram':
                return self.diagram_orchestrator.process(content, diagram_format)
            
            elif content_type == 'code':
                return self.code_orchestrator.process(content, ensure_description)
            
            elif content_type == 'latex':
                return self.math_orchestrator.process(content)
            
            elif content_type == 'markdown':
                return self.markdown_orchestrator.process(content)
            
            else:
                # For plain text, just apply basic markdown formatting
                return self.markdown_orchestrator.process(content)
                
        except Exception as e:
            logger.error(f"Error formatting content: {e}")
            return content  # Return original on error
    
    def format_with_agent(
        self,
        content: str,
        agent_type: str,
        **kwargs
    ) -> str:
        """
        Format content with a specific agent.
        
        Args:
            content: Content to format
            agent_type: Agent key (e.g., 'mermaid_flowchart', 'latex_block')
            **kwargs: Additional arguments for the agent
            
        Returns:
            Formatted content
        """
        agent = self.agents.get(agent_type)
        
        if agent is None:
            logger.warning(f"Unknown agent type: {agent_type}")
            return content
        
        try:
            return agent.process(content)
        except Exception as e:
            logger.error(f"Error using agent {agent_type}: {e}")
            return content
    
    def validate_and_fix(
        self,
        content: str,
        content_type: Optional[str] = None,
    ) -> Tuple[str, List[str]]:
        """
        Validate content and fix any issues.
        
        Returns:
            Tuple of (fixed_content, list_of_issues_found)
        """
        if content_type is None:
            content_type = self.detect_content_type(content)
        
        issues = []
        fixed_content = content
        
        # Get appropriate agents based on content type
        if content_type == 'diagram':
            # Check for mermaid block
            if '```mermaid' not in content.lower() and not any(c in content for c in ['┌', '─', '│']):
                issues.append("Diagram not wrapped in code block")
            fixed_content = self.diagram_orchestrator.process(content)
            
        elif content_type == 'code':
            # Check for code block
            if '```' not in content:
                issues.append("Code not wrapped in code block")
            fixed_content = self.code_orchestrator.process(content)
            
        elif content_type == 'latex':
            # Check for latex delimiters
            if '$' not in content and '\\' not in content:
                issues.append("Math expressions not in LaTeX format")
            fixed_content = self.math_orchestrator.process(content)
        
        return fixed_content, issues

