"""
Agent module for question generation.

This module implements the agentic AI logic for generating MTech level
questions using Google Gemini and structured prompting.
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
    attach_rendered_visual,
)


logger = get_logger(__name__)


class QuestionGenerationAgent:
    """
    Agent for generating MTech level questions.

    This agent uses Google Gemini to generate high-quality, structured
    questions for various AI/ML subjects.
    """

    SYSTEM_PROMPT = """You are an expert MTech level question generator for AI/ML subjects.
Your task is to generate high-quality, academic-level questions that test deep understanding
and critical thinking. Always respond with valid JSON format containing question details.

Important Guidelines:
1. Generate questions appropriate for MTech level students
2. Ensure questions are technically accurate and well-structured
3. Provide clear, concise questions without ambiguity
4. Include detailed explanations for answers
5. For multiple choice questions, ensure options are plausible but clearly different
6. Questions should test concepts, applications, and analytical thinking
7. Maintain consistency in formatting and structure"""

    def __init__(self):
        """Initialize the question generation agent."""
        self.llm_client = get_llm_client()
        self.prompt_builder = PromptBuilder()
        logger.info("QuestionGenerationAgent initialized with PromptBuilder")

    def _build_generation_prompt(
        self,
        subject: str,
        question_type: str,
        difficulty_level: str,
        num_questions: int,
        additional_context: str = "",
    ) -> str:
        """
        Build the prompt for question generation using PromptBuilder.

        Args:
            subject: Subject area
            question_type: Type of questions
            difficulty_level: Difficulty level
            num_questions: Number of questions
            additional_context: Additional context

        Returns:
            str: Formatted prompt for LLM
        """
        # Use PromptBuilder to construct the prompt
        prompt = self.prompt_builder.build_question_generation_prompt(
            subject=subject,
            question_type=question_type,
            difficulty_level=difficulty_level,
            num_questions=num_questions,
            additional_context=additional_context,
            use_cot=True,
            use_few_shots=True,
        )

        logger.debug(f"Generated prompt for {num_questions} {question_type} questions on {subject}")
        return prompt

    def generate_questions(
        self,
        subject: str,
        question_type: str,
        difficulty_level: str,
        num_questions: int,
        additional_context: str = "",
        diagram_format: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using the LLM agent.

        The generation pipeline:
        1. Build optimized prompt with type-specific guidance
        2. Call LLM to generate JSON questions
        3. Parse and validate response
        4. Apply UNIFIED formatting based on question type
        5. Fix any LaTeX corruption

        Args:
            subject: Subject area for questions
            question_type: Type of questions
            difficulty_level: Difficulty level
            num_questions: Number of questions to generate
            additional_context: Additional context for generation
            diagram_format: Format for diagrams (Mermaid/ASCII) - only for Diagram-Based

        Returns:
            List[Dict[str, Any]]: List of generated questions

        Raises:
            Exception: If question generation fails
        """
        logger.info(
            f"Generating {num_questions} {question_type} questions "
            f"for {subject} at {difficulty_level} level"
        )

        # Add diagram format to context if specified
        if diagram_format and question_type in ["Diagram-Based", "Diagram"]:
            if "mermaid" in diagram_format.lower():
                additional_context += "\n\nIMPORTANT: Use Mermaid.js syntax for ALL diagrams. Wrap diagrams in ```mermaid code blocks."
            else:
                additional_context += "\n\nIMPORTANT: Use ASCII art with box drawing characters (┌ ─ ┐ │ └ ┘) for ALL diagrams. Do NOT use Mermaid.js."

        try:
            # Build prompt
            prompt = self._build_generation_prompt(
                subject=subject,
                question_type=question_type,
                difficulty_level=difficulty_level,
                num_questions=num_questions,
                additional_context=additional_context,
            )

            logger.debug(f"Prompt: {prompt[:200]}...")

            # Generate response from LLM
            response = self.llm_client.generate_json_message(prompt)

            logger.debug(f"Raw response: {response[:200]}...")
            logger.info(f"Generating {num_questions} questions with difficulty_level={difficulty_level}")

            # Parse response
            parsed_response = parse_llm_response(response)

            # Extract questions
            questions = self._process_response(
                parsed_response,
                subject,
                question_type,
                difficulty_level,
            )

            # SINGLE POST-PROCESSING: Apply unified formatting
            # This is the ONLY formatting step - ensures consistency
            from backend.app.utils import format_all_questions_with_flags, fix_question_latex
            
            # Apply type-based formatting (handles code blocks, LaTeX, diagrams, sanitization)
            questions = format_all_questions_with_flags(questions, question_type)
            
            # Fix any corrupted LaTeX backslashes (e.g., \text becoming extdepth)
            questions = [fix_question_latex(q) for q in questions]
            questions = [attach_rendered_visual(q) for q in questions]

            logger.info(f"Successfully generated and formatted {len(questions)} questions")
            return questions

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise

    def _process_response(
        self,
        response: Dict[str, Any],
        subject: str,
        question_type: str,
        difficulty_level: str,
    ) -> List[Dict[str, Any]]:
        """
        Process and structure the LLM response.

        Args:
            response: Raw response from LLM
            subject: Subject area
            question_type: Type of questions
            difficulty_level: Difficulty level

        Returns:
            List[Dict[str, Any]]: Processed questions

        Raises:
            ValueError: If response format is invalid
        """
        questions = []

        try:
            # Log incoming request details
            logger.info(f"Processing response with difficulty_level={difficulty_level}")
            
            # Handle different response formats
            if isinstance(response, dict):
                if "questions" in response:
                    raw_questions = response["questions"]
                elif isinstance(response, dict) and len(response) > 0:
                    # If response is a dict with question data
                    raw_questions = [response]
                else:
                    raw_questions = []
            elif isinstance(response, list):
                raw_questions = response
            else:
                logger.warning(f"Unexpected response type: {type(response)}")
                return []

            # Process each question
            for question_data in raw_questions:
                if not isinstance(question_data, dict):
                    logger.warning(f"Skipping invalid question data: {question_data}")
                    continue

                try:
                    # Get fields with defensive type checking
                    question_text = question_data.get("question_text") or question_data.get("question") or ""
                    if not isinstance(question_text, str):
                        question_text = str(question_text)
                    
                    options = question_data.get("options")
                    if options is not None and not isinstance(options, list):
                        if isinstance(options, bool):
                            options = None
                        else:
                            options = None
                    
                    expected_answer = question_data.get("expected_answer", "")
                    if not isinstance(expected_answer, str):
                        expected_answer = str(expected_answer) if expected_answer else ""
                    
                    explanation = question_data.get("explanation", "")
                    if not isinstance(explanation, str):
                        explanation = str(explanation) if explanation else ""
                    
                    tags = question_data.get("tags", [])
                    if not isinstance(tags, list):
                        tags = []
                    
                    processed_question = format_question_response(
                        question_id=generate_question_id(),
                        subject=subject,
                        question_type=question_type,
                        difficulty_level=difficulty_level,
                        question_text=question_text,
                        options=options,
                        expected_answer=expected_answer,
                        explanation=explanation,
                        tags=tags,
                    )
                    
                    # Preserve structured metadata emitted by Gemini.
                    if isinstance(question_data.get("content_flags"), dict):
                        processed_question["content_flags"] = question_data["content_flags"]
                    if isinstance(question_data.get("visual"), dict):
                        processed_question["visual"] = question_data["visual"]

                    logger.debug(f"Processed question with difficulty={processed_question.get('difficulty_level')}")
                    questions.append(processed_question)

                except Exception as e:
                    logger.warning(f"Error processing question: {str(e)}")
                    continue

            logger.info(f"Processed {len(questions)} questions from response")
            return questions

        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            raise

    def generate_with_context(
        self,
        subject: str,
        context_topics: List[str],
        num_questions: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions with specific topics/concepts focus.

        Args:
            subject: Subject area
            context_topics: Specific topics to focus on
            num_questions: Number of questions

        Returns:
            List[Dict[str, Any]]: Generated questions

        Raises:
            Exception: If generation fails
        """
        context_str = ", ".join(context_topics)

        logger.info(
            f"Generating {num_questions} questions for {subject} "
            f"focusing on: {context_str}"
        )

        return self.generate_questions(
            subject=subject,
            question_type="Long Answer",
            difficulty_level="Hard",
            num_questions=num_questions,
            additional_context=f"Focus on these topics: {context_str}",
        )


def get_agent() -> QuestionGenerationAgent:
    """
    Get or create a question generation agent instance.

    Returns:
        QuestionGenerationAgent: Agent instance

    Example:
        >>> from backend.app.agents.question_generator import get_agent
        >>> agent = get_agent()
        >>> questions = agent.generate_questions(...)
    """
    return QuestionGenerationAgent()
