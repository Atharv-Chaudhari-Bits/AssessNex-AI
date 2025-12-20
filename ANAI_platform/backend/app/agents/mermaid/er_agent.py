"""
Mermaid ER Diagram Agent - Specialized agent for Entity-Relationship diagrams.

Supports:
- Entities with attributes
- Relationships with cardinality
- Primary keys and foreign keys
- Relationship labels
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


class MermaidERDAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js Entity-Relationship diagrams.
    
    Creates ER diagrams showing:
    - Entities with attributes
    - Primary keys and foreign keys
    - Relationships with cardinality
    - Identifying vs non-identifying relationships
    """
    
    # Cardinality notation
    CARDINALITY = {
        "zero_or_one": "|o",
        "exactly_one": "||",
        "zero_or_more": "}o",
        "one_or_more": "}|",
    }
    
    # Relationship types
    RELATIONSHIPS = {
        "identifying": "--",      # Solid line - identifying relationship
        "non_identifying": "..",  # Dashed line - non-identifying relationship
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidERDAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js ER diagram specialist. Your role is to:

1. CREATE valid Mermaid ER diagrams from database schemas
2. VALIDATE and FIX existing ER diagram syntax
3. MODEL proper relationships with cardinality
4. SHOW primary/foreign keys appropriately

MERMAID ER DIAGRAM SYNTAX RULES:
================================

1. DECLARATION:
   erDiagram

2. ENTITIES:
   ENTITY_NAME {
       type attribute_name PK "comment"
       type attribute_name FK "comment"
       type attribute_name UK "unique"
       type attribute_name "just a comment"
   }
   
   Example:
   CUSTOMER {
       int id PK "Primary Key"
       string name
       string email UK "Unique email"
       int address_id FK "Foreign Key"
   }

3. ATTRIBUTE TYPES:
   - string
   - int
   - float
   - boolean
   - date
   - datetime
   - text
   - blob
   - enum

4. ATTRIBUTE KEYS:
   PK - Primary Key
   FK - Foreign Key  
   UK - Unique Key

5. RELATIONSHIPS:
   ENTITY1 ||--|| ENTITY2 : "label"    # One to one
   ENTITY1 ||--o{ ENTITY2 : "label"    # One to many
   ENTITY1 }o--o{ ENTITY2 : "label"    # Many to many
   ENTITY1 ||..o{ ENTITY2 : "label"    # Non-identifying

6. CARDINALITY NOTATION:
   || - Exactly one
   |o - Zero or one
   }| - One or more
   }o - Zero or more

7. RELATIONSHIP LINE:
   -- - Identifying relationship (solid line)
   .. - Non-identifying relationship (dashed line)

8. READING RELATIONSHIPS:
   CUSTOMER ||--o{ ORDER : "places"
   Reads as: One CUSTOMER places zero or more ORDERs
   
   ORDER ||--|{ LINE_ITEM : "contains"
   Reads as: One ORDER contains one or more LINE_ITEMs

BEST PRACTICES:
===============
- Use UPPERCASE for entity names
- Use lowercase for attribute names
- Mark all primary keys with PK
- Mark foreign keys with FK
- Add meaningful relationship labels
- Use identifying vs non-identifying correctly
- Group related entities visually

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        show_attributes = kwargs.get("show_attributes", True)
        
        return f"""Convert the following database schema description into a Mermaid ER diagram.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Show attributes: {show_attributes}
- Mark primary keys with PK
- Mark foreign keys with FK
- Include relationship labels
- Use proper cardinality notation

EXPECTED OUTPUT FORMAT:
```mermaid
erDiagram
    CUSTOMER {{
        int id PK
        string name
        string email UK
        datetime created_at
    }}
    
    ORDER {{
        int id PK
        int customer_id FK
        datetime order_date
        float total
    }}
    
    ORDER_ITEM {{
        int id PK
        int order_id FK
        int product_id FK
        int quantity
    }}
    
    PRODUCT {{
        int id PK
        string name
        float price
        int stock
    }}
    
    CUSTOMER ||--o{{ ORDER : "places"
    ORDER ||--|{{ ORDER_ITEM : "contains"
    PRODUCT ||--o{{ ORDER_ITEM : "included in"
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "er",
    "entity_count": number_of_entities,
    "relationship_count": number_of_relationships,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid ER diagram syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if 'erDiagram' not in content:
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any('erDiagram' in line for line in lines[:3]):
            errors.append("Missing 'erDiagram' declaration")
        
        # Check for entities
        entity_pattern = r'\w+\s*\{'
        has_entities = re.search(entity_pattern, diagram)
        
        # Check for relationships
        relationship_pattern = r'\w+\s*(\|\||\|o|\}o|\}\|)\s*--\s*(\|\||\|o|\}o|\}\|)\s*\w+'
        has_relationships = re.search(relationship_pattern, diagram)
        
        if not has_entities and not has_relationships:
            errors.append("No entities or relationships found")
        
        # Check for balanced braces
        brace_count = diagram.count('{') - diagram.count('}')
        if brace_count != 0:
            errors.append("Unbalanced braces in entity definitions")
        
        # Validate relationship syntax
        for line in lines:
            if '--' in line and ':' in line:
                # Should have cardinality on both sides
                if not re.search(r'(\|\||\|o|\}o|\}\|)\s*--\s*(\|\||\|o|\}o|\}\|)', line):
                    # Check for dashed relationships too
                    if not re.search(r'(\|\||\|o|\}o|\}\|)\s*\.\.\s*(\|\||\|o|\}o|\}\|)', line):
                        errors.append(f"Invalid relationship syntax: {line[:60]}")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid ER diagram."""
        if '```mermaid' not in content.lower() and 'erDiagram' not in content:
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def create_er_diagram(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Tuple[str, str, str, str, str]],
    ) -> AgentResult:
        """
        Create an ER diagram from entities and relationships.
        
        Args:
            entities: List of entity dicts with keys:
                     - name: entity name
                     - attributes: list of (type, name, key, comment) tuples
            relationships: List of (entity1, cardinality1, entity2, cardinality2, label)
            
        Returns:
            AgentResult with the generated diagram
        """
        diagram_lines = ["erDiagram"]
        
        # Add entities
        for entity in entities:
            name = entity.get("name", "ENTITY")
            attributes = entity.get("attributes", [])
            
            diagram_lines.append(f"    {name} {{")
            for attr_type, attr_name, key, comment in attributes:
                line = f"        {attr_type} {attr_name}"
                if key:
                    line += f" {key}"
                if comment:
                    line += f' "{comment}"'
                diagram_lines.append(line)
            diagram_lines.append("    }")
            diagram_lines.append("")
        
        # Add relationships
        for e1, c1, e2, c2, label in relationships:
            card1 = self.CARDINALITY.get(c1, "||")
            card2 = self.CARDINALITY.get(c2, "||")
            diagram_lines.append(f'    {e1} {card1}--{card2} {e2} : "{label}"')
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(entities),
            agent_name=self.config.name,
            metadata={
                "entity_count": len(entities),
                "relationship_count": len(relationships),
            }
        )
