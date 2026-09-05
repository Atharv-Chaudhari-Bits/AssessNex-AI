"""
Prompt manager for constructing dynamic prompts.

This module handles the composition of prompts from various templates
and contextual information, now with Bloom's taxonomy support.
"""

from typing import Optional, List, Dict, Any
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
    Now supports Bloom's taxonomy calibration.
    """

    # Bloom's taxonomy level definitions
    BLOOM_LEVELS = {
        "Remember": {
            "description": "Recall facts, terms, basic concepts",
            "keywords": ["define", "list", "recall", "name", "identify", "state"],
            "cognitive_demand": "Lowest - simple recall",
            "question_style": "Direct recall of facts, definitions, or basic properties"
        },
        "Understand": {
            "description": "Explain ideas or concepts",
            "keywords": ["explain", "describe", "summarize", "interpret", "paraphrase", "classify"],
            "cognitive_demand": "Low - demonstrate comprehension",
            "question_style": "Describe concepts in own words, summarize, give examples"
        },
        "Apply": {
            "description": "Use information in new situations",
            "keywords": ["apply", "demonstrate", "implement", "solve", "use", "compute"],
            "cognitive_demand": "Medium - execute or implement",
            "question_style": "Solve problems, apply formulas, use methods in new contexts"
        },
        "Analyze": {
            "description": "Draw connections among ideas",
            "keywords": ["analyze", "compare", "contrast", "differentiate", "examine", "investigate"],
            "cognitive_demand": "Medium-High - distinguish, organize, attribute",
            "question_style": "Break down concepts, find patterns, analyze relationships"
        },
        "Evaluate": {
            "description": "Justify a stand or decision",
            "keywords": ["evaluate", "critique", "assess", "justify", "debate", "recommend"],
            "cognitive_demand": "High - check, critique, judge",
            "question_style": "Make judgments, defend positions, critique methodologies"
        },
        "Create": {
            "description": "Produce new or original work",
            "keywords": ["design", "develop", "formulate", "propose", "construct", "synthesize"],
            "cognitive_demand": "Highest - generate, plan, produce",
            "question_style": "Design solutions, create models, develop novel approaches"
        }
    }

    def __init__(self):
        """Initialize the prompt builder."""
        self.system_prompt = SYSTEM_PROMPT
        self.few_shot_examples = FEW_SHOT_EXAMPLES
        self.chain_of_thought = CHAIN_OF_THOUGHT_PROMPT
        logger.info("PromptBuilder initialized with Bloom's taxonomy support")

    def validate_bloom_level(self, bloom_level: str) -> bool:
        """
        Validate if a Bloom's level is supported.
        
        Args:
            bloom_level: Bloom's level to validate
            
        Returns:
            bool: True if valid
        """
        return bloom_level in self.BLOOM_LEVELS


    def validate_bloom_distribution(self, distribution: Dict[str, int]) -> bool:
        """
        Validate Bloom's taxonomy distribution.
        
        Args:
            distribution: Dictionary mapping levels to percentages
            
        Returns:
            bool: True if valid
        """
        # Check if all levels are valid
        for level in distribution.keys():
            if level not in self.BLOOM_LEVELS:
                logger.warning(f"Invalid Bloom level in distribution: {level}")
                return False
        
        # Check if percentages sum to 100
        total = sum(distribution.values())
        if total != 100:
            logger.warning(f"Bloom distribution sums to {total}, expected 100")
            return False
        
        return True

    def build_question_generation_prompt(
        self,
        subject: str,
        question_type: str,
        num_questions: int,
        difficulty_level: str = "Medium",
        bloom_level: Optional[str] = None,
        additional_context: str = "",
        use_cot: bool = True,
        use_few_shots: bool = True,
    ) -> str:
        """
        Build a comprehensive prompt for question generation.

        Args:
            subject: Subject area for questions
            question_type: Type of questions to generate
            num_questions: Number of questions to generate
            difficulty_level: Difficulty level (legacy)
            bloom_level: Bloom's taxonomy level (new)
            additional_context: Optional additional context
            use_cot: Whether to include chain-of-thought guidance
            use_few_shots: Whether to include few-shot examples

        Returns:
            str: Fully constructed prompt
        """
        try:
            # Validate bloom level if provided
            if bloom_level and not self.validate_bloom_level(bloom_level):
                logger.warning(f"Invalid bloom level: {bloom_level}, defaulting to Understand")
                bloom_level = "Understand"
            
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
                f"difficulty={difficulty_level}, bloom={bloom_level}, count={num_questions}"
            )

            prompt_parts = []

            # Determine which system prompt to use
            if bloom_level:
                system_prompt = self._get_bloom_system_prompt(bloom_level)
            else:
                system_prompt = self.system_prompt
            
            prompt_parts.append(system_prompt)

            # Add question type specific guidance
            type_guidance = self._get_type_specific_guidance(question_type)
            if type_guidance:
                prompt_parts.append(f"\n📋 QUESTION TYPE GUIDANCE:\n{type_guidance}")

            # Add Bloom's taxonomy guidance if specified
            if bloom_level:
                bloom_guidance = self._get_bloom_guidance(bloom_level)
                prompt_parts.append(f"\n🎯 BLOOM'S TAXONOMY CALIBRATION:\n{bloom_guidance}")

            # Add few-shot examples if requested
            if use_few_shots:
                examples = self._get_filtered_examples(question_type, bloom_level)
                if examples:
                    prompt_parts.append(f"\n📚 REFERENCE EXAMPLES:\n{examples}")

            # Add chain-of-thought if requested
            if use_cot:
                cot_instructions = self._get_cot_instructions(question_type, bloom_level)
                prompt_parts.append(f"\n🧠 GENERATION APPROACH:\n{cot_instructions}")

            # Add generation request
            generation_request = self._build_generation_request(
                subject=subject,
                question_type=question_type,
                num_questions=num_questions,
                difficulty_level=difficulty_level,
                bloom_level=bloom_level,
                additional_context=additional_context,
            )
            prompt_parts.append(f"\n📝 TASK:\n{generation_request}")

            full_prompt = "\n".join(prompt_parts)

            logger.debug(f"Prompt built successfully. Length: {len(full_prompt)} chars")
            return full_prompt

        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}", exc_info=True)
            # Return a fallback prompt
            return f"Generate {num_questions} {question_type} questions about {subject}."

    def _get_bloom_system_prompt(self, bloom_level: str) -> str:
        """
        Get system prompt with Bloom's taxonomy focus.

        Args:
            bloom_level: Bloom's taxonomy level

        Returns:
            str: Enhanced system prompt
        """
        return f"""You are an expert MTech level question generator for AI/ML subjects.
