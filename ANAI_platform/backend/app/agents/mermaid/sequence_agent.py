"""
Mermaid Sequence Diagram Agent - Specialized agent for sequence diagrams.

Supports:
- Participants and Actors
- Messages (sync, async, returns)
- Activations/Deactivations
- Notes (left, right, over)
- Loops, Alt, Opt, Par blocks
- Breaks
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


class MermaidSequenceAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js sequence diagrams.
    
    Creates sequence diagrams showing:
    - Actor/participant interactions
    - Message flows (synchronous, asynchronous)
    - Activation bars
    - Conditional logic (alt/opt)
    - Loops and parallel processing
    """
    
    # Message types
    MESSAGE_TYPES = {
        "solid_arrow": "->>",           # Synchronous message
        "solid_arrow_open": "->",       # Async without arrowhead
        "dotted_arrow": "-->>",         # Response/return
        "dotted_arrow_open": "-->",     # Async response
        "solid_cross": "-x",            # Lost message
        "dotted_cross": "--x",          # Lost response
        "solid_async": "-)",            # Async message
        "dotted_async": "--)",          # Async response
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidSequenceAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js sequence diagram specialist. Your role is to:

1. CREATE valid Mermaid sequence diagrams from interaction descriptions
2. VALIDATE and FIX existing sequence diagram syntax
3. ENSURE proper participant/actor definitions
4. MODEL complex interactions with loops, alternatives, and notes

MERMAID SEQUENCE DIAGRAM SYNTAX RULES:
======================================

1. DECLARATION:
   sequenceDiagram

2. PARTICIPANTS (define at the top):
   participant A as Alice
   participant B as Bob
   actor U as User         # Stick figure icon
   
3. MESSAGE TYPES:
   A->>B: Synchronous call           # Solid line, filled arrow
   A-->>B: Response/Return           # Dotted line, filled arrow  
   A-)B: Async message               # Solid line, open arrow
   A--)B: Async response             # Dotted line, open arrow
   A-xB: Lost message (to nowhere)   # Cross at end
   
4. ACTIVATIONS (show processing):
   activate A       # Start activation bar
   deactivate A     # End activation bar
   A->>+B: Message  # Activate B on message
   B-->>-A: Response # Deactivate B on response

5. NOTES:
   Note left of A: Text
   Note right of B: Text
   Note over A: Text
   Note over A,B: Text spanning participants

6. CONTROL STRUCTURES:
   
   loop Every minute
       A->>B: Heartbeat
   end
   
   alt Condition met
       A->>B: Do this
   else Not met
       A->>B: Do that
   end
   
   opt Optional action
       A->>B: Maybe do this
   end
   
   par Parallel 1
       A->>B: Message 1
   and Parallel 2
       A->>C: Message 2
   end
   
   critical Critical section
       A->>B: Important
   option On failure
       A->>C: Fallback
   end
   
   break When error
       A->>B: Error handling
   end

7. AUTONUMBER:
   autonumber  # Adds sequence numbers to messages

8. STYLING:
   %%{init: {'theme': 'base'}}%%

