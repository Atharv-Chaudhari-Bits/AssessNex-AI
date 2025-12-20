"""
Supervisor Agent - Validates outputs and triggers regeneration.

Features:
- Output validation
- Quality assessment
- LLM-based verification
- Automatic regeneration on failure
- Error tracking and reporting
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
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


class ValidationStatus(Enum):
    """Status of validation."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationRule:
    """A validation rule to apply."""
    name: str
    description: str
    validator: Callable[[str], Tuple[bool, str]]
    severity: str = "error"  # error, warning, info
    auto_fix: bool = False


@dataclass
class ValidationReport:
    """Report from validation."""
    status: ValidationStatus
    passed_rules: List[str] = field(default_factory=list)
    failed_rules: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    score: float = 1.0  # 0.0 to 1.0


class SupervisorAgent(BaseFormattingAgent):
    """
    Supervises formatting outputs and ensures quality.
    
    Responsibilities:
    1. Validate formatted output against rules
    2. Check syntax and structure
    3. Verify content completeness
    4. Trigger regeneration if needed
    5. Track and report errors
    """
    
    def __init__(self, llm_client=None):
        super().__init__(llm_client)
        self._validation_rules: Dict[str, List[ValidationRule]] = {}
        self._setup_default_rules()
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="SupervisorAgent",
            content_type=ContentType.MIXED,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a quality assurance specialist for formatted content. Your role is to:

1. VALIDATE formatted output against expected patterns
2. CHECK for syntax errors and structural issues
3. VERIFY completeness and correctness
4. SUGGEST improvements or corrections
5. DETERMINE if content needs regeneration

VALIDATION CHECKS:
==================

MERMAID DIAGRAMS:
- Syntax: proper keywords (graph, flowchart, sequenceDiagram, etc.)
- Structure: valid node definitions, proper connections
- Completeness: all referenced nodes exist

LATEX/MATH:
- Balanced delimiters: $...$ or $$...$$
- Valid commands: \\frac, \\sqrt, etc.
- Proper escaping

CODE:
- Syntax validity
- Proper formatting
- Complete structure

ASCII ART:
- Alignment
- Consistent characters
- Proper connections