Your task is to generate high-quality, academic-level questions that target specific Bloom's taxonomy levels.
Always respond with valid JSON format containing question details.

CRITICAL CALIBRATION REQUIREMENTS FOR {bloom_level} LEVEL:
1. Questions MUST be calibrated EXACTLY to the {bloom_level} level - no higher, no lower
2. Each question must use action verbs appropriate for {bloom_level}
3. The cognitive demand must match: {self.BLOOM_LEVELS[bloom_level]['cognitive_demand']}
4. Question style: {self.BLOOM_LEVELS[bloom_level]['question_style']}
5. In the explanation, explicitly justify why this question targets {bloom_level} level
6. DO NOT create questions at lower levels (Remember/Understand) or higher levels (Evaluate/Create)
7. Ensure questions are technically accurate and well-structured
8. Provide clear, concise questions without ambiguity
9. Include detailed explanations for answers
10. For multiple choice questions, ensure options are plausible but clearly different"""

    def _get_bloom_guidance(self, bloom_level: str) -> str:
        """
        Get detailed guidance for a specific Bloom's taxonomy level.

        Args:
            bloom_level: The Bloom's taxonomy level

        Returns:
            str: Detailed guidance for question generation at this level
        """
        level_info = self.BLOOM_LEVELS.get(bloom_level, self.BLOOM_LEVELS["Understand"])
        
        guidance = f"""
╔════════════════════════════════════════════════════════════════╗
║           BLOOM'S TAXONOMY CALIBRATION: {bloom_level} LEVEL          ║
╚════════════════════════════════════════════════════════════════╝

📋 Level Description: {level_info['description']}
🧠 Cognitive Demand: {level_info['cognitive_demand']}
✏️ Question Style: {level_info['question_style']}

🔑 REQUIRED ACTION VERBS (use these in questions):
   Primary verbs: {', '.join(level_info['keywords'][:3])}
   Secondary verbs: {', '.join(level_info['keywords'][3:6])}