BEST PRACTICES:
===============
- Define all participants at the top
- Use meaningful participant aliases
- Group related interactions in blocks
- Add notes for clarification
- Use activations to show processing time
- Keep messages concise

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        include_autonumber = kwargs.get("autonumber", False)
        include_activations = kwargs.get("activations", True)
        
        return f"""Convert the following interaction description into a Mermaid sequence diagram.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Include auto-numbering: {include_autonumber}
- Show activations: {include_activations}
- Define all participants at the top
- Use appropriate message types (sync/async/response)
- Add notes where helpful for clarity

EXPECTED OUTPUT FORMAT:
```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant D as Database
    
    C->>+S: HTTP Request
    S->>+D: Query
    D-->>-S: Results
    S-->>-C: HTTP Response
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "sequence",
    "participant_count": number_of_participants,
    "message_count": number_of_messages,
    "has_loops": true/false,
    "has_alternatives": true/false,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid sequence diagram syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if 'sequenceDiagram' not in content:
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any('sequenceDiagram' in line for line in lines[:3]):
            errors.append("Missing 'sequenceDiagram' declaration")
        
        # Check for participants or actors
        has_participants = any(
            re.match(r'\s*(participant|actor)\s+\w+', line) 
            for line in lines
        )
        
        # Check for messages
        message_pattern = r'\w+\s*(->>|-->>|-\)|--\)|-x|--x|->|-->)\s*\w+'
        has_messages = any(re.search(message_pattern, line) for line in lines)
        
        if not has_messages:
            errors.append("No messages found between participants")
        
        # Check for balanced blocks
        block_starts = ['loop', 'alt', 'opt', 'par', 'critical', 'break', 'rect']
        block_count = 0
        end_count = 0
        
        for line in lines:
            stripped = line.strip().lower()
            if any(stripped.startswith(b) for b in block_starts):
                block_count += 1
            if stripped == 'end':
                end_count += 1
        
        if block_count != end_count:
            errors.append(f"Unbalanced blocks: {block_count} starts, {end_count} ends")
        
        # Check activation balance
        activate_count = sum(1 for line in lines if 'activate' in line.lower() and 'deactivate' not in line.lower())
        deactivate_count = sum(1 for line in lines if 'deactivate' in line.lower())
        plus_activations = sum(1 for line in lines if '->>+' in line or '-)+' in line)
        minus_deactivations = sum(1 for line in lines if '>>-' in line or ')-' in line)
        
        total_activate = activate_count + plus_activations
        total_deactivate = deactivate_count + minus_deactivations
        
        if total_activate != total_deactivate:
            errors.append(f"Unbalanced activations: {total_activate} activate, {total_deactivate} deactivate")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid sequence diagram."""
        if '```mermaid' not in content.lower() and 'sequenceDiagram' not in content:
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def _get_best_effort(self, content: str, **kwargs) -> str:
        """Create a basic sequence diagram from text."""
        lines = content.strip().split('\n')
        participants = set()
        messages = []
        
        # Try to extract interactions
        for line in lines:
            # Look for patterns like "A sends message to B"
            match = re.search(r'(\w+)\s+(?:sends?|calls?|requests?)\s+(.+?)\s+(?:to|from)\s+(\w+)', line, re.I)
            if match:
                participants.add(match.group(1))
                participants.add(match.group(3))
                messages.append((match.group(1), match.group(3), match.group(2)))
        
        if not messages:
            return content
        
        # Build diagram
        diagram_lines = ["sequenceDiagram"]
        for p in sorted(participants):
            diagram_lines.append(f"    participant {p}")
        diagram_lines.append("")
        for sender, receiver, msg in messages:
            diagram_lines.append(f"    {sender}->>>{receiver}: {msg[:40]}")
        
        return "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
    
    def create_sequence(
        self,
        participants: List[str],
        interactions: List[Tuple[str, str, str, str]],
        title: Optional[str] = None,
        autonumber: bool = False,
    ) -> AgentResult:
        """
        Create a sequence diagram from participants and interactions.
        
        Args:
            participants: List of (id, alias) tuples or just names
            interactions: List of (from, to, message, type) tuples
                         type can be: sync, async, response, lost
            title: Optional title
            autonumber: Whether to add auto-numbering
            
        Returns:
            AgentResult with the generated diagram
        """
        diagram_lines = ["sequenceDiagram"]
        
        if autonumber:
            diagram_lines.append("    autonumber")
        
        # Add participants
        for p in participants:
            if isinstance(p, tuple):
                diagram_lines.append(f"    participant {p[0]} as {p[1]}")
            else:
                diagram_lines.append(f"    participant {p}")
        
        diagram_lines.append("")
        
        # Add interactions
        type_map = {
            "sync": "->>",
            "async": "-)",
            "response": "-->>",
            "async_response": "--)",
            "lost": "-x",
        }
        
        for sender, receiver, message, msg_type in interactions:
            arrow = type_map.get(msg_type, "->>")
            diagram_lines.append(f"    {sender}{arrow}{receiver}: {message}")
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(interactions),
            agent_name=self.config.name,
            metadata={
                "participant_count": len(participants),
                "message_count": len(interactions),
            }
        )
