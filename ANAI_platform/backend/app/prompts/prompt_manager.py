"""
Prompt manager for constructing dynamic prompts.

This module handles the composition of prompts from various templates
and contextual information.
"""

from typing import Optional
from backend.app.prompts.base import (
    SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
)
from backend.app.prompts.base.base_prompts import (
    CHAIN_OF_THOUGHT_PROMPT,
    CODE_IMPLEMENTATION_PROMPT,
    ESSAY_PROMPT,
)
from backend.app.prompts.standard import QUESTION_TYPE_PROMPTS
from backend.app.utils.logger import get_logger


logger = get_logger(__name__)


class PromptBuilder:
    """
    Builds dynamic prompts for question generation.

    Combines system prompts, few-shot examples, and context-specific
    instructions to create optimized prompts for different question types.
    """

    def __init__(self):
        """Initialize the prompt builder."""
        self.system_prompt = SYSTEM_PROMPT
        self.few_shot_examples = FEW_SHOT_EXAMPLES
        self.chain_of_thought = CHAIN_OF_THOUGHT_PROMPT

    def build_question_generation_prompt(
        self,
        subject: str,
        question_type: str,
        difficulty_level: str,
        num_questions: int,
        additional_context: Optional[str] = None,
        use_cot: bool = True,
        use_few_shots: bool = True,
    ) -> str:
        """
        Build a comprehensive prompt for question generation.

        Args:
            subject: Subject area for questions
            question_type: Type of questions to generate
            difficulty_level: Difficulty level
            num_questions: Number of questions to generate
            additional_context: Optional additional context
            use_cot: Whether to include chain-of-thought guidance
            use_few_shots: Whether to include few-shot examples

        Returns:
            str: Fully constructed prompt
        """
        # Ensure types are correct
        if not isinstance(subject, str):
            subject = str(subject)
        if not isinstance(question_type, str):
            question_type = str(question_type)
        if not isinstance(difficulty_level, str):
            difficulty_level = str(difficulty_level)
        if not isinstance(num_questions, int):
            num_questions = int(num_questions)
        if additional_context and not isinstance(additional_context, str):
            additional_context = str(additional_context)
        
        logger.debug(
            f"Building prompt: subject={subject}, type={question_type}, "
            f"difficulty={difficulty_level}, count={num_questions}"
        )

        prompt_parts = []

        # Add system prompt
        prompt_parts.append(self.system_prompt)

        # Add question type specific guidance
        type_guidance = self._get_type_specific_guidance(question_type)
        if type_guidance:
            prompt_parts.append(f"\nQUESTION TYPE GUIDANCE:\n{type_guidance}")

        # Add few-shot examples if requested
        if use_few_shots:
            prompt_parts.append(f"\nLEARNING EXAMPLES:\n{self.few_shot_examples}")

        # Add chain-of-thought if requested
        if use_cot:
            prompt_parts.append(f"\nGENERATION APPROACH:\n{self.chain_of_thought}")

        # Add generation request
        generation_request = self._build_generation_request(
            subject=subject,
            question_type=question_type,
            difficulty_level=difficulty_level,
            num_questions=num_questions,
            additional_context=additional_context,
        )
        prompt_parts.append(f"\nTASK:\n{generation_request}")

        full_prompt = "\n".join(prompt_parts)

        logger.debug(f"Prompt built successfully. Length: {len(full_prompt)} chars")
        return full_prompt

    def _get_type_specific_guidance(self, question_type: str) -> Optional[str]:
        """
        Get guidance specific to question type.

        Args:
            question_type: Type of question

        Returns:
            str: Type-specific guidance or None
        """
        # First try extended prompts dictionary
        if question_type in QUESTION_TYPE_PROMPTS:
            return QUESTION_TYPE_PROMPTS[question_type]
        
        # Fallback for legacy types
        guidance_map = {
            "Code Implementation": CODE_IMPLEMENTATION_PROMPT,
            "Essay": ESSAY_PROMPT,
            "Multiple Choice": "Ensure options are plausible but distinct. "
                              "Include one clearly correct answer.",
            "Short Answer": "Expect concise but complete answers. "
                           "Clear expected answer criteria.",
            "Long Answer": "Allow for comprehensive responses. "
                          "Multiple valid approaches may be acceptable.",
        }

        return guidance_map.get(question_type)

    def _get_type_specific_formatting(self, question_type: str) -> str:
        """
        Get type-specific formatting instructions for question generation.
        
        CRITICAL: This ensures correct formatting based on question type.
        TEXT types must NOT get code/diagram formatting.
        
        Args:
            question_type: Type of question
            
        Returns:
            str: Formatting instructions for this question type
        """
        # TEXT TYPES - No special formatting (plain text only)
        text_types = ["Multiple Choice", "True/False", "Short Answer", "Long Answer", "Essay", "Fill in the Blank"]
        
        # CODE TYPES - Need code block formatting
        code_types = ["Code Implementation", "Code Output Prediction", "Coding", "Coding Problem"]
        
        # DIAGRAM TYPES - Need mermaid/ASCII formatting
        diagram_types = ["Diagram-Based", "Diagram", "Flowchart", "Data Flow", "UML Diagram", "Architecture Diagram"]
        
        # MATH TYPES - Need LaTeX formatting
        math_types = ["Numerical Problem", "Numerical", "Complexity Analysis", "Algorithm Complexity"]
        
        if question_type in text_types:
            return """

⚠️ CRITICAL FORMATTING RULES FOR TEXT-BASED QUESTIONS:
- Use PLAIN TEXT only - NO code blocks, NO diagrams, NO mermaid, NO ASCII art
- Questions must be written as simple, clear text sentences
- Options (for MCQ) must be plain text options like "A) Option text", "B) Option text"
- expected_answer must be plain text - just the answer letter for MCQ (e.g., "B") or short text
- explanation must be plain text paragraphs - NO special formatting
- DO NOT use: ```mermaid, ```python, flowchart, sequenceDiagram, or any diagram syntax
- DO NOT include ANY code blocks or technical formatting markers
- Focus on CONCEPTUAL content, not visual representations"""

        elif question_type in code_types:
            return """

⚠️ MANDATORY CODE FORMATTING RULES:
- ALL code snippets in question_text MUST be wrapped in markdown code blocks
- Use triple backticks with language: ```python, ```javascript, ```java, etc.
- NEVER include raw code without code block formatting
- Code in expected_answer MUST also use proper code blocks
- Example of CORRECT format: "What does this output?\\n\\n```python\\nprint('hello')\\n```"
- Example of WRONG format: "What does this output?\\nprint('hello')"
- Include text descriptions alongside code to explain what it does
- This ensures proper syntax highlighting and formatting in the UI"""

        elif question_type in diagram_types:
            return """

⚠️ MANDATORY DIAGRAM FORMATTING RULES:
- ALL diagrams MUST use Mermaid.js syntax wrapped in ```mermaid code blocks
- Use proper Mermaid syntax: flowchart TD, sequenceDiagram, classDiagram, etc.
- Include text descriptions explaining what the diagram shows
- Example format:
```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
```
- Ensure diagrams are valid Mermaid syntax that will render correctly"""

        elif question_type in math_types:
            return """

⚠️ MANDATORY MATH FORMATTING RULES:
- Use LaTeX notation for ALL mathematical expressions
- Inline math: wrap in single $ symbols like $x^2 + y^2$
- Block math: wrap in double $$ symbols for complex equations
- Use proper LaTeX commands: \\frac{}{}, \\sum, \\sqrt{}, \\times, etc.
- Example: "The time complexity is $O(n \\log n)$"
- Show step-by-step calculations with LaTeX for each step"""

        else:
            # SCENARIO-BASED or other types - conditional code formatting
            return """

⚠️ FORMATTING RULES:
- Use code blocks ONLY if the question requires actual code implementation
- If no code is needed, use plain text formatting
- For scenarios requiring code, wrap in ```python blocks
- Include clear text descriptions and explanations"""

    def _build_generation_request(
        self,
        subject: str,
        question_type: str,
        difficulty_level: str,
        num_questions: int,
        additional_context: Optional[str] = None,
    ) -> str:
        """
        Build the actual generation request text.

        Args:
            subject: Subject area
            question_type: Question type
            difficulty_level: Difficulty level
            num_questions: Number of questions
            additional_context: Additional context

        Returns:
            str: Generation request text
        """
        request = f"""Generate exactly {num_questions} HIGHLY DIVERSE AND INNOVATIVE {question_type} questions for {subject} at {difficulty_level} difficulty level.

Subject Context: {subject}
Question Type: {question_type}
Difficulty Level: {difficulty_level}
Number of Questions: {num_questions}"""

        if additional_context:
            request += f"\nAdditional Focus Areas: {additional_context}"

        # Add type-specific formatting instructions
        formatting_instructions = self._get_type_specific_formatting(question_type)
        request += formatting_instructions

        request += f"""

🎯 DIVERSITY & INNOVATION REQUIREMENTS:
1. EACH question MUST cover DIFFERENT concepts/subtopics within {subject}
2. NO repetition - vary the focus areas, scenarios, and applications
3. Mix theoretical, practical, analytical, and applied perspectives
4. Include edge cases, real-world scenarios, and cutting-edge concepts
5. Create NOVEL questions NOT commonly found in textbooks or online
6. Vary question complexity patterns - some direct, some analytical
7. Use different problem contexts - change domains, industries, situations
8. Make questions INTERESTING and thought-provoking for MTech students

CRITICAL REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions - NO MORE, NO LESS
2. Return ONLY valid JSON array format (no markdown, no extra text)
3. No text before or after the JSON array
4. Every question MUST have all fields populated (no null/empty fields)
5. question_text MUST be complete, clear, and engaging
6. expected_answer MUST be detailed, accurate, and comprehensive
7. explanation MUST provide deep educational value and reasoning
8. Options (for MCQ) MUST be plausible and distinct - no obvious wrong answers

FORMAT REQUIREMENTS:
- Return ONLY this JSON array format:
[{{"question_text": "...", "question_type": "{question_type}", "difficulty_level": "{difficulty_level}", "subject": "{subject}", "options": ["...", "...", "..."], "expected_answer": "...", "explanation": "...", "tags": ["..."], "content_flags": {{"has_code": false, "has_latex": false, "has_diagram": false, "code_language": null}}}}]

CONTENT_FLAGS FIELD (MANDATORY):
- has_code: true if question/answer contains programming code
- has_latex: true if question/answer contains mathematical formulas (LaTeX)
- has_diagram: true if question/answer contains mermaid/diagram syntax
- code_language: if has_code is true, specify the language (python, javascript, sql, etc.) otherwise null

Generate {num_questions} diverse, innovative, and unique questions as JSON array now:"""

        return request

    def build_batch_generation_prompt(
        self,
        subjects: list,
        question_types: list,
        difficulty_levels: list,
        questions_per_config: int = 2,
    ) -> str:
        """
        Build prompt for generating multiple question configurations at once.

        Args:
            subjects: List of subjects
            question_types: List of question types
            difficulty_levels: List of difficulty levels
            questions_per_config: Questions per configuration

        Returns:
            str: Batch generation prompt
        """
        configs = []
        for subject in subjects:
            for q_type in question_types:
                for difficulty in difficulty_levels:
                    configs.append(
                        f"{questions_per_config} {q_type} questions for {subject} "
                        f"at {difficulty} level"
                    )

        config_text = "\n".join([f"  - {config}" for config in configs])

        return f"""Generate questions for multiple configurations:

{config_text}

Return all questions as a single valid JSON array.
"""


def get_prompt_builder() -> PromptBuilder:
    """
    Get or create a prompt builder instance.

    Returns:
        PromptBuilder: Prompt builder instance
    """
    return PromptBuilder()