⚠️ STRICT CALIBRATION RULES:
1. DO NOT create questions at lower levels (Remember/Understand)
2. DO NOT create questions at higher levels (Evaluate/Create)
3. Each question MUST clearly demonstrate {bloom_level} level cognitive skills
4. The complexity and depth MUST match {bloom_level} expectations
5. Students should need to {level_info['keywords'][0]} to answer correctly

✅ VERIFICATION CHECKLIST:
   ☐ Question uses appropriate action verbs for {bloom_level}
   ☐ Question matches {bloom_level} cognitive demand
   ☐ Question style aligns with {level_info['question_style']}
   ☐ Explanation justifies why this is a {bloom_level} level question
"""
        return guidance

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
        
        # Enhanced guidance map
        guidance_map = {
            "Code Implementation": CODE_IMPLEMENTATION_PROMPT + """

ADDITIONAL CODE REQUIREMENTS:
- Use proper code blocks with language specification
- Include comments in code for clarity
- Test cases should cover edge cases
- Provide expected input/output examples""",
            
            "Essay": ESSAY_PROMPT + """

ESSAY REQUIREMENTS:
- Specify expected word count range (e.g., 500-800 words)
- Include evaluation criteria in explanation
- Suggest key points to cover
- Reference relevant theories or frameworks""",
            
            "Multiple Choice": """Multiple Choice Question Guidelines:
- Options should be plausible but clearly distinct
- One clearly correct answer (no "all of the above" trick options)
- Distractors should test common misconceptions
- Avoid obvious wrong answers
- Include 4 options (A, B, C, D) for consistency""",
            
            "Short Answer": """Short Answer Guidelines:
- Expect concise but complete answers (2-5 sentences)
- Define expected key terms or concepts
- Accept multiple valid formulations
- Provide scoring criteria in explanation""",
            
            "Long Answer": """Long Answer Guidelines:
- Allow for comprehensive responses (paragraphs)
- Multiple valid approaches may be acceptable
- Specify expected coverage areas
- Include evaluation rubric in explanation""",
            
            "Diagram-Based": """Diagram-Based Question Guidelines:
- Use Mermaid.js syntax for ALL diagrams
- Wrap diagrams in ```mermaid code blocks
- Include text description alongside diagram
- Explain what the diagram should illustrate
- Provide expected diagram elements""",
            
            "Numerical Problem": """Numerical Problem Guidelines:
- Show step-by-step solution in answer
- Use LaTeX for all mathematical expressions
- Include unit conversions if applicable
- Provide intermediate calculation steps
- Specify precision requirements""",
            
            "True/False": """True/False Question Guidelines:
- Statements should be unequivocally true or false
- Avoid double negatives
- Include brief justification in explanation
- Test understanding, not trickery"""
        }

        return guidance_map.get(question_type)

    def _get_type_specific_formatting(self, question_type: str, bloom_level: Optional[str] = None) -> str:
        """
        Get type-specific formatting instructions for question generation.
        
        CRITICAL: This ensures correct formatting based on question type.
        TEXT types must NOT get code/diagram formatting.
        
        Args:
            question_type: Type of question
            bloom_level: Optional Bloom's level for context
            
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
        
        bloom_context = f" at {bloom_level} level" if bloom_level else ""
        
        if question_type in text_types:
            return f"""

╔════════════════════════════════════════════════════════════════╗
║           CRITICAL FORMATTING RULES FOR TEXT QUESTIONS        ║
╚════════════════════════════════════════════════════════════════╝

📝 TEXT-ONLY FORMATTING{bloom_context}:
- Use PLAIN TEXT only - NO code blocks, NO diagrams, NO mermaid, NO ASCII art
- Questions must be written as simple, clear text sentences
- Options (for MCQ) must be plain text like "A) Option text", "B) Option text"
- expected_answer: just the answer letter for MCQ (e.g., "B") or short text
- explanation: plain text paragraphs - NO special formatting
- DO NOT use: ```mermaid, ```python, flowchart, sequenceDiagram
- DO NOT include ANY code blocks or technical formatting markers
- Focus on CONCEPTUAL content, not visual representations
- Ensure language is precise and unambiguous"""

        elif question_type in code_types:
            return f"""

╔════════════════════════════════════════════════════════════════╗
║           MANDATORY CODE FORMATTING RULES                     ║
╚════════════════════════════════════════════════════════════════╝

💻 CODE FORMATTING{bloom_context}:
- ALL code snippets in question_text MUST be wrapped in markdown code blocks
- Use triple backticks with language: ```python, ```javascript, ```java, etc.
- NEVER include raw code without code block formatting
- Code in expected_answer MUST also use proper code blocks
- Example of CORRECT format: 
  ```python
  def hello():
      print('Hello World')

Example of WRONG format: "def hello(): print('Hello World')"

Include text descriptions alongside code to explain what it does

For output prediction, clearly indicate expected output format

This ensures proper syntax highlighting and formatting in the UI"""
        elif question_type in diagram_types:
            return f"""
╔════════════════════════════════════════════════════════════════╗
║ MANDATORY DIAGRAM FORMATTING RULES ║
╚════════════════════════════════════════════════════════════════╝

📊 DIAGRAM FORMATTING{bloom_context}:

ALL diagrams MUST use Mermaid.js syntax wrapped in ```mermaid code blocks

