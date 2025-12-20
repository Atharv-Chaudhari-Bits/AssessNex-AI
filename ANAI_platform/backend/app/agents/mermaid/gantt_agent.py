"""
Mermaid Gantt Chart Agent - Specialized agent for project timeline diagrams.

Supports:
- Tasks with start dates and durations
- Milestones
- Task dependencies
- Sections for grouping
- Date formats
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


class MermaidGanttAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js Gantt charts.
    
    Creates project timeline charts showing:
    - Tasks with durations
    - Task dependencies
    - Milestones
    - Project sections
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidGanttAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js Gantt chart specialist. Your role is to:

1. CREATE valid Mermaid Gantt charts from project plans
2. VALIDATE and FIX existing Gantt chart syntax
3. MODEL task dependencies and timelines
4. ORGANIZE tasks into logical sections

MERMAID GANTT CHART SYNTAX RULES:
=================================

1. DECLARATION:
   gantt

2. CHART SETTINGS:
   title Project Title
   dateFormat YYYY-MM-DD    # Date format for parsing
   axisFormat %Y-%m-%d      # Date format for display
   excludes weekends        # Exclude weekends
   excludes 2024-12-25      # Exclude specific dates
   todayMarker stroke:#f00,stroke-width:3px  # Today marker style

3. SECTIONS:
   section Section Name
       Task name : id, start_date, duration
   
4. TASK DEFINITIONS:
   Task name           : taskId, start_date, duration
   Task name           : taskId, after otherId, duration
   Task name           : done, taskId, 2024-01-01, 5d
   Task name           : active, taskId, 2024-01-01, 3d
   Task name           : crit, taskId, 2024-01-01, 2d
   Task name           : milestone, m1, 2024-01-15, 0d
   
5. TASK STATUS:
   done     - Completed task
   active   - Currently in progress
   crit     - Critical path task
   (none)   - Regular task

6. DURATION FORMATS:
   5d    - 5 days
   2w    - 2 weeks
   3h    - 3 hours (less common)
   
7. DEPENDENCIES:
   Task 2 : task2, after task1, 3d      # Starts after task1
   Task 3 : task3, after task1 task2, 2d # Starts after both

8. MILESTONES:
   Milestone : milestone, m1, 2024-01-15, 0d
   Release   : milestone, after task3, 0d

9. DATE FORMATS:
   dateFormat YYYY-MM-DD    # 2024-01-15
   dateFormat DD-MM-YYYY    # 15-01-2024
   dateFormat DD/MM/YYYY    # 15/01/2024
   
10. AXIS FORMAT:
    axisFormat %Y-%m-%d     # 2024-01-15
    axisFormat %d/%m        # 15/01
    axisFormat %b %d        # Jan 15

BEST PRACTICES:
===============
- Use meaningful task IDs
- Group related tasks in sections
- Define dependencies explicitly
- Mark critical path tasks
- Include milestones at key points
- Use consistent date format
- Keep task names concise

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        date_format = kwargs.get("date_format", "YYYY-MM-DD")
        include_excludes = kwargs.get("exclude_weekends", True)
        
        return f"""Convert the following project plan into a Mermaid Gantt chart.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Date format: {date_format}
- Exclude weekends: {include_excludes}
- Group tasks into logical sections
- Show task dependencies
- Include milestones for major deliverables

EXPECTED OUTPUT FORMAT:
```mermaid
gantt
    title Project Timeline
    dateFormat {date_format}
    {'excludes weekends' if include_excludes else ''}
    
    section Planning
    Requirements       : req, 2024-01-01, 5d
    Design            : design, after req, 3d
    Review            : milestone, after design, 0d
    
    section Development
    Backend           : backend, after design, 10d
    Frontend          : frontend, after design, 8d
    Integration       : active, integ, after backend frontend, 3d
    
    section Testing
    QA Testing        : qa, after integ, 5d
    Bug Fixes         : crit, bugs, after qa, 3d
    Release           : milestone, after bugs, 0d
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "gantt",
    "section_count": number_of_sections,
    "task_count": number_of_tasks,
    "milestone_count": number_of_milestones,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid Gantt chart syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if 'gantt' not in content.lower():
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any('gantt' in line.lower() for line in lines[:3]):
            errors.append("Missing 'gantt' declaration")
        
        # Check for tasks
        task_pattern = r'\w+.*:\s*\w+'
        has_tasks = any(re.search(task_pattern, line) for line in lines 
                       if not line.strip().startswith(('title', 'dateFormat', 'axisFormat', 'section', 'excludes')))
        
        if not has_tasks:
            errors.append("No tasks found in Gantt chart")
        
        # Check for dateFormat
        has_date_format = any('dateFormat' in line for line in lines)
        if not has_date_format:
            errors.append("Missing dateFormat declaration")
        
        # Validate task syntax
        for line in lines:
            stripped = line.strip()
            if ':' in stripped and not any(stripped.startswith(k) for k in 
                                           ['title', 'dateFormat', 'axisFormat', 'section', 'excludes', 'todayMarker']):
                # Should be a task line
                parts = stripped.split(':')
                if len(parts) < 2 or not parts[1].strip():
                    errors.append(f"Invalid task syntax: {stripped[:50]}")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid Gantt chart."""
        if '```mermaid' not in content.lower() and 'gantt' not in content.lower():
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def create_gantt(
        self,
        title: str,
        sections: Dict[str, List[Dict[str, Any]]],
        date_format: str = "YYYY-MM-DD",
        exclude_weekends: bool = True,
    ) -> AgentResult:
        """
        Create a Gantt chart from sections and tasks.
        
        Args:
            title: Chart title
            sections: Dict mapping section names to lists of task dicts:
                     - name: task name
                     - id: task id
                     - start: start date or "after taskId"
                     - duration: e.g., "5d", "2w"
                     - status: done, active, crit, milestone (optional)
            date_format: Date format string
            exclude_weekends: Whether to exclude weekends
            
        Returns:
            AgentResult with the generated chart
        """
        diagram_lines = [
            "gantt",
            f"    title {title}",
            f"    dateFormat {date_format}",
        ]
        
        if exclude_weekends:
            diagram_lines.append("    excludes weekends")
        
        diagram_lines.append("")
        
        task_count = 0
        milestone_count = 0
        
        for section_name, tasks in sections.items():
            diagram_lines.append(f"    section {section_name}")
            
            for task in tasks:
                name = task.get("name", "Task")
                task_id = task.get("id", f"task{task_count}")
                start = task.get("start", "")
                duration = task.get("duration", "1d")
                status = task.get("status", "")
                
                parts = [name, ":"]
                if status:
                    parts.append(status + ",")
                parts.append(task_id + ",")
                parts.append(start + ",")
                parts.append(duration)
                
                diagram_lines.append("    " + " ".join(parts))
                
                task_count += 1
                if status == "milestone":
                    milestone_count += 1
            
            diagram_lines.append("")
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=title,
            agent_name=self.config.name,
            metadata={
                "section_count": len(sections),
                "task_count": task_count,
                "milestone_count": milestone_count,
            }
        )
