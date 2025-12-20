"""
Mermaid State Diagram Agent - Specialized agent for state machine diagrams.

Supports:
- States and transitions
- Start/End states
- Composite states
- Forks/Joins
- Choice states
- Notes
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


class MermaidStateAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js state diagrams.
    
    Creates state machine diagrams showing:
    - States with descriptions
    - Transitions with events/conditions
    - Composite/nested states
    - Fork and join for parallel states
    """
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidStateAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js state diagram specialist. Your role is to:

1. CREATE valid Mermaid state diagrams from state machine descriptions
2. VALIDATE and FIX existing state diagram syntax
3. MODEL complex state behaviors with transitions
4. HANDLE composite states and parallel execution

MERMAID STATE DIAGRAM SYNTAX RULES:
===================================

1. DECLARATION:
   stateDiagram-v2
   (use v2 for better features)

2. STATES:
   s1 : Description
   state "Long State Name" as s1
   
3. SPECIAL STATES:
   [*] --> s1      # Start state
   s1 --> [*]      # End state
   
4. TRANSITIONS:
   s1 --> s2                    # Simple transition
   s1 --> s2 : event           # With event/trigger
   s1 --> s2 : event [guard]   # With condition
   s1 --> s2 : event / action  # With action
   
5. COMPOSITE STATES:
   state CompositeState {
       [*] --> inner1
       inner1 --> inner2
       inner2 --> [*]
   }
   
6. FORK AND JOIN (parallel):
   state fork_state <<fork>>
   state join_state <<join>>
   
   [*] --> fork_state
   fork_state --> State2
   fork_state --> State3
   State2 --> join_state
   State3 --> join_state
   join_state --> State4
   
7. CHOICE (conditional):
   state choice_state <<choice>>
   
   [*] --> choice_state
   choice_state --> State1 : if condition1
   choice_state --> State2 : if condition2
   choice_state --> State3 : else
   
8. NOTES:
   note right of State1
       Important information
       about this state
   end note
   
   note left of State2: Short note
   
9. DIRECTION:
   direction LR
   direction TB

10. CONCURRENCY:
    state Concurrent {
        [*] --> A1
        --
        [*] --> B1
    }

BEST PRACTICES:
===============
- Use stateDiagram-v2 for better syntax
- Define meaningful state names
- Add descriptions to complex states
- Use composite states for related states
- Include start/end states
- Add events to transitions
- Use choice for conditional branching

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        direction = kwargs.get("direction", "LR")
        
        return f"""Convert the following state machine description into a Mermaid state diagram.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Use stateDiagram-v2 syntax
- Direction: {direction}
- Include start and end states where appropriate
- Add event/trigger labels on transitions
- Use composite states for nested behaviors

EXPECTED OUTPUT FORMAT:
```mermaid
stateDiagram-v2
    direction {direction}
    
    [*] --> Idle
    Idle --> Processing : start
    Processing --> Completed : success
    Processing --> Failed : error
    Completed --> [*]
    Failed --> Idle : retry
    Failed --> [*] : abort
    
    state Processing {{
        [*] --> Validating
        Validating --> Executing
        Executing --> [*]
    }}
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "state",
    "state_count": number_of_states,
    "transition_count": number_of_transitions,
    "has_composite": true/false,
    "has_fork_join": true/false,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid state diagram syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if 'stateDiagram' not in content:
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any(re.search(r'stateDiagram(-v2)?', line) for line in lines[:3]):
            errors.append("Missing 'stateDiagram' or 'stateDiagram-v2' declaration")
        
        # Check for states or transitions
        has_states = re.search(r'\[?\*?\]?\s*-->', diagram)
        if not has_states:
            errors.append("No states or transitions found")
        
        # Check for balanced braces in composite states
        brace_count = diagram.count('{') - diagram.count('}')
        if brace_count != 0:
            errors.append("Unbalanced braces in composite states")
        
        # Check note syntax
        note_starts = len(re.findall(r'note\s+(left|right|over)\s+of', diagram, re.I))
        note_ends = diagram.lower().count('end note')
        
        # Multi-line notes should have matching end note
        multi_line_notes = len(re.findall(r'note\s+(left|right)\s+of\s+\w+\s*\n', diagram, re.I))
        if multi_line_notes > note_ends:
            errors.append(f"Unbalanced notes: {multi_line_notes} multi-line notes, {note_ends} 'end note'")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid state diagram."""
        if '```mermaid' not in content.lower() and 'stateDiagram' not in content:
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def create_state_diagram(
        self,
        states: List[Dict[str, Any]],
        transitions: List[Tuple[str, str, str]],
        direction: str = "LR",
    ) -> AgentResult:
        """
        Create a state diagram from states and transitions.
        
        Args:
            states: List of state dicts with keys:
                    - name: state name
                    - description: optional description
                    - type: normal, composite, fork, join, choice
                    - substates: for composite states
            transitions: List of (from_state, to_state, event)
            direction: LR or TB
            
        Returns:
            AgentResult with the generated diagram
        """
        diagram_lines = ["stateDiagram-v2", f"    direction {direction}", ""]
        
        # Define states
        for state in states:
            name = state.get("name")
            desc = state.get("description")
            state_type = state.get("type", "normal")
            substates = state.get("substates", [])
            
            if state_type == "fork":
                diagram_lines.append(f"    state {name} <<fork>>")
            elif state_type == "join":
                diagram_lines.append(f"    state {name} <<join>>")
            elif state_type == "choice":
                diagram_lines.append(f"    state {name} <<choice>>")
            elif state_type == "composite" and substates:
                diagram_lines.append(f"    state {name} {{")
                for sub in substates:
                    diagram_lines.append(f"        {sub}")
                diagram_lines.append("    }")
            elif desc:
                diagram_lines.append(f"    {name} : {desc}")
        
        diagram_lines.append("")
        
        # Add transitions
        for from_state, to_state, event in transitions:
            if event:
                diagram_lines.append(f"    {from_state} --> {to_state} : {event}")
            else:
                diagram_lines.append(f"    {from_state} --> {to_state}")
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(states),
            agent_name=self.config.name,
            metadata={
                "state_count": len(states),
                "transition_count": len(transitions),
            }
        )