Use proper Mermaid syntax based on diagram type:

Flowcharts: flowchart TD/LR/R

Sequence diagrams: sequenceDiagram

Class diagrams: classDiagram

State diagrams: stateDiagram-v2

ER diagrams: erDiagram

Gantt charts: gantt

Include text descriptions explaining what the diagram shows

Example format:
flowchart TD
    A[Start] --> B{{Decision}}
    B -->|Yes| C[Process]
    B -->|No| D[End]
    Ensure diagrams are valid Mermaid syntax that will render correctly

For ASCII diagrams, use box drawing characters (┌ ─ ┐ │ └ ┘)"""
        elif question_type in math_types:
            return f"""
╔════════════════════════════════════════════════════════════════╗
║ MANDATORY MATH FORMATTING RULES ║
╚════════════════════════════════════════════════════════════════╝

🔢 MATH FORMATTING{bloom_context}:

Use LaTeX notation for ALL mathematical expressions

Inline math: wrap in single $ symbols like $x^2 + y^2 = z^2$

Block math: wrap in double $$ symbols for complex equations

Use proper LaTeX commands:

Fractions: $\\frac{{numerator}}{{denominator}}$

Summation: $\\sum_{{i=1}}^{{n}} i$

Square root: $\\sqrt{{x}}$

Multiplication: $\\times$

Greek letters: $\\alpha$, $\\beta$, $\\theta$

Example: "The time complexity is $O(n \\log n)$"

Show step-by-step calculations with LaTeX for each step

Ensure all mathematical symbols are properly escaped"""
        else:
            # SCENARIO-BASED or other types - conditional formatting
            return f"""
╔════════════════════════════════════════════════════════════════╗
║ GENERAL FORMATTING GUIDELINES{bloom_context} ║
╚════════════════════════════════════════════════════════════════╝

📋 FORMATTING RULES:

Use code blocks ONLY if the question requires actual code implementation

If no code is needed, use plain text formatting

For scenarios requiring code, wrap in ```python or appropriate language blocks

For scenarios requiring diagrams, use ```mermaid blocks

# For scenarios requiring math, use LaTeX notation $...$ or $$...$$ for complex equations
# Include proper LaTeX syntax for all mathematical expressions

Include clear text descriptions and explanations

