"""
Mermaid Class Diagram Agent - Specialized agent for UML class diagrams.

Supports:
- Classes with attributes and methods
- Relationships (inheritance, composition, aggregation, association)
- Visibility modifiers
- Annotations
- Namespaces
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


class MermaidClassAgent(BaseFormattingAgent):
    """
    Specialized agent for Mermaid.js UML class diagrams.
    
    Creates class diagrams showing:
    - Classes with attributes and methods
    - Inheritance and interface implementation
    - Composition and aggregation
    - Associations with cardinality
    """
    
    # Relationship types
    RELATIONSHIPS = {
        "inheritance": "<|--",      # Class A inherits from Class B
        "composition": "*--",       # Class A is composed of Class B (strong)
        "aggregation": "o--",       # Class A contains Class B (weak)
        "association": "-->",       # Class A uses Class B
        "dependency": "..>",        # Class A depends on Class B
        "realization": "..|>",      # Class A implements Interface B
        "link_solid": "--",         # Simple solid link
        "link_dashed": "..",        # Simple dashed link
    }
    
    # Visibility modifiers
    VISIBILITY = {
        "public": "+",
        "private": "-",
        "protected": "#",
        "package": "~",
    }
    
    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="MermaidClassAgent",
            content_type=ContentType.MERMAID,
            max_retries=3,
            validation_level=ValidationLevel.STRICT,
            enable_llm_fallback=True,
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Mermaid.js UML class diagram specialist. Your role is to:

1. CREATE valid Mermaid class diagrams from OOP descriptions
2. VALIDATE and FIX existing class diagram syntax
3. MODEL proper relationships between classes
4. USE correct visibility modifiers and annotations

MERMAID CLASS DIAGRAM SYNTAX RULES:
===================================

1. DECLARATION:
   classDiagram

2. CLASS DEFINITION:
   class ClassName {
       +String publicAttribute
       -int privateAttribute
       #double protectedAttribute
       ~List~String~ packageAttribute
       +publicMethod() String
       -privateMethod(param: int) void
       #protectedMethod()* void
       +abstractMethod()* returnType
       +staticMethod()$ returnType
   }
   
   OR inline:
   class ClassName
   ClassName : +attribute
   ClassName : +method()

3. VISIBILITY MODIFIERS:
   + Public
   - Private
   # Protected
   ~ Package/Internal

4. METHOD MODIFIERS:
   methodName()* - Abstract method (asterisk)
   methodName()$ - Static method (dollar sign)

5. GENERIC TYPES:
   List~String~ for List<String>
   Map~String, int~ for Map<String, int>

6. RELATIONSHIPS:
   ClassA <|-- ClassB : Inheritance (B extends A)
   ClassA *-- ClassB : Composition (A owns B)
   ClassA o-- ClassB : Aggregation (A has B)
   ClassA --> ClassB : Association (A uses B)
   ClassA ..> ClassB : Dependency (A depends on B)
   ClassA ..|> InterfaceB : Realization (A implements B)
   
   With cardinality:
   ClassA "1" --> "*" ClassB : has many
   ClassA "1" --> "0..1" ClassB : has optional

7. ANNOTATIONS:
   class Shape {
       <<abstract>>
       +draw()*
   }
   
   class IDrawable {
       <<interface>>
       +draw()
   }
   
   class Color {
       <<enumeration>>
       RED
       GREEN
       BLUE
   }
   
   class Singleton {
       <<service>>
   }

8. NAMESPACES:
   namespace BaseShapes {
       class Triangle
       class Rectangle
   }

9. NOTES:
   note "This is a note"
   note for ClassName "Note for specific class"

10. DIRECTION:
    direction TB  # Top to bottom
    direction LR  # Left to right

BEST PRACTICES:
===============
- Define interfaces with <<interface>> annotation
- Use meaningful class names (PascalCase)
- Group related classes in namespaces
- Show only important attributes/methods
- Use proper relationship types
- Add cardinality for associations

Return ONLY valid JSON with the formatted diagram."""

    def _get_format_prompt(self, content: str, **kwargs) -> str:
        direction = kwargs.get("direction", "TB")
        show_methods = kwargs.get("show_methods", True)
        
        return f"""Convert the following OOP description into a Mermaid class diagram.

INPUT CONTENT:
{content}

REQUIREMENTS:
- Direction: {direction}
- Show methods: {show_methods}
- Use proper visibility modifiers (+, -, #, ~)
- Include relationship labels and cardinality
- Use appropriate annotations (<<interface>>, <<abstract>>, etc.)

EXPECTED OUTPUT FORMAT:
```mermaid
classDiagram
    direction {direction}
    
    class Animal {{
        <<abstract>>
        +String name
        +int age
        +makeSound()* void
        +move() void
    }}
    
    class Dog {{
        +String breed
        +makeSound() void
        +fetch() void
    }}
    
    class Cat {{
        +bool indoor
        +makeSound() void
        +climb() void
    }}
    
    Animal <|-- Dog : extends
    Animal <|-- Cat : extends
```

Return a JSON object with:
{{
    "formatted_content": "the complete mermaid diagram wrapped in ```mermaid code block",
    "diagram_type": "class",
    "class_count": number_of_classes,
    "relationship_count": number_of_relationships,
    "has_interfaces": true/false,
    "has_abstract": true/false,
    "validation_notes": ["any notes about the diagram"]
}}"""

    def _validate_output(self, content: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid class diagram syntax."""
        errors = []
        
        # Extract diagram content
        mermaid_match = re.search(r'```mermaid\s*([\s\S]*?)```', content)
        if not mermaid_match:
            if 'classDiagram' not in content:
                errors.append("Missing mermaid code block wrapper")
                return False, errors
            diagram = content
        else:
            diagram = mermaid_match.group(1).strip()
        
        lines = diagram.split('\n')
        
        # Check declaration
        if not any('classDiagram' in line for line in lines[:3]):
            errors.append("Missing 'classDiagram' declaration")
        
        # Check for class definitions
        class_pattern = r'class\s+\w+'
        has_classes = any(re.search(class_pattern, line) for line in lines)
        
        if not has_classes:
            errors.append("No class definitions found")
        
        # Check for balanced braces in class definitions
        brace_count = 0
        for line in lines:
            brace_count += line.count('{') - line.count('}')
        
        if brace_count != 0:
            errors.append(f"Unbalanced braces in class definitions")
        
        # Check relationship syntax
        relationship_pattern = r'\w+\s*(<\|--|[\*o]--|-->|\.\.>|\.\.\|>|--|\.\.).*\w+'
        for line in lines:
            if '<|' in line or '*-' in line or 'o-' in line or '->' in line or '..' in line:
                if not re.search(relationship_pattern, line):
                    if not line.strip().startswith('<<'):  # Not an annotation
                        errors.append(f"Invalid relationship syntax: {line[:50]}")
        
        return len(errors) == 0, errors
    
    def _is_already_formatted(self, content: str) -> bool:
        """Check if content is already a valid class diagram."""
        if '```mermaid' not in content.lower() and 'classDiagram' not in content:
            return False
        is_valid, _ = self._validate_output(content)
        return is_valid
    
    def create_class_diagram(
        self,
        classes: List[Dict[str, Any]],
        relationships: List[Tuple[str, str, str, str]],
        direction: str = "TB",
    ) -> AgentResult:
        """
        Create a class diagram from class definitions and relationships.
        
        Args:
            classes: List of class dicts with keys:
                     - name: class name
                     - attributes: list of (visibility, type, name)
                     - methods: list of (visibility, name, params, return_type)
                     - annotation: optional (interface, abstract, enum)
            relationships: List of (from_class, to_class, type, label)
            direction: TB or LR
            
        Returns:
            AgentResult with the generated diagram
        """
        diagram_lines = ["classDiagram", f"    direction {direction}", ""]
        
        # Add classes
        for cls in classes:
            name = cls.get("name", "UnnamedClass")
            annotation = cls.get("annotation")
            attributes = cls.get("attributes", [])
            methods = cls.get("methods", [])
            
            diagram_lines.append(f"    class {name} {{")
            
            if annotation:
                diagram_lines.append(f"        <<{annotation}>>")
            
            for vis, typ, attr_name in attributes:
                v = self.VISIBILITY.get(vis, "+")
                diagram_lines.append(f"        {v}{typ} {attr_name}")
            
            for vis, method_name, params, ret_type in methods:
                v = self.VISIBILITY.get(vis, "+")
                params_str = ", ".join(params) if params else ""
                diagram_lines.append(f"        {v}{method_name}({params_str}) {ret_type}")
            
            diagram_lines.append("    }")
            diagram_lines.append("")
        
        # Add relationships
        for from_cls, to_cls, rel_type, label in relationships:
            arrow = self.RELATIONSHIPS.get(rel_type, "-->")
            if label:
                diagram_lines.append(f"    {from_cls} {arrow} {to_cls} : {label}")
            else:
                diagram_lines.append(f"    {from_cls} {arrow} {to_cls}")
        
        content = "```mermaid\n" + "\n".join(diagram_lines) + "\n```"
        
        return AgentResult(
            success=True,
            content=content,
            original_content=str(classes),
            agent_name=self.config.name,
            metadata={
                "class_count": len(classes),
                "relationship_count": len(relationships),
            }
        )
