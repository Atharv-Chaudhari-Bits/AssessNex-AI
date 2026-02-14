"""
Customized Question Generation Module.

This module implements the agentic AI logic for generating MTech level
questions calibrated to specific Bloom's taxonomy levels using Azure OpenAI
and structured prompting.
"""

import json
from typing import List, Dict, Any, Optional
from backend.app.llm_client import get_llm_client
from backend.app.prompts.prompt_manager import PromptBuilder
from backend.app.utils import (
    get_logger,
    generate_question_id,
    parse_llm_response,
    format_question_response,
    fix_question_latex,
)

logger = get_logger(__name__)


class CustomizedQuestionAgent:
    """
    Agent for generating MTech level questions calibrated to Bloom's taxonomy levels.

    This agent uses Azure OpenAI to generate high-quality, structured
    questions for various AI/ML subjects based on specific Bloom's taxonomy
    levels chosen by the user.
    """

    # Bloom's taxonomy level definitions and guidance
    BLOOM_LEVELS = {
        "Remember": {
            "description": "Recall facts, terms, basic concepts",
            "keywords": ["define", "list", "recall", "name", "identify", "state"],
            "cognitive_demand": "Lowest - simple recall",
            "question_style": "Direct recall of facts, definitions, or basic properties",
            "icon": "🔵",
            "color": "#4299E1"
        },
        "Understand": {
            "description": "Explain ideas or concepts",
            "keywords": ["explain", "describe", "summarize", "interpret", "paraphrase", "classify"],
            "cognitive_demand": "Low - demonstrate comprehension",
            "question_style": "Describe concepts in own words, summarize, give examples",
            "icon": "🟢",
            "color": "#48BB78"
        },
        "Apply": {
            "description": "Use information in new situations",
            "keywords": ["apply", "demonstrate", "implement", "solve", "use", "compute"],
            "cognitive_demand": "Medium - execute or implement",
            "question_style": "Solve problems, apply formulas, use methods in new contexts",
            "icon": "🟠",
            "color": "#ED8936"
        },
        "Analyze": {
            "description": "Draw connections among ideas",
            "keywords": ["analyze", "compare", "contrast", "differentiate", "examine", "investigate"],
            "cognitive_demand": "Medium-High - distinguish, organize, attribute",
            "question_style": "Break down concepts, find patterns, analyze relationships",
            "icon": "🟣",
            "color": "#9F7AEA"
        },
        "Evaluate": {
            "description": "Justify a stand or decision",
            "keywords": ["evaluate", "critique", "assess", "justify", "debate", "recommend"],
            "cognitive_demand": "High - check, critique, judge",
            "question_style": "Make judgments, defend positions, critique methodologies",
            "icon": "🔴",
            "color": "#F56565"
        },
        "Create": {
            "description": "Produce new or original work",
            "keywords": ["design", "develop", "formulate", "propose", "construct", "synthesize"],
            "cognitive_demand": "Highest - generate, plan, produce",
            "question_style": "Design solutions, create models, develop novel approaches",
            "icon": "🟤",
            "color": "#D69E2E"
        }
    }

    # Question type specific format requirements
    QUESTION_TYPE_FORMATS = {
        "Multiple Choice": '''
FORMAT REQUIREMENTS FOR MULTIPLE CHOICE:
- MUST include exactly 4 options in the 'options' array
- Options should be labeled A) Option text, B) Option text, etc.
- One clearly correct answer
- Plausible distractors that test common misconceptions
- expected_answer should be the letter of correct option (e.g., "B")
- Explanation should justify why correct and why others are wrong
''',
        "True/False":'''
FORMAT REQUIREMENTS FOR TRUE/FALSE:
- MUST include 2 options in the 'options' array: ["A) True", "B) False"]
- expected_answer should be "A" for True or "B" for False
- Statement should be unequivocally true or false
- Explanation should clarify why the statement is true/false
''',
        "Diagram-Based": '''
FORMAT REQUIREMENTS FOR DIAGRAM-BASED:
- MUST include diagram description in question_text
- For answer, use Mermaid.js syntax wrapped in ```mermaid code blocks
- Example answer format:
  ```mermaid
  flowchart TD
      A[Start] --> B{{Decision}}
      B -->|Yes| C[Process]
      B -->|No| D[End]
  ```
- Include text explanation alongside diagram
''',
        "Code-Based":'''
FORMAT REQUIREMENTS FOR CODE-BASED:
- MUST include code in question_text wrapped in ```language blocks
- expected_answer MUST include code wrapped in ```language blocks
- Use appropriate language (python, javascript, etc.)
- Include comments in code for clarity
''',
        "Code Implementation": '''
FORMAT REQUIREMENTS FOR CODE IMPLEMENTATION:
- MUST include code in question_text wrapped in ```language blocks
- expected_answer MUST include complete solution code in ```language blocks
- Use appropriate language (python, javascript, etc.)
- Include comments explaining the code
- Test cases should be included in explanation if applicable
''',
        "Code Output Prediction": '''
FORMAT REQUIREMENTS FOR CODE OUTPUT PREDICTION:
- MUST include code in question_text wrapped in ```language blocks
- expected_answer should be the exact output as text
- If output spans multiple lines, preserve formatting
- Explanation should walk through code execution step by step
''',
        "Coding Problem": '''
FORMAT REQUIREMENTS FOR CODING PROBLEM:
- MUST include problem description and any starter code in question_text
- expected_answer MUST include complete solution code in ```language blocks
- Include time/space complexity analysis in explanation
- Include edge cases and test cases in explanation
''',
        "Numerical Problem": '''
FORMAT REQUIREMENTS FOR NUMERICAL PROBLEM:
- MUST use LaTeX for all mathematical expressions
- Inline math: $x^2 + y^2 = z^2$
- Block math: $$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$
- expected_answer should show step-by-step solution with LaTeX
- Include units and precision in answer
''',
        "Short Answer": '''
FORMAT REQUIREMENTS FOR SHORT ANSWER:
- Concise question expecting 2-5 sentence answer
- expected_answer should be complete but concise
- Options field should be null
- Explanation should elaborate on key points
''',
        "Long Answer": '''
FORMAT REQUIREMENTS FOR LONG ANSWER:
- Open-ended question expecting paragraph response
- expected_answer should be comprehensive
- Options field should be null
- Explanation should include evaluation criteria
''',
        "Essay": '''
FORMAT REQUIREMENTS FOR ESSAY:
- Question should specify expected length (e.g., 500-800 words)
- expected_answer should outline key points to cover
- Options field should be null
- Explanation should include grading rubric
''',
        "Scenario-Based": '''
FORMAT REQUIREMENTS FOR SCENARIO-BASED:
- Present real-world scenario in question_text
- expected_answer should be detailed solution approach
- Options field null unless multiple choice
- Explanation should connect to theoretical concepts
'''
    }

    SYSTEM_PROMPT = """You are an expert MTech level question generator for AI/ML subjects.
Your task is to generate high-quality, academic-level questions that target specific Bloom's taxonomy levels.
Always respond with valid JSON format containing question details.

IMPORTANT CALIBRATION REQUIREMENTS:
1. Generate questions appropriate for MTech level students
2. Questions MUST be calibrated EXACTLY to the specified Bloom's level - no higher, no lower
3. Each question must use action verbs appropriate for that specific Bloom's level
4. Ensure questions are technically accurate and well-structured
5. Provide clear, concise questions without ambiguity
6. Include detailed explanations for answers
7. For multiple choice questions, ensure options are plausible but clearly different
8. Questions should test concepts, applications, and analytical thinking appropriate to the Bloom's level
9. In the explanation, explicitly justify why this question targets that specific Bloom's level"""

    def __init__(self):
        """Initialize the customized question generation agent."""
        self.llm_client = get_llm_client()
        self.prompt_builder = PromptBuilder()
        logger.info("CustomizedQuestionAgent initialized with PromptBuilder")

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
==================================================
BLOOM'S TAXONOMY CALIBRATION: {bloom_level} LEVEL
==================================================

