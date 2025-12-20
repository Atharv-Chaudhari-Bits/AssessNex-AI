"""
Quality Control Agent - Final quality assurance and refinement.

Features:
- Final output polishing
- Consistency checking
- Format standardization
- Quality scoring
- Output optimization
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
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


class QualityLevel(Enum):
    """Quality levels for output."""
    EXCELLENT = "excellent"      # 90-100%
    GOOD = "good"               # 75-89%
    ACCEPTABLE = "acceptable"   # 60-74%
    NEEDS_WORK = "needs_work"   # 40-59%
    POOR = "poor"               # 0-39%


@dataclass
class QualityMetrics:
    """Quality metrics for content."""
    overall_score: float = 0.0
    formatting_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    readability_score: float = 0.0
    level: QualityLevel = QualityLevel.ACCEPTABLE
    issues: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)


class QualityControlAgent(BaseFormattingAgent):
    """
    Final quality control for all formatted content.
    
    Responsibilities:
    1. Score content quality
    2. Check consistency across sections
    3. Polish final output
    4. Optimize formatting
    5. Generate quality reports
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="QualityControlAgent",
            content_type=ContentType.MIXED,
            max_retries=2,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a quality assurance expert for formatted content. Your role is to:

1. ASSESS overall content quality
2. CHECK consistency across sections
3. POLISH and refine output
4. OPTIMIZE formatting for readability
5. ENSURE professional standards

QUALITY CRITERIA:
=================

FORMATTING (25%):
- Proper Markdown syntax
- Correct code block usage
- Valid diagram syntax
- Balanced delimiters

COMPLETENESS (25%):
- All sections present
- No truncated content
- Proper endings
- Full explanations

CONSISTENCY (25%):
- Uniform styling
- Consistent terminology
- Matching patterns
- Coherent structure

READABILITY (25%):
- Clear organization
- Logical flow
- Appropriate spacing
- Good visual hierarchy

Return detailed quality assessment with actionable improvements."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        return f"""Assess the quality of this content and suggest improvements.

CONTENT:
{content}

Evaluate:
1. Formatting quality (0-100)
2. Completeness (0-100)
3. Consistency (0-100)
4. Readability (0-100)

