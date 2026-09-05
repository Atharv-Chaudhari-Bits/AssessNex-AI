"""
Plagiarism check router for API endpoints.

Provides endpoints for checking question plagiarism and uniqueness.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.agents.plagiarism_check import PlagiarismCheckAgent
from backend.app.schemas import (
    PlagiarismCheckRequest,
    PlagiarismCheckResponse,
    BatchPlagiarismCheckRequest,
    BatchPlagiarismCheckResponse,
)
from backend.app.utils import get_logger
from backend.app.config import get_settings


logger = get_logger(__name__)
router = APIRouter(prefix="/plagiarism", tags=["plagiarism"])

# Initialize agent
plagiarism_agent = None


def get_plagiarism_agent() -> PlagiarismCheckAgent:
    """Get or create plagiarism check agent (singleton)."""
    global plagiarism_agent
    if plagiarism_agent is None:
        plagiarism_agent = PlagiarismCheckAgent()
    return plagiarism_agent


@router.post(
    "/check",
    response_model=PlagiarismCheckResponse,
    summary="Check Question Plagiarism",
    description="Check if a question is plagiarized against reference questions"
)
async def check_plagiarism(
    request: PlagiarismCheckRequest,
) -> PlagiarismCheckResponse:
    """
    Check if a question is plagiarized.

    Args:
        request: Plagiarism check request with question and references

    Returns:
        PlagiarismCheckResponse: Analysis results with similarity scores

    Raises:
        HTTPException: If plagiarism check fails

    Example:
        POST /api/v1/plagiarism/check
        {
            "current_question": {
                "text": "What is supervised learning?",
                "type": "Short Answer",
                "subject": "Machine Learning"
            },
            "reference_questions": [...]
        }
    """
    try:
        if not get_settings().ENABLE_PLAGIARISM_CHECK:
            raise HTTPException(status_code=503, detail="Plagiarism checking is disabled")

        logger.info(
            f"Plagiarism check request for question: "
            f"{request.current_question.get('text', '')[:50]}..."
        )

        # Get agent
        agent = get_plagiarism_agent()

        # Perform plagiarism check
        result = agent.check_plagiarism(
            current_question=request.current_question,
            reference_questions=request.reference_questions,
            plagiarism_threshold=request.plagiarism_threshold,
        )

        logger.info(
            f"Plagiarism check completed - "
            f"Uniqueness: {result.get('uniqueness_score', 0):.2f}"
        )

        # Convert result to response model
        return PlagiarismCheckResponse(**result)

    except Exception as e:
        logger.error(f"Error checking plagiarism: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check plagiarism: {str(e)}"
        )


@router.post(
    "/batch-check",
    response_model=BatchPlagiarismCheckResponse,
    summary="Batch Check Plagiarism",
    description="Check plagiarism for multiple questions at once"
)
async def batch_check_plagiarism(
    request: BatchPlagiarismCheckRequest,
) -> BatchPlagiarismCheckResponse:
    """
    Check plagiarism for multiple questions.

    Args:
        request: Batch plagiarism check request

    Returns:
        BatchPlagiarismCheckResponse: Results for all questions

    Raises:
        HTTPException: If batch check fails

    Example:
        POST /api/v1/plagiarism/batch-check
        {
            "questions": [...],
            "reference_questions": [...],
            "plagiarism_threshold": 0.70
        }
    """
    try:
        if not get_settings().ENABLE_PLAGIARISM_CHECK:
            raise HTTPException(status_code=503, detail="Plagiarism checking is disabled")

        logger.info(
            f"Batch plagiarism check for {len(request.questions)} questions"
        )

        # Get agent
        agent = get_plagiarism_agent()

        # Perform batch check
        results = agent.batch_check_plagiarism(
            questions=request.questions,
            reference_questions=request.reference_questions,
            plagiarism_threshold=request.plagiarism_threshold,
        )

        # Calculate summary
        flagged_count = sum(
            1 for r in results if r.get("is_plagiarized", False)
        )
        avg_uniqueness = sum(
            r.get("uniqueness_score", 0) for r in results
        ) / len(results) if results else 0

        summary = {
            "total_checked": len(results),
            "flagged_as_plagiarized": flagged_count,
            "average_uniqueness": avg_uniqueness,
            "acceptance_rate": (len(results) - flagged_count) / len(results)
            if results else 0,
        }

        logger.info(
            f"Batch check completed - "
            f"Total: {len(results)}, Flagged: {flagged_count}, "
            f"Avg Uniqueness: {avg_uniqueness:.2f}"
        )

        # Convert results to response models
        response_results = [
            PlagiarismCheckResponse(**r) if "error" not in r
            else PlagiarismCheckResponse(
                uniqueness_score=0.0,
                plagiarism_score=1.0,
                is_plagiarized=True,
                plagiarism_threshold_exceeded=True,
                recommendations=[f"Error: {r['error']}"],
            )
            for r in results
        ]

        return BatchPlagiarismCheckResponse(
            status="success",
            message=f"Batch plagiarism check completed for {len(results)} questions",
            results=response_results,
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Error in batch plagiarism check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform batch plagiarism check: {str(e)}"
        )


@router.post(
    "/similarity-score",
    summary="Calculate Similarity Score",
    description="Calculate basic similarity score between two questions"
)
async def calculate_similarity(
    question1: str,
    question2: str,
) -> Dict[str, Any]:
    """
    Calculate simple similarity score between two questions.

    Args:
        question1: First question text
        question2: Second question text

    Returns:
        Dict with similarity score and analysis

    Example:
        POST /api/v1/plagiarism/similarity-score
        {
            "question1": "What is machine learning?",
            "question2": "Define machine learning"
        }
    """
    try:
        if not get_settings().ENABLE_PLAGIARISM_CHECK:
            raise HTTPException(status_code=503, detail="Plagiarism checking is disabled")

        logger.debug("Calculating similarity score for two questions")

        # Get agent
        agent = get_plagiarism_agent()

        # Calculate similarity
        score = agent.calculate_similarity_score(question1, question2)

        logger.info(f"Similarity calculated: {score:.2f}")

        return {
            "similarity_score": score,
            "are_similar": score > 0.5,
            "question1_preview": question1[:100],
            "question2_preview": question2[:100],
        }

    except Exception as e:
        logger.error(f"Error calculating similarity: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate similarity: {str(e)}"
        )