Level Description: {level_info['description']}
Cognitive Demand: {level_info['cognitive_demand']}
Question Style: {level_info['question_style']}

REQUIRED ACTION VERBS (use these in questions):
- Primary verbs: {', '.join(level_info['keywords'][:3])}
- Secondary verbs: {', '.join(level_info['keywords'][3:6])}

STRICT CALIBRATION RULES:
1. DO NOT create questions at Remember/Understand level if target is {bloom_level}
2. DO NOT create questions at Evaluate/Create level if target is {bloom_level}
3. Each question MUST clearly demonstrate {bloom_level} level cognitive skills
4. The complexity and depth MUST match {bloom_level} expectations
5. Students should need to {level_info['keywords'][0]} to answer correctly

VERIFICATION: After generating, verify each question is truly at {bloom_level} level
==================================================
"""
        return guidance

    def _get_question_type_format(self, question_type: str) -> str:
        """
        Get format requirements for specific question type.
        
        Args:
            question_type: Type of question
            
        Returns:
            str: Format requirements
        """
        return self.QUESTION_TYPE_FORMATS.get(question_type, """
FORMAT REQUIREMENTS FOR GENERAL QUESTIONS:
- question_text: Clear, well-structured question
- options: Array of options (for MCQ) or null for open-ended
- expected_answer: Complete answer
- explanation: Detailed explanation with reasoning
- tags: Array of relevant topics
""")

    def _build_generation_prompt(
        self,
        subject: str,
        question_type: str,
        bloom_level: str,
        num_questions: int,
        additional_context: str = "",
        topic_focus: Optional[List[str]] = None,
    ) -> str:
        """
        Build the prompt for customized question generation with Bloom's level calibration.

        Args:
            subject: Subject area
            question_type: Type of questions
            bloom_level: Bloom's taxonomy level
            num_questions: Number of questions
            additional_context: Additional context
            topic_focus: Specific topics to focus on

        Returns:
            str: Formatted prompt for LLM
        """
        # Get Bloom's level guidance
        bloom_guidance = self._get_bloom_guidance(bloom_level)
        
        # Get question type specific format
        type_format = self._get_question_type_format(question_type)
        
        # Format topic focus if provided
        topic_str = ""
        if topic_focus:
            topic_str = f"FOCUS TOPICS: {', '.join(topic_focus)}\nEnsure questions specifically cover these topics at {bloom_level} level.\n"
        
        # Enhance additional context with Bloom's requirements and type-specific format
        enhanced_context = f"""
{additional_context}