Ensure formatting matches the cognitive requirements of {bloom_context if bloom_level else "the specified difficulty"}"""

    def _get_filtered_examples(self, question_type: str, bloom_level: Optional[str] = None) -> str:
        """
        Get filtered few-shot examples based on question type and bloom level.
        
        Args:
            question_type: Type of question
            bloom_level: Optional Bloom's level

        Returns:
            str: Filtered examples
        """
        base_examples = self.few_shot_examples
        
        # Add type-specific examples
        if question_type == "Multiple Choice":
            return base_examples + """
    MCQ EXAMPLE:
    {
        "question_text": "Which of the following best describes the purpose of the attention mechanism in transformer architectures?",
        "options": [
            "A) To process sequences sequentially like RNNs",
            "B) To allow the model to focus on relevant parts of the input",
            "C) To reduce the number of parameters in the model",
            "D) To replace all convolutional layers"
        ],
        "expected_answer": "B",
        "explanation": "The attention mechanism allows the model to weigh the importance of different input elements dynamically. This enables focusing on relevant context, which is key to transformer performance. Option B correctly captures this core purpose."
    }"""
        elif question_type == "Long Answer" and bloom_level == "Analyze":
            return """
    ANALYZE LEVEL EXAMPLE:
    {
        "question_text": "Compare and contrast Transformer architectures with traditional RNNs for sequence processing tasks. Analyze their respective strengths and weaknesses in terms of parallelization, long-range dependencies, and computational efficiency.",
        "expected_answer": "Transformers process sequences in parallel using self-attention, enabling efficient training on GPUs. They capture long-range dependencies through attention mechanisms without the sequential bottleneck of RNNs. However, transformers have O(n²) complexity with sequence length due to full attention, while RNNs are O(n) but suffer from vanishing gradients. Transformers excel at capturing global context but require more data and compute for training. RNNs, especially with LSTM/GRU variants, can be more efficient for shorter sequences and have better inductive bias for temporal data.",
        "explanation": "This question requires Analyze level thinking as students must break down both architectures, compare their components, and evaluate trade-offs. The answer requires synthesizing multiple aspects: parallelization capabilities, handling of long-range dependencies, computational complexity, and practical implications."
    }"""
        elif question_type == "Code Implementation" and bloom_level == "Apply":
            return """
    CODE IMPLEMENTATION EXAMPLE:
    {
        "question_text": "Implement a function `kmeans_clustering` that performs K-means clustering on a given dataset. The function should take as input: data points (numpy array of shape (n_samples, n_features)), number of clusters K, and maximum iterations. Return the cluster centroids and labels for each point.",
        "expected_answer": "```python\nimport numpy as np\n\ndef kmeans_clustering(X, K, max_iters=100):\n    # Randomly initialize centroids\n    centroids = X[np.random.choice(X.shape[0], K, replace=False)]\n    \n    for _ in range(max_iters):\n        # Assign points to nearest centroid\n        distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))\n        labels = np.argmin(distances, axis=0)\n        \n        # Update centroids\n        new_centroids = np.array([X[labels == k].mean(axis=0) for k in range(K)])\n        \n        # Check convergence\n        if np.all(centroids == new_centroids):\n            break\n        centroids = new_centroids\n    \n    return centroids, labels\n```",
        "explanation": "This question requires Apply level thinking as students must implement the K-means algorithm from scratch, demonstrating understanding of the algorithm's steps: initialization, assignment, and update phases. The implementation requires practical application of numpy operations and algorithmic thinking."
    }"""
        return base_examples

    def _get_cot_instructions(self, question_type: str, bloom_level: Optional[str] = None) -> str:
        """
        Get Chain of Thought instructions adapted for question type and bloom level.

        Args:
            question_type: Type of question
            bloom_level: Optional Bloom's level

        Returns:
            str: CoT instructions
        """
        base_cot = CHAIN_OF_THOUGHT_PROMPT

        if bloom_level:
            level_info = self.BLOOM_LEVELS.get(bloom_level, self.BLOOM_LEVELS["Understand"])
            base_cot += f"""
BLOOM'S LEVEL SPECIFIC THINKING FOR {bloom_level}:

First, ensure the question targets {level_info['cognitive_demand']}

Select appropriate action verbs from: {', '.join(level_info['keywords'][:5])}

Design the question to require {level_info['question_style']}

In explanation, explicitly map to {bloom_level} level criteria"""

        if question_type == "Multiple Choice":
            base_cot += """
MCQ GENERATION STEPS:
5. Create 4 options with the correct answer and 3 plausible distractors
6. Ensure distractors test common misconceptions
7. Make all options grammatically consistent
8. Avoid patterns that make the correct answer obvious"""
        elif question_type in ["Code Implementation", "Coding Problem"]:
            base_cot += """
CODE GENERATION STEPS:
5. Design the problem to test specific programming concepts
6. Include edge cases and error handling considerations
7. Provide starter code structure if applicable
8. Include test cases to validate solution
9. Ensure solution code is efficient and follows best practices"""
        elif question_type in ["Diagram-Based"]:
            base_cot += """