Return JSON with:
{{
    "scores": {{
        "formatting": 85,
        "completeness": 90,
        "consistency": 80,
        "readability": 88
    }},
    "overall": 86,
    "issues": ["issue1", "issue2"],
    "improvements": ["suggestion1", "suggestion2"],
    "polished_content": "..." (optional)
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate QC output."""
        return True, []
    
    def _is_already_formatted(self, content: str) -> bool:
        """QC always processes."""
        return False
    
    def calculate_formatting_score(self, content: str) -> float:
        """
        Calculate formatting quality score.
        
        Args:
            content: The content to score
            
        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        penalties = []
        
        # Check code block balance
        if content.count('```') % 2 != 0:
            score -= 0.2
            penalties.append("Unbalanced code blocks")
        
        # Check LaTeX balance
        dollar_count = content.count('$') - content.count('$$') * 2
        if dollar_count % 2 != 0:
            score -= 0.15
            penalties.append("Unbalanced math delimiters")
        
        # Check for broken Mermaid
        mermaid_blocks = re.findall(r'```mermaid\n([\s\S]*?)```', content)
        for block in mermaid_blocks:
            if block.count('[') != block.count(']'):
                score -= 0.1
                penalties.append("Unbalanced brackets in Mermaid")
                break
        
        # Check for proper headings
        if '# ' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('#') and i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line and not prev_line.endswith('\n'):
                        score -= 0.05
                        penalties.append("Missing blank line before heading")
                        break
        
        logger.debug(f"Formatting score: {score}, penalties: {penalties}")
        return max(0.0, score)
    
    def calculate_completeness_score(self, content: str) -> float:
        """
        Calculate content completeness score.
        
        Args:
            content: The content to score
            
        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        
        # Check for truncation indicators
        truncation_patterns = [
            r'\.\.\.(?!\s*```)',  # ... not in code
            r'\[truncated\]',
            r'\[continued\]',
            r'etc\.\s*$',
        ]
        
        for pattern in truncation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 0.15
        
        # Check for incomplete code blocks
        code_blocks = re.findall(r'```\w*\n([\s\S]*?)```', content)
        for block in code_blocks:
            # Check for common incomplete patterns
            if block.strip().endswith('...'):
                score -= 0.1
            if 'TODO' in block or 'FIXME' in block:
                score -= 0.05
        
        # Check for empty sections
        empty_section = re.search(r'##\s+\w+\s*\n\s*\n\s*##', content)
        if empty_section:
            score -= 0.2
        
        return max(0.0, score)
    
    def calculate_consistency_score(self, content: str) -> float:
        """
        Calculate consistency score.
        
        Args:
            content: The content to score
            
        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        
        # Check heading consistency
        headings = re.findall(r'^(#+)\s+', content, re.MULTILINE)
        if headings:
            # Check for skipped heading levels
            levels = [len(h) for h in headings]
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    score -= 0.1
                    break
        
        # Check list consistency
        bullet_lists = re.findall(r'^[\*\-\+]\s', content, re.MULTILINE)
        if bullet_lists:
            bullet_chars = set(b[0] for b in bullet_lists)
            if len(bullet_chars) > 1:
                score -= 0.1  # Mixed bullet styles
        
        # Check code block language consistency
        code_langs = re.findall(r'```(\w+)', content)
        if code_langs:
            # Check if same language used different cases
            lower_langs = [l.lower() for l in code_langs]
            if len(set(code_langs)) != len(set(lower_langs)):
                score -= 0.1  # Inconsistent casing
        
        return max(0.0, score)
    
    def calculate_readability_score(self, content: str) -> float:
        """
        Calculate readability score.
        
        Args:
            content: The content to score
            
        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        
        lines = content.split('\n')
        
        # Check line lengths
        long_lines = sum(1 for line in lines if len(line) > 120)
        if long_lines > 5:
            score -= 0.1
        
        # Check for appropriate spacing
        consecutive_blank = 0
        max_consecutive = 0
        for line in lines:
            if line.strip() == '':
                consecutive_blank += 1
                max_consecutive = max(max_consecutive, consecutive_blank)
            else:
                consecutive_blank = 0
        
        if max_consecutive > 3:
            score -= 0.1
        
        # Check for dense content (no blank lines in long sections)
        non_blank_streak = 0
        for line in lines:
            if line.strip():
                non_blank_streak += 1
                if non_blank_streak > 20:
                    score -= 0.1
                    break
            else:
                non_blank_streak = 0
        
        # Check for proper code block spacing
        for i, line in enumerate(lines):
            if line.startswith('```') and i > 0:
                if lines[i-1].strip():
                    score -= 0.05  # No blank line before code block
                    break
        
        return max(0.0, score)
    
    def assess_quality(self, content: str) -> QualityMetrics:
        """
        Perform comprehensive quality assessment.
        
        Args:
            content: The content to assess
            
        Returns:
            QualityMetrics with detailed scores
        """
        formatting = self.calculate_formatting_score(content)
        completeness = self.calculate_completeness_score(content)
        consistency = self.calculate_consistency_score(content)
        readability = self.calculate_readability_score(content)
        
        overall = (formatting + completeness + consistency + readability) / 4
        
        # Determine level
        if overall >= 0.90:
            level = QualityLevel.EXCELLENT
        elif overall >= 0.75:
            level = QualityLevel.GOOD
        elif overall >= 0.60:
            level = QualityLevel.ACCEPTABLE
        elif overall >= 0.40:
            level = QualityLevel.NEEDS_WORK
        else:
            level = QualityLevel.POOR
        
        # Collect issues
        issues = []
        improvements = []
        
        if formatting < 0.8:
            issues.append("Formatting issues detected")
            improvements.append("Review and fix formatting syntax")
        
        if completeness < 0.8:
            issues.append("Content may be incomplete")
            improvements.append("Ensure all sections are complete")
        
        if consistency < 0.8:
            issues.append("Inconsistencies found")
            improvements.append("Standardize formatting patterns")
        
        if readability < 0.8:
            issues.append("Readability could be improved")
            improvements.append("Add spacing and organize content")
        
        return QualityMetrics(
            overall_score=overall,
            formatting_score=formatting,
            completeness_score=completeness,
            consistency_score=consistency,
            readability_score=readability,
            level=level,
            issues=issues,
            improvements=improvements,
        )
    
    async def assess_with_llm(self, content: str) -> QualityMetrics:
        """
        Use LLM for advanced quality assessment.
        
        Args:
            content: The content to assess
            
        Returns:
            QualityMetrics with LLM-based assessment
        """
        prompt = self._get_format_prompt(content)
        
        try:
            response = await self._call_llm(prompt)
            
            # Try to parse JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                
                scores = result.get("scores", {})
                overall = result.get("overall", 0) / 100
                
                # Determine level
                if overall >= 0.90:
                    level = QualityLevel.EXCELLENT
                elif overall >= 0.75:
                    level = QualityLevel.GOOD
                elif overall >= 0.60:
                    level = QualityLevel.ACCEPTABLE
                elif overall >= 0.40:
                    level = QualityLevel.NEEDS_WORK
                else:
                    level = QualityLevel.POOR
                
                return QualityMetrics(
                    overall_score=overall,
                    formatting_score=scores.get("formatting", 0) / 100,
                    completeness_score=scores.get("completeness", 0) / 100,
                    consistency_score=scores.get("consistency", 0) / 100,
                    readability_score=scores.get("readability", 0) / 100,
                    level=level,
                    issues=result.get("issues", []),
                    improvements=result.get("improvements", []),
                )
                
        except Exception as e:
            logger.error(f"LLM quality assessment failed: {e}")
        
        # Fallback to rule-based assessment
        return self.assess_quality(content)
    
    def polish_content(self, content: str) -> str:
        """
        Apply automatic polishing to content.
        
        Args:
            content: The content to polish
            
        Returns:
            Polished content
        """
        polished = content
        
        # Ensure proper spacing around headings
        polished = re.sub(r'(\S)\n(#{1,6}\s)', r'\1\n\n\2', polished)
        
        # Ensure proper spacing around code blocks
        polished = re.sub(r'(\S)\n(```)', r'\1\n\n\2', polished)
        polished = re.sub(r'(```)\n(\S)', r'\1\n\n\2', polished)
        
        # Normalize list markers (use - consistently)
        polished = re.sub(r'^[\*\+]\s', '- ', polished, flags=re.MULTILINE)
        
        # Remove excessive blank lines
        polished = re.sub(r'\n{4,}', '\n\n\n', polished)
        
        # Ensure file ends with newline
        if polished and not polished.endswith('\n'):
            polished += '\n'
        
        return polished
    
    async def quality_control(
        self,
        content: str,
        auto_polish: bool = True,
        use_llm: bool = False,
    ) -> AgentResult:
        """
        Perform full quality control.
        
        Args:
            content: The content to QC
            auto_polish: Whether to automatically polish
            use_llm: Whether to use LLM for assessment
            
        Returns:
            AgentResult with QC'd content
        """
        # Assess quality
        if use_llm and self.llm_client:
            metrics = await self.assess_with_llm(content)
        else:
            metrics = self.assess_quality(content)
        
        # Polish if needed and allowed
        final_content = content
        if auto_polish:
            final_content = self.polish_content(content)
            
            # Re-assess after polishing
            post_metrics = self.assess_quality(final_content)
            if post_metrics.overall_score > metrics.overall_score:
                metrics = post_metrics
        
        return AgentResult(
            success=metrics.level in [QualityLevel.EXCELLENT, QualityLevel.GOOD, QualityLevel.ACCEPTABLE],
            content=final_content,
            original_content=content,
            agent_name=self.config.name,
            metadata={
                "quality_level": metrics.level.value,
                "overall_score": metrics.overall_score,
                "formatting_score": metrics.formatting_score,
                "completeness_score": metrics.completeness_score,
                "consistency_score": metrics.consistency_score,
                "readability_score": metrics.readability_score,
                "issues": metrics.issues,
                "improvements": metrics.improvements,
                "was_polished": auto_polish,
            }
        )
    
    def generate_quality_report(self, metrics: QualityMetrics) -> str:
        """
        Generate a human-readable quality report.
        
        Args:
            metrics: The quality metrics
            
        Returns:
            Formatted quality report
        """
        report_lines = [
            "# Quality Report",
            "",
            f"**Overall Quality:** {metrics.level.value.replace('_', ' ').title()}",
            f"**Overall Score:** {metrics.overall_score:.1%}",
            "",
            "## Detailed Scores",
            "",
            f"| Category | Score |",
            f"|----------|-------|",
            f"| Formatting | {metrics.formatting_score:.1%} |",
            f"| Completeness | {metrics.completeness_score:.1%} |",
            f"| Consistency | {metrics.consistency_score:.1%} |",
            f"| Readability | {metrics.readability_score:.1%} |",
            "",
        ]
        
        if metrics.issues:
            report_lines.append("## Issues Found")
            report_lines.append("")
            for issue in metrics.issues:
                report_lines.append(f"- {issue}")
            report_lines.append("")
        
        if metrics.improvements:
            report_lines.append("## Suggested Improvements")
            report_lines.append("")
            for improvement in metrics.improvements:
                report_lines.append(f"- {improvement}")
            report_lines.append("")
        
        return "\n".join(report_lines)