Return detailed validation results with specific issues found."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        content_type = kwargs.get("content_type", "unknown")
        
        return f"""Validate this {content_type} content for correctness.

CONTENT:
{content}

Check for:
1. Syntax errors
2. Structural issues
3. Missing elements
4. Formatting problems

Return JSON with:
{{
    "is_valid": true/false,
    "errors": ["error1", "error2"],
    "warnings": ["warning1"],
    "suggestions": ["suggestion1"],
    "corrected_content": "..." (if corrections needed)
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Basic validation."""
        return True, []
    
    def _is_already_formatted(self, content: str) -> bool:
        """Supervisor always validates."""
        return False
    
    def _setup_default_rules(self):
        """Set up default validation rules for different content types."""
        
        # Mermaid validation rules
        self._validation_rules["mermaid"] = [
            ValidationRule(
                name="mermaid_syntax",
                description="Check Mermaid diagram syntax",
                validator=self._validate_mermaid_syntax,
                severity="error",
            ),
            ValidationRule(
                name="mermaid_structure",
                description="Check Mermaid diagram structure",
                validator=self._validate_mermaid_structure,
                severity="error",
            ),
        ]
        
        # LaTeX validation rules
        self._validation_rules["latex"] = [
            ValidationRule(
                name="latex_delimiters",
                description="Check LaTeX delimiter balance",
                validator=self._validate_latex_delimiters,
                severity="error",
            ),
            ValidationRule(
                name="latex_commands",
                description="Check LaTeX command validity",
                validator=self._validate_latex_commands,
                severity="warning",
            ),
        ]
        
        # Code validation rules
        self._validation_rules["code"] = [
            ValidationRule(
                name="code_blocks",
                description="Check code block syntax",
                validator=self._validate_code_blocks,
                severity="error",
            ),
            ValidationRule(
                name="code_indentation",
                description="Check code indentation",
                validator=self._validate_indentation,
                severity="warning",
            ),
        ]
        
        # ASCII validation rules
        self._validation_rules["ascii"] = [
            ValidationRule(
                name="ascii_alignment",
                description="Check ASCII art alignment",
                validator=self._validate_ascii_alignment,
                severity="warning",
            ),
        ]
    
    def _validate_mermaid_syntax(self, content: str) -> Tuple[bool, str]:
        """Validate Mermaid diagram syntax."""
        mermaid_match = re.search(r'```mermaid\n([\s\S]*?)```', content)
        if not mermaid_match:
            return True, ""  # No mermaid, skip
        
        mermaid_code = mermaid_match.group(1)
        
        # Check for valid diagram type
        valid_types = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap'
        ]
        
        has_valid_type = any(vt in mermaid_code for vt in valid_types)
        if not has_valid_type:
            return False, "No valid Mermaid diagram type found"
        
        # Check for unbalanced brackets
        if mermaid_code.count('[') != mermaid_code.count(']'):
            return False, "Unbalanced square brackets in Mermaid"
        
        if mermaid_code.count('{') != mermaid_code.count('}'):
            return False, "Unbalanced curly brackets in Mermaid"
        
        return True, ""
    
    def _validate_mermaid_structure(self, content: str) -> Tuple[bool, str]:
        """Validate Mermaid diagram structure."""
        mermaid_match = re.search(r'```mermaid\n([\s\S]*?)```', content)
        if not mermaid_match:
            return True, ""
        
        mermaid_code = mermaid_match.group(1).strip()
        lines = mermaid_code.split('\n')
        
        if len(lines) < 2:
            return False, "Mermaid diagram too short"
        
        return True, ""
    
    def _validate_latex_delimiters(self, content: str) -> Tuple[bool, str]:
        """Validate LaTeX delimiter balance."""
        # Check inline math
        inline_opens = content.count('$') - content.count('$$') * 2
        if inline_opens % 2 != 0:
            return False, "Unbalanced inline math delimiters ($)"
        
        # Check block math
        block_opens = content.count('$$')
        if block_opens % 2 != 0:
            return False, "Unbalanced block math delimiters ($$)"
        
        # Check begin/end environments
        begins = len(re.findall(r'\\begin\{(\w+)\}', content))
        ends = len(re.findall(r'\\end\{(\w+)\}', content))
        if begins != ends:
            return False, f"Unbalanced LaTeX environments (begin: {begins}, end: {ends})"
        
        return True, ""
    
    def _validate_latex_commands(self, content: str) -> Tuple[bool, str]:
        """Validate common LaTeX commands."""
        # Check for common typos
        typos = [
            (r'\\frak\b', '\\frac'),
            (r'\\sqr\b', '\\sqrt'),
            (r'\\summ\b', '\\sum'),
        ]
        
        for typo_pattern, correct in typos:
            if re.search(typo_pattern, content):
                return False, f"Possible typo: use {correct}"
        
        return True, ""
    
    def _validate_code_blocks(self, content: str) -> Tuple[bool, str]:
        """Validate code block syntax."""
        opens = content.count('```')
        if opens % 2 != 0:
            return False, "Unbalanced code block delimiters (```)"
        
        return True, ""
    
    def _validate_indentation(self, content: str) -> Tuple[bool, str]:
        """Validate code indentation consistency."""
        code_blocks = re.findall(r'```\w*\n([\s\S]*?)```', content)
        
        for block in code_blocks:
            lines = block.split('\n')
            indent_chars = set()
            
            for line in lines:
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    if leading > 0:
                        indent_chars.add(line[0])
            
            if len(indent_chars) > 1 and '\t' in indent_chars and ' ' in indent_chars:
                return False, "Mixed tabs and spaces in code"
        
        return True, ""
    
    def _validate_ascii_alignment(self, content: str) -> Tuple[bool, str]:
        """Validate ASCII art alignment."""
        # Simple check - look for box characters
        box_chars = set('┌┬┐├┼┤└┴┘│─')
        has_box = any(c in content for c in box_chars)
        
        if has_box:
            lines = content.split('\n')
            # Check for broken lines
            for line in lines:
                if '│' in line:
                    # Should have matching │ at start and end for tables
                    stripped = line.strip()
                    if stripped.startswith('│') and not stripped.endswith('│'):
                        return False, "Misaligned ASCII table borders"
        
        return True, ""
    
    def validate_content(
        self,
        content: str,
        content_type: str = None,
    ) -> ValidationReport:
        """
        Validate content against all applicable rules.
        
        Args:
            content: The content to validate
            content_type: Optional specific content type
            
        Returns:
            ValidationReport with results
        """
        report = ValidationReport(status=ValidationStatus.PASSED)
        
        # Determine which rule sets to apply
        rule_sets = []
        if content_type:
            if content_type in self._validation_rules:
                rule_sets.append(content_type)
        else:
            # Auto-detect and apply all relevant rules
            if 'mermaid' in content.lower() or '```mermaid' in content:
                rule_sets.append("mermaid")
            if '$' in content or '\\' in content:
                rule_sets.append("latex")
            if '```' in content:
                rule_sets.append("code")
            if any(c in content for c in '┌┬┐├┼┤└┴┘'):
                rule_sets.append("ascii")
        
        # Apply rules
        total_rules = 0
        passed_rules = 0
        
        for rule_set_name in rule_sets:
            rules = self._validation_rules.get(rule_set_name, [])
            
            for rule in rules:
                total_rules += 1
                is_valid, error_msg = rule.validator(content)
                
                if is_valid:
                    passed_rules += 1
                    report.passed_rules.append(rule.name)
                else:
                    report.failed_rules.append({
                        "rule": rule.name,
                        "description": rule.description,
                        "error": error_msg,
                        "severity": rule.severity,
                    })
                    
                    if rule.severity == "error":
                        report.status = ValidationStatus.FAILED
                    elif rule.severity == "warning" and report.status != ValidationStatus.FAILED:
                        report.status = ValidationStatus.WARNING
                        report.warnings.append(error_msg)
        
        # Calculate score
        if total_rules > 0:
            report.score = passed_rules / total_rules
        
        return report
    
    async def validate_with_llm(
        self,
        content: str,
        content_type: str = None,
    ) -> ValidationReport:
        """
        Use LLM for advanced validation.
        
        Args:
            content: The content to validate
            content_type: The type of content
            
        Returns:
            ValidationReport with LLM-based validation
        """
        prompt = self._get_format_prompt(content, content_type=content_type or "mixed")
        
        try:
            response = await self._call_llm(prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    report = ValidationReport(
                        status=ValidationStatus.PASSED if result.get("is_valid", True) else ValidationStatus.FAILED,
                        failed_rules=[{"rule": "llm_validation", "error": e} for e in result.get("errors", [])],
                        warnings=result.get("warnings", []),
                        suggestions=result.get("suggestions", []),
                    )
                    
                    return report
            except json.JSONDecodeError:
                pass
            
            # Fallback to basic report
            return ValidationReport(
                status=ValidationStatus.WARNING,
                warnings=["Could not parse LLM validation response"],
            )
            
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return ValidationReport(
                status=ValidationStatus.SKIPPED,
                warnings=[f"LLM validation skipped: {str(e)}"],
            )
    
    async def supervise_and_fix(
        self,
        content: str,
        formatting_agent: BaseFormattingAgent,
        max_attempts: int = 3,
    ) -> AgentResult:
        """
        Supervise content and fix issues through regeneration.
        
        Args:
            content: The content to supervise
            formatting_agent: The agent to use for regeneration
            max_attempts: Maximum regeneration attempts
            
        Returns:
            AgentResult with final content
        """
        current_content = content
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            logger.debug(f"Supervision attempt {attempt}/{max_attempts}")
            
            # Validate current content
            rule_report = self.validate_content(current_content)
            
            if rule_report.status == ValidationStatus.PASSED:
                return AgentResult(
                    success=True,
                    content=current_content,
                    original_content=content,
                    agent_name=self.config.name,
                    metadata={
                        "attempts": attempt,
                        "final_score": rule_report.score,
                        "passed_rules": rule_report.passed_rules,
                    }
                )
            
            # If failed, try LLM validation for more details
            if self.llm_client and attempt < max_attempts:
                llm_report = await self.validate_with_llm(current_content)
                
                # Regenerate with error context
                errors = [r["error"] for r in rule_report.failed_rules]
                errors.extend(llm_report.warnings)
                
                result = await formatting_agent.regenerate_if_invalid(
                    current_content,
                    errors,
                )
                
                if result.success:
                    current_content = result.content
                else:
                    break
            else:
                break
        
        # Return with warnings about validation issues
        return AgentResult(
            success=False,
            content=current_content,
            original_content=content,
            agent_name=self.config.name,
            errors=[r["error"] for r in rule_report.failed_rules],
            metadata={
                "attempts": attempt,
                "final_score": rule_report.score,
                "failed_rules": rule_report.failed_rules,
            }
        )
    
    def add_custom_rule(
        self,
        content_type: str,
        rule: ValidationRule,
    ):
        """
        Add a custom validation rule.
        
        Args:
            content_type: The content type this rule applies to
            rule: The validation rule to add
        """
        if content_type not in self._validation_rules:
            self._validation_rules[content_type] = []
        
        self._validation_rules[content_type].append(rule)
        logger.debug(f"Added custom rule '{rule.name}' for {content_type}")