DIAGRAM GENERATION STEPS:
5. Choose appropriate diagram type (flowchart, sequence, class, etc.)
6. Design the diagram to illustrate key concepts
7. Use clear labels and proper Mermaid syntax
8. Include explanatory text alongside diagram
9. Ensure diagram is accurate and readable"""
        return base_cot

    def _build_generation_request(
        self,
        subject: str,
        question_type: str,
        num_questions: int,
        difficulty_level: str = "Medium",
        bloom_level: Optional[str] = None,
        additional_context: str = "",
    ) -> str:
        """
        Build the actual generation request text.

        Args:
            subject: Subject area
            question_type: Question type
            num_questions: Number of questions
            difficulty_level: Difficulty level
            bloom_level: Bloom's taxonomy level
            additional_context: Additional context

        Returns:
            str: Generation request text
        """
        # Determine cognitive level display
        if bloom_level:
            cognitive_display = f"Bloom's Taxonomy Level: {bloom_level}"
            level_info = self.BLOOM_LEVELS.get(bloom_level, self.BLOOM_LEVELS["Understand"])
            cognitive_display += f"\nCognitive Demand: {level_info['cognitive_demand']}"
            cognitive_display += f"\nRequired Verbs: {', '.join(level_info['keywords'][:5])}"
        else:
            cognitive_display = f"Difficulty Level: {difficulty_level}"

        request = f"""Generate exactly {num_questions} HIGHLY DIVERSE AND INNOVATIVE {question_type} questions for {subject}.
╔════════════════════════════════════════════════════════════════╗
║ GENERATION SPECIFICATIONS ║
╚════════════════════════════════════════════════════════════════╝

📚 Subject: {subject}
❓ Question Type: {question_type}
🧠 {cognitive_display}
🔢 Number of Questions: {num_questions}"""
        if additional_context:
            request += f"\n📋 Additional Context: {additional_context}"

        # Add type-specific formatting instructions
        formatting_instructions = self._get_type_specific_formatting(question_type, bloom_level)
        request += formatting_instructions

        request += f"""
🎯 DIVERSITY & INNOVATION REQUIREMENTS:

EACH question MUST cover DIFFERENT concepts/subtopics within {subject}

NO repetition - vary the focus areas, scenarios, and applications

Mix theoretical, practical, analytical, and applied perspectives

Include edge cases, real-world scenarios, and cutting-edge concepts

Create NOVEL questions NOT commonly found in textbooks or online

Vary question complexity patterns - some direct, some analytical

Use different problem contexts - change domains, industries, situations

Make questions INTERESTING and thought-provoking for MTech students

CRITICAL REQUIREMENTS:

Generate EXACTLY {num_questions} questions - NO MORE, NO LESS

Return ONLY valid JSON array format (no markdown, no extra text)

No text before or after the JSON array

Every question MUST have all fields populated (no null/empty fields)

question_text MUST be complete, clear, and engaging

expected_answer MUST be detailed, accurate, and comprehensive

explanation MUST provide deep educational value and reasoning

Options (for MCQ) MUST be plausible and distinct - no obvious wrong answers

FORMAT REQUIREMENTS:

Return ONLY this JSON array format:
[{{"question_text": "...", "question_type": "{question_type}", "difficulty_level": "{difficulty_level}", "bloom_level": "{bloom_level if bloom_level else 'Not Specified'}", "subject": "{subject}", "options": ["...", "...", "...", "..."], "expected_answer": "...", "explanation": "...", "tags": ["..."], "content_flags": {{"has_code": false, "has_latex": false, "has_diagram": false, "code_language": null}}}}]

CONTENT_FLAGS FIELD (MANDATORY):

has_code: true if question/answer contains programming code

has_latex: true if question/answer contains mathematical formulas (LaTeX)

has_diagram: true if question/answer contains mermaid/diagram syntax

code_language: if has_code is true, specify the language (python, javascript, sql, etc.) otherwise null

Generate {num_questions} diverse, innovative, and unique questions as JSON array now:"""
        return request
    

    def build_batch_generation_prompt(
        self,
        subjects: list,
        question_types: list,
        difficulty_levels: list,
        bloom_levels: Optional[List[str]] = None,
        questions_per_config: int = 2,
    ) -> str:
        """
        Build prompt for generating multiple question configurations at once.

        Args:
            subjects: List of subjects
            question_types: List of question types
            difficulty_levels: List of difficulty levels
            bloom_levels: Optional list of Bloom's levels
            questions_per_config: Questions per configuration

        Returns:
            str: Batch generation prompt
        """
        configs = []
        
        if bloom_levels:
            for subject in subjects:
                for q_type in question_types:
                    for bloom in bloom_levels:
                        configs.append(
                            f"{questions_per_config} {q_type} questions for {subject} "
                            f"at {bloom} Bloom's level"
                        )
        else:
            for subject in subjects:
                for q_type in question_types:
                    for difficulty in difficulty_levels:
                        configs.append(
                            f"{questions_per_config} {q_type} questions for {subject} "
                            f"at {difficulty} difficulty level"
                        )

        config_text = "\n".join([f"  - {config}" for config in configs])

        return f"""Generate questions for multiple configurations in a single batch:

