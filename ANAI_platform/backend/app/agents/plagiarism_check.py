"""
Plagiarism check agent for question uniqueness detection.

This module implements similarity scoring and plagiarism detection
for generated questions to ensure uniqueness.
"""

import json
from typing import List, Dict, Any
from backend.app.llm_client import get_llm_client
from backend.app.prompts import PLAGIARISM_CHECK_PROMPT
from backend.app.utils import get_logger, parse_llm_response


logger = get_logger(__name__)


class PlagiarismCheckAgent:
    """
    Agent for detecting plagiarism and uniqueness in questions.
    
    This agent uses similarity analysis to compare new questions against
    a reference database to ensure originality and uniqueness.
    """

    def __init__(self):
        """Initialize the plagiarism check agent."""
        self.llm_client = get_llm_client()
        logger.info("PlagiarismCheckAgent initialized")

    def check_plagiarism(
        self,
        current_question: Dict[str, Any],
        reference_questions: List[Dict[str, Any]],
        plagiarism_threshold: float = 0.70,
    ) -> Dict[str, Any]:
        """
        Check if a question is plagiarized against reference questions.

        Args:
            current_question: The question to check
            reference_questions: List of reference questions to compare against
            plagiarism_threshold: Threshold for flagging as plagiarized (0-1)

        Returns:
            Dict with plagiarism analysis results

        Raises:
            Exception: If plagiarism check fails
        """
        logger.info(
            f"Checking plagiarism for: {current_question.get('text', '')[:50]}... "
            f"against {len(reference_questions)} reference questions"
        )

        try:
            # Build analysis prompt
            analysis_prompt = self._build_plagiarism_analysis_prompt(
                current_question=current_question,
                reference_questions=reference_questions,
                plagiarism_threshold=plagiarism_threshold,
            )

            logger.debug(f"Plagiarism analysis prompt: {analysis_prompt[:200]}...")

            # Get analysis from LLM
            response = self.llm_client.generate_json_message(analysis_prompt)

            logger.debug(f"Raw plagiarism response: {response[:200]}...")

            # Parse response
            analysis_result = parse_llm_response(response)

            logger.info(
                f"Plagiarism check completed - "
                f"Uniqueness Score: {analysis_result.get('uniqueness_score', 0):.2f}, "
                f"Is Plagiarized: {analysis_result.get('is_plagiarized', False)}"
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Error checking plagiarism: {str(e)}")
            raise

    def _build_plagiarism_analysis_prompt(
        self,
        current_question: Dict[str, Any],
        reference_questions: List[Dict[str, Any]],
        plagiarism_threshold: float,
    ) -> str:
        """
        Build the prompt for plagiarism analysis.

        Args:
            current_question: Question to analyze
            reference_questions: Reference questions
            plagiarism_threshold: Threshold for plagiarism

        Returns:
            str: Formatted prompt for LLM
        """
        analysis_request = {
            "current_question": current_question,
            "reference_questions": reference_questions,
            "plagiarism_threshold": plagiarism_threshold,
        }

        prompt = f"""{PLAGIARISM_CHECK_PROMPT}

CURRENT REQUEST:
{json.dumps(analysis_request, indent=2)}

Perform a detailed similarity analysis and provide results in the specified JSON format.
Ensure uniqueness_score + plagiarism_score = 1.0.
"""
        return prompt

    def batch_check_plagiarism(
        self,
        questions: List[Dict[str, Any]],
        reference_questions: List[Dict[str, Any]],
        plagiarism_threshold: float = 0.70,
    ) -> List[Dict[str, Any]]:
        """
        Check plagiarism for multiple questions.

        Args:
            questions: List of questions to check
            reference_questions: List of reference questions
            plagiarism_threshold: Threshold for flagging as plagiarized

        Returns:
            List of plagiarism analysis results for each question

        Raises:
            Exception: If batch check fails
        """
        logger.info(f"Batch plagiarism check for {len(questions)} questions")

        results = []
        for idx, question in enumerate(questions):
            try:
                logger.debug(f"Checking question {idx + 1}/{len(questions)}")
                result = self.check_plagiarism(
                    current_question=question,
                    reference_questions=reference_questions,
                    plagiarism_threshold=plagiarism_threshold,
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to check question {idx + 1}: {str(e)}")
                results.append({
                    "error": str(e),
                    "question_text": question.get("text", ""),
                    "is_plagiarized": False,
                })

        logger.info(
            f"Batch plagiarism check completed - "
            f"Checked: {len(results)}, Flagged as plagiarized: "
            f"{sum(1 for r in results if r.get('is_plagiarized', False))}"
        )

        return results

    def calculate_similarity_score(
        self,
        question1: str,
        question2: str,
    ) -> float:
        """
        Calculate similarity score between two questions (simple version).

        Args:
            question1: First question text
            question2: Second question text

        Returns:
            float: Similarity score (0-1)
        """
        logger.debug(f"Calculating similarity between two questions")

        try:
            # Simple word overlap similarity
            words1 = set(question1.lower().split())
            words2 = set(question2.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = len(words1 & words2)
            union = len(words1 | words2)

            similarity = intersection / union if union > 0 else 0.0

            logger.debug(f"Word overlap similarity: {similarity:.2f}")
            return similarity

        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