{topic_str}

{bloom_guidance}

{type_format}

╔════════════════════════════════════════════════════════════════╗
║                 CRITICAL CALIBRATION CHECKLIST                 ║
╠════════════════════════════════════════════════════════════════╣
║  ☐ All questions MUST be at EXACTLY {bloom_level} level          ║
║  ☐ Use action verbs: {', '.join(self.BLOOM_LEVELS[bloom_level]['keywords'][:3])}   ║
║  ☐ NOT easier than {bloom_level} (not Remember/Understand)     ║
║  ☐ NOT harder than {bloom_level} (not Evaluate/Create)         ║
║  ☐ Each question clearly demonstrates {bloom_level} thinking    ║
║  ☐ Explanation must justify Bloom's level alignment            ║
║  ☐ Follow {question_type} format requirements EXACTLY          ║
╚════════════════════════════════════════════════════════════════╝

OUTPUT FORMAT:
Return a JSON object with a "questions" array containing {num_questions} questions.
Each question must have:
- question_text: The actual question (with action verbs at {bloom_level} level)
- options: For MCQ only, array of 4 choices; for other types, null
- expected_answer: Correct answer/solution (with proper formatting for the question type)
- explanation: Detailed explanation with Bloom's level justification
- tags: Array of relevant topic tags
- bloom_level: Set to "{bloom_level}" (explicitly set this)
"""

        # Use PromptBuilder to construct the prompt
        prompt = self.prompt_builder.build_question_generation_prompt(
            subject=subject,
            question_type=question_type,
            bloom_level=bloom_level,
            num_questions=num_questions,
            additional_context=enhanced_context,
            use_cot=True,
            use_few_shots=True,
        )

        logger.debug(f"Generated calibrated prompt for {num_questions} {question_type} questions at Bloom's level {bloom_level}")
        return prompt

    def _get_type_example(self, question_type: str, bloom_level: str) -> str:
        """
        Get example for specific question type.
        
        Args:
            question_type: Type of question
            bloom_level: Bloom's level
            
        Returns:
            str: Example JSON
        """
        examples = {
            "Multiple Choice": '''
    EXAMPLE OF CORRECT MULTIPLE CHOICE FORMAT:
    {
    "question_text": "Which of the following best describes the attention mechanism in transformers?",
    "options": [
        "A) A sequential processing mechanism",
        "B) A way to focus on relevant parts of input",
        "C) A replacement for all neural layers",
        "D) A type of activation function"
    ],
    "expected_answer": "B",
    "explanation": "The attention mechanism allows the model to weigh the importance of different input elements. This is a key innovation in transformers that enables parallel processing and capturing long-range dependencies.",
    "tags": ["transformers", "attention", "neural networks"],
    "bloom_level": "''' + bloom_level + '''"
    }''',
            "True/False": '''
    EXAMPLE OF CORRECT TRUE/FALSE FORMAT:
    {
    "question_text": "The transformer architecture processes sequences in parallel rather than sequentially.",
    "options": ["A) True", "B) False"],
    "expected_answer": "A",
    "explanation": "Transformers use self-attention to process all positions simultaneously, unlike RNNs which process sequentially.",
    "tags": ["transformers", "architecture"],
    "bloom_level": "''' + bloom_level + '''"
    }''',
            "Diagram-Based": '''
    EXAMPLE OF CORRECT DIAGRAM-BASED FORMAT:
    {
    "question_text": "Draw a flowchart showing the training loop of a neural network including forward pass, loss calculation, backpropagation, and weight update.",
    "options": null,
    "expected_answer": "```mermaid\\nflowchart TD\\n    A[Input Data] --> B[Forward Pass]\\n    B --> C[Calculate Loss]\\n    C --> D[Backpropagation]\\n    D --> E[Update Weights]\\n    E -->|Next Epoch| B\\n    E --> F[Converged?]\\n    F -->|Yes| G[Final Model]\\n    F -->|No| B\\n```\\n\\nThe diagram shows the iterative training process where forward pass computes predictions, loss is calculated, gradients flow backward, and weights are updated.",
    "explanation": "This diagram illustrates the complete training loop. The process repeats until convergence, with each epoch refining the model parameters.",
    "tags": ["neural networks", "training", "backpropagation"],
    "bloom_level": "''' + bloom_level + '''"
    }''',
            "Code Implementation": '''
    EXAMPLE OF CORRECT CODE IMPLEMENTATION FORMAT:
    {
    "question_text": "Implement a function `binary_search(arr, target)` that returns the index of target in sorted array arr, or -1 if not found.",
    "options": null,
    "expected_answer": "```python\\ndef binary_search(arr, target):\\n    left, right = 0, len(arr) - 1\\n    \\n    while left <= right:\\n        mid = (left + right) // 2\\n        if arr[mid] == target:\\n            return mid\\n        elif arr[mid] < target:\\n            left = mid + 1\\n        else:\\n            right = mid - 1\\n    \\n    return -1\\n```\\n\\nTime complexity: O(log n), Space complexity: O(1)",
    "explanation": "Binary search works by repeatedly dividing the search interval in half. This implementation handles edge cases and follows the divide-and-conquer principle at the Apply level.",
    "tags": ["algorithms", "searching", "binary search"],
    "bloom_level": "''' + bloom_level + '''"
    }''',
            "Code Output Prediction": '''
    EXAMPLE OF CORRECT CODE OUTPUT PREDICTION FORMAT:
    {
    "question_text": "```python\\nx = [1, 2, 3, 4]\\ny = [i**2 for i in x if i % 2 == 0]\\nprint(y)\\n```\\n\\nWhat is the output of this code?",
    "options": null,
    "expected_answer": "[4, 16]",
    "explanation": "The list comprehension iterates through x, squares each element, but only includes elements where i % 2 == 0 (even numbers). So 2² = 4 and 4² = 16 are included.",
    "tags": ["python", "list comprehension"],
    "bloom_level": "''' + bloom_level + '''"
    }''',
            "Numerical Problem": '''
    EXAMPLE OF CORRECT NUMERICAL PROBLEM FORMAT:
    {
    "question_text": "Calculate the time complexity of the following recurrence relation using the Master Theorem: $T(n) = 3T(n/4) + n\\\\log n$",
    "options": null,
    "expected_answer": "$a = 3$, $b = 4$, $f(n) = n\\\\log n$\\n\\n$\\\\log_b a = \\\\log_4 3 \\\\approx 0.792$\\n\\nCompare $f(n)$ with $n^{{\\\\log_b a}}$:\\n$n\\\\log n$ vs $n^{{0.792}}$\\n\\n$n\\\\log n = \\\\Theta(n^{{0.792}}\\\\log n)$ falls under Case 2 of Master Theorem\\n\\nTherefore, $T(n) = \\\\Theta(n^{{\\\\log_4 3}} \\\\log^2 n)$",
    "explanation": "This requires applying the Master Theorem correctly, identifying the parameters and comparing functions. The solution shows step-by-step reasoning.",
    "tags": ["algorithms", "complexity", "master theorem"],
    "bloom_level": "''' + bloom_level + '''"
    }''',
            "Long Answer": '''
    EXAMPLE OF CORRECT LONG ANSWER FORMAT:
    {
    "question_text": "Explain the concept of attention mechanism in transformers and analyze how it addresses the limitations of RNNs for sequence processing tasks.",
    "options": null,
    "expected_answer": "The attention mechanism allows the model to dynamically weigh the importance of different input elements when producing each output. Unlike RNNs which process sequences sequentially and suffer from vanishing gradients, attention enables parallel processing and captures long-range dependencies effectively. Self-attention computes queries, keys, and values from input embeddings, then uses dot products to determine relevance between positions. Multi-head attention runs multiple attention operations in parallel, allowing the model to focus on different types of relationships. This architecture eliminates the sequential bottleneck of RNNs, enables better GPU utilization, and achieves state-of-the-art results on various NLP tasks.",
    "explanation": "This question tests deep understanding of transformer architecture, requiring comparison with RNNs and analysis of the attention mechanism's advantages.",
    "tags": ["transformers", "attention", "RNN", "NLP"],
    "bloom_level": "''' + bloom_level + '''"
    }'''
        }
        
        return examples.get(question_type, "")

    def generate_customized_questions(
        self,
        subject: str,
        question_type: str,
        bloom_level: str,
        num_questions: int,
        additional_context: str = "",
        topic_focus: Optional[List[str]] = None,
        diagram_format: Optional[str] = None,
        require_bloom_justification: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions calibrated to a specific Bloom's taxonomy level.
        
        This is the main method for generating customized questions with
        precise Bloom's taxonomy calibration.

        Args:
            subject: Subject area for questions
            question_type: Type of questions (Multiple Choice, Long Answer, etc.)
            bloom_level: Bloom's taxonomy level (Remember, Understand, Apply, Analyze, Evaluate, Create)
            num_questions: Number of questions to generate
            additional_context: Additional context for generation
            topic_focus: Specific topics to focus on
            diagram_format: Format for diagrams (Mermaid/ASCII) - only for Diagram-Based
            require_bloom_justification: Whether explanations must justify Bloom's level

        Returns:
            List[Dict[str, Any]]: List of generated questions with Bloom's level calibration

        Raises:
            ValueError: If bloom_level is invalid
            Exception: If question generation fails
        """
        # Validate Bloom's level
        if bloom_level not in self.BLOOM_LEVELS:
            valid_levels = ", ".join(self.BLOOM_LEVELS.keys())
            raise ValueError(f"Invalid Bloom's level: {bloom_level}. Must be one of: {valid_levels}")

        logger.info(
            f"CALIBRATED GENERATION: {num_questions} {question_type} questions "
            f"for {subject} at EXACT Bloom's level: {bloom_level}"
        )
        
        if topic_focus:
            logger.info(f"Topic focus: {', '.join(topic_focus)}")

        # Add diagram format to context if specified
        if diagram_format and question_type in ["Diagram-Based", "Diagram"]:
            if "mermaid" in diagram_format.lower():
                additional_context += "\n\nIMPORTANT: Use Mermaid.js syntax for ALL diagrams. Wrap diagrams in ```mermaid code blocks."
            else:
                additional_context += "\n\nIMPORTANT: Use ASCII art with box drawing characters (┌ ─ ┐ │ └ ┘) for ALL diagrams. Do NOT use Mermaid.js."

        # Add Bloom's justification requirement
        if require_bloom_justification:
            additional_context += f"\n\nIMPORTANT: In the explanation field, explicitly state WHY this question is at the {bloom_level} level of Bloom's taxonomy. Reference the action verbs and cognitive processes required."

        try:
            # Build prompt with Bloom's level calibration
            prompt = self._build_generation_prompt(
                subject=subject,
                question_type=question_type,
                bloom_level=bloom_level,
                num_questions=num_questions,
                additional_context=additional_context,
                topic_focus=topic_focus,
            )

            logger.debug(f"Calibration prompt generated: {prompt[:200]}...")

            # Generate response from LLM
            response = self.llm_client.generate_json_message(prompt)

            logger.debug(f"Raw LLM response received: {response[:200]}...")

            # Parse response
            parsed_response = parse_llm_response(response)

            # Extract and process questions
            questions = self._process_calibrated_response(
                parsed_response,
                subject,
                question_type,
                bloom_level,
                topic_focus,
            )

            # Apply unified formatting
            from backend.app.utils import format_all_questions_with_flags, fix_question_latex
            
            questions = format_all_questions_with_flags(questions, question_type)
            questions = [fix_question_latex(q) for q in questions]

            # Add Bloom's level metadata and verify calibration
            for q in questions:
                q['bloom_level'] = bloom_level
                q['cognitive_demand'] = self.BLOOM_LEVELS[bloom_level]['cognitive_demand']
                q['calibration_type'] = 'bloom_taxonomy'
                q['verification_status'] = 'calibrated'
                
            logger.info(f"SUCCESS: Generated {len(questions)} calibrated questions at Bloom's level {bloom_level}")
            
            # Log calibration verification
            levels_found = {}
            for q in questions:
                level = q.get('bloom_level', 'unknown')
                levels_found[level] = levels_found.get(level, 0) + 1
            
            if len(levels_found) == 1 and bloom_level in levels_found:
                logger.info(f"CALIBRATION VERIFIED: All {len(questions)} questions at {bloom_level} level")
            else:
                logger.warning(f"CALIBRATION MISMATCH: Expected all {bloom_level}, found {levels_found}")
            
            return questions

        except Exception as e:
            logger.error(f"Error in customized question generation: {str(e)}")
            raise

    def _process_calibrated_response(
        self,
        response: Dict[str, Any],
        subject: str,
        question_type: str,
        bloom_level: str,
        topic_focus: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process and structure the LLM response with Bloom's level calibration.

        Args:
            response: Raw response from LLM
            subject: Subject area
            question_type: Type of questions
            bloom_level: Bloom's taxonomy level
            topic_focus: Focus topics for tagging

        Returns:
            List[Dict[str, Any]]: Processed questions with calibration metadata
        """
        questions = []

        try:
            logger.info(f"Processing calibrated response for bloom_level={bloom_level}")
            
            # Handle different response formats
            if isinstance(response, dict):
                if "questions" in response:
                    raw_questions = response["questions"]
                elif isinstance(response, dict) and len(response) > 0:
                    raw_questions = [response]
                else:
                    raw_questions = []
            elif isinstance(response, list):
                raw_questions = response
            else:
                logger.warning(f"Unexpected response type: {type(response)}")
                return []

            # Process each question
            for idx, question_data in enumerate(raw_questions):
                if not isinstance(question_data, dict):
                    logger.warning(f"Skipping invalid question data at index {idx}")
                    continue

                try:
                    # Extract question fields with calibration focus
                    question_text = question_data.get("question_text") or question_data.get("question") or ""
                    if not isinstance(question_text, str):
                        question_text = str(question_text)
                    
                    options = question_data.get("options")
                    if options is not None and not isinstance(options, list):
                        # Convert single option to list or set to None
                        if isinstance(options, str) and question_type in ["Multiple Choice", "True/False"]:
                            options = [options]
                        else:
                            options = None
                    
                    # Ensure MCQ has proper options
                    if question_type in ["Multiple Choice", "True/False"]:
                        if not options or len(options) == 0:
                            # Generate default options if missing
                            if question_type == "Multiple Choice":
                                options = ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"]
                            elif question_type == "True/False":
                                options = ["A) True", "B) False"]
                    
                    expected_answer = question_data.get("expected_answer", "")
                    if not isinstance(expected_answer, str):
                        expected_answer = str(expected_answer) if expected_answer else ""
                    
                    explanation = question_data.get("explanation", "")
                    if not isinstance(explanation, str):
                        explanation = str(explanation) if explanation else ""
                    
                    # Get tags, merge with topic focus
                    tags = question_data.get("tags", [])
                    if not isinstance(tags, list):
                        tags = []
                    
                    # Add topic focus to tags if provided
                    if topic_focus:
                        tags.extend(topic_focus)
                    tags = list(set(tags))  # Remove duplicates
                    
                    # Preserve bloom_level from LLM if provided, otherwise use requested level
                    question_bloom = question_data.get("bloom_level", bloom_level)
                    
                    processed_question = format_question_response(
                        question_id=generate_question_id(),
                        subject=subject,
                        question_type=question_type,
                        difficulty_level=None,  # Deprecated
                        bloom_level=question_bloom,
                        question_text=question_text,
                        options=options,
                        expected_answer=expected_answer,
                        explanation=explanation,
                        tags=tags,
                    )
                    
                    # Add calibration metadata
                    processed_question['bloom_level'] = question_bloom
                    processed_question['cognitive_demand'] = self.BLOOM_LEVELS.get(question_bloom, {}).get('cognitive_demand', 'Unknown')
                    processed_question['calibration_level'] = bloom_level
                    processed_question['question_style'] = self.BLOOM_LEVELS.get(question_bloom, {}).get('question_style', '')
                    
                    # Check if explanation contains Bloom's justification
                    if 'bloom' in explanation.lower() or 'taxonomy' in explanation.lower() or question_bloom.lower() in explanation.lower():
                        processed_question['has_bloom_justification'] = True
                    else:
                        processed_question['has_bloom_justification'] = False
                        logger.debug(f"Question {idx} missing explicit Bloom's justification")
                    
                    questions.append(processed_question)
                    logger.debug(f"Processed calibrated question {idx + 1} with bloom_level={question_bloom}")

                except Exception as e:
                    logger.warning(f"Error processing calibrated question at index {idx}: {str(e)}")
                    continue

            logger.info(f"Successfully processed {len(questions)} calibrated questions")
            return questions

        except Exception as e:
            logger.error(f"Error processing calibrated response: {str(e)}")
            raise

    def generate_customized_by_topic(
        self,
        subject: str,
        topic_focus: List[str],
        bloom_level: str,
        num_questions: int = 5,
        question_type: str = "Mixed",
    ) -> List[Dict[str, Any]]:
        """
        Generate customized questions focused on specific topics at a given Bloom's level.

        Args:
            subject: Subject area
            topic_focus: Specific topics to focus on
            bloom_level: Bloom's taxonomy level
            num_questions: Number of questions to generate
            question_type: Type of questions

        Returns:
            List[Dict[str, Any]]: Generated questions calibrated to Bloom's level
        """
        context_str = ", ".join(topic_focus)

        logger.info(
            f"Topic-focused calibration: Generating {num_questions} {question_type} questions "
            f"for {subject} at Bloom's level {bloom_level} focusing on: {context_str}"
        )

        return self.generate_customized_questions(
            subject=subject,
            question_type=question_type,
            bloom_level=bloom_level,
            num_questions=num_questions,
            topic_focus=topic_focus,
            additional_context=f"These questions MUST focus specifically on the following topics: {context_str}. Each question should test {bloom_level} level understanding of these topics.",
        )

    def calibrate_difficulty_to_bloom(
        self, 
        traditional_difficulty: str
    ) -> str:
        """
        Convert traditional difficulty levels to Bloom's taxonomy levels.
        Utility method for backward compatibility.

        Args:
            traditional_difficulty: Easy, Medium, Hard

        Returns:
            str: Corresponding Bloom's taxonomy level
        """
        mapping = {
            "Easy": "Remember",
            "Medium": "Apply",
            "Hard": "Analyze",
            "Very Hard": "Evaluate",
            "Expert": "Create"
        }
        return mapping.get(traditional_difficulty, "Understand")

    def get_bloom_level_details(self, bloom_level: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Bloom's level.
        
        Args:
            bloom_level: The Bloom's taxonomy level
            
        Returns:
            Dict with description, keywords, cognitive demand, etc.
        """
        return self.BLOOM_LEVELS.get(bloom_level, self.BLOOM_LEVELS["Understand"])


def get_customized_agent() -> CustomizedQuestionAgent:
    """
    Get or create a customized question generation agent instance.
    This is the main factory function for importing in endpoint code.

    Returns:
        CustomizedQuestionAgent: Agent instance for calibrated question generation

    Example:
        >>> from backend.app.agents.customized_question_module import get_customized_agent
        >>> agent = get_customized_agent()
        >>> questions = agent.generate_customized_questions(
        ...     subject="Deep Learning",
        ...     question_type="Long Answer",
        ...     bloom_level="Analyze",
        ...     num_questions=5,
        ...     topic_focus=["Transformers", "Attention Mechanism"]
        ... )
    """
    return CustomizedQuestionAgent()

CustomizedQuestionModule = CustomizedQuestionAgent

all = [
"CustomizedQuestionAgent",
"CustomizedQuestionModule",
"get_customized_agent",
]