CONFIGURATIONS:
{config_text}

Return ALL questions as a single valid JSON array.
Each question must include its configuration metadata.
"""
    
    def build_assignment_prompt(
        self,
        subject: str,
        topic: str,
        assignment_type: str,
        num_tasks: int,
        max_marks: int,
        bloom_distribution: Dict[str, int],
        description: str,
        chat_context: str = "",
        include_solutions: bool = True,
        include_starter_code: bool = False,
        include_test_cases: bool = False
    ) -> str:
        """
        Build prompt for assignment generation with Bloom's taxonomy.

        Args:
            subject: Subject area
            topic: Specific topic
            assignment_type: Type of assignment
            num_tasks: Number of tasks
            max_marks: Maximum marks
            bloom_distribution: Distribution of Bloom's levels
            description: Assignment description
            chat_context: Additional context
            include_solutions: Whether to include solutions
            include_starter_code: Whether to include starter code
            include_test_cases: Whether to include test cases

        Returns:
            str: Formatted prompt
        """
        # Validate bloom distribution
        if not self.validate_bloom_distribution(bloom_distribution):
            logger.warning("Invalid bloom distribution, using default")
            bloom_distribution = {
                "Remember": 10,
                "Understand": 20,
                "Apply": 30,
                "Analyze": 20,
                "Evaluate": 10,
                "Create": 10
            }

        bloom_levels_str = "\n".join([
            f"- {level}: {weight}%" 
            for level, weight in bloom_distribution.items()
        ])

        prompt = f"""Generate a comprehensive {assignment_type} assignment with the following specifications:

    ## Assignment Details
    - Subject: {subject}
    - Topic: {topic}
    - Type: {assignment_type}
    - Number of Tasks: {num_tasks}
    - Total Marks: {max_marks}
    - Bloom's Taxonomy Distribution:
    {bloom_levels_str}

    ## Assignment Description
    {description}

    ## Requirements
    1. Create {num_tasks} distinct tasks/questions
    2. Distribute marks according to Bloom's levels
    3. Each task should clearly indicate its Bloom's level
    4. Provide clear instructions and requirements
    5. Include appropriate hints where helpful
    {f"- Include starter code for applicable tasks" if include_starter_code else ""}
    {f"- Include comprehensive solutions" if include_solutions else ""}
    {f"- Include test cases for verification" if include_test_cases else ""}

    ## Additional Context
    {chat_context if chat_context else "No additional context provided."}

    ## Output Format
    Return the assignment in JSON format with the following structure:
    {{
        "tasks": [
            {{
                "task_id": "task_1",
                "title": "Task title",
                "description": "Detailed task description",
                "points": 20,
                "bloom_level": "Apply",
                "requirements": ["Requirement 1", "Requirement 2"],
                "hints": ["Hint 1", "Hint 2"],
                "expected_output": "Description of expected output",
                "starter_code": "Optional starter code",
                "solution_code": "Optional solution code",
                "test_cases": ["Test case 1", "Test case 2"]
            }}
        ],
        "submission_guidelines": ["Guideline 1", "Guideline 2"],
        "evaluation_criteria": [
            {{
                "criterion": "Criterion name",
                "weight": 0.4,
                "description": "Description",
                "bloom_level": "Apply"
            }}
        ],
        "learning_objectives": ["Objective 1", "Objective 2"],
        "generated_files": [
            {{
                "filename": "file.py",
                "content": "File content",
                "file_type": "code",
                "language": "python",
                "description": "File description"
            }}
        ]
    }}

    Ensure all tasks are appropriately calibrated to their assigned Bloom's taxonomy levels.
    """
        return prompt

# ====== THIS FUNCTION MUST BE OUTSIDE THE CLASS ======
def get_prompt_builder() -> PromptBuilder:
    """
    Get or create a prompt builder instance.
    
    Returns:
        PromptBuilder: Prompt builder instance
    """
    return PromptBuilder()


