"""
Questions endpoints router.

Handles all question generation and retrieval endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json
from backend.app.schemas import (
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    SubjectListResponse,
    Question,
    ErrorResponse,
)
from backend.app.config import get_settings
from backend.app.agents import get_agent
from backend.app.utils import (
    get_logger,
    validate_subject,
    validate_question_type,
    validate_difficulty_level,
    get_current_timestamp,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/questions", tags=["questions"])


@router.get(
    "/subjects",
    response_model=SubjectListResponse,
    summary="Get Available Subjects",
    description="Retrieve list of available subjects for question generation"
)
async def get_subjects() -> SubjectListResponse:
    """
    Get list of available subjects.

    Returns:
        SubjectListResponse: List of available subjects

    Example:
        GET /api/v1/questions/subjects
    """
    try:
        settings = get_settings()

        logger.info("Fetching available subjects")

        return SubjectListResponse(subjects=settings.SUBJECTS)

    except Exception as e:
        logger.error(f"Error fetching subjects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subjects")


@router.post(
    "/generate",
    response_model=QuestionGenerationResponse,
    summary="Generate Questions",
    description="Generate AI/ML questions based on specified criteria"
)
async def generate_questions(
    request: QuestionGenerationRequest,
) -> QuestionGenerationResponse:
    """
    Generate questions based on request parameters.

    Args:
        request: Question generation request with subject, type, difficulty, etc.

    Returns:
        QuestionGenerationResponse: Generated questions with metadata

    Raises:
        HTTPException: If validation or generation fails

    Example:
        POST /api/v1/questions/generate
        {
            "subject": "Machine Learning",
            "question_type": "Multiple Choice",
            "difficulty_level": "Hard",
            "num_questions": 5
        }
    """
    try:
        logger.info(
            f"Question generation request: subject={request.subject}, "
            f"type={request.question_type}, difficulty={request.difficulty_level}, "
            f"count={request.num_questions}"
        )

        # Validate inputs
        if not validate_subject(request.subject):
            logger.warning(f"Invalid subject: {request.subject}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid subject: {request.subject}"
            )

        if not validate_question_type(request.question_type):
            logger.warning(f"Invalid question type: {request.question_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid question type: {request.question_type}"
            )

        if not validate_difficulty_level(request.difficulty_level):
            logger.warning(f"Invalid difficulty level: {request.difficulty_level}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid difficulty level: {request.difficulty_level}"
            )

        # Get agent and generate questions
        agent = get_agent()

        questions_data = agent.generate_questions(
            subject=request.subject,
            question_type=request.question_type,
            difficulty_level=request.difficulty_level,
            num_questions=request.num_questions,
            additional_context=request.additional_context or "",
            diagram_format=request.diagram_format,
        )

        # Log raw questions data before conversion
        logger.info(f"Raw questions data from agent: {len(questions_data)} questions")
        for idx, q_data in enumerate(questions_data):
            logger.info(f"\n[Question {idx + 1}] ======================")
            logger.info(f"  Type: {type(q_data)}")
            logger.info(f"  Keys: {q_data.keys() if isinstance(q_data, dict) else 'N/A'}")
            if isinstance(q_data, dict):
                logger.info(f"  Question: {q_data.get('question_text', 'N/A')[:100]}...")
                logger.info(f"  Options: {q_data.get('options')}")
                logger.info(f"  Options Type: {type(q_data.get('options'))}")
                logger.info(f"  Answer: {q_data.get('expected_answer', 'N/A')}")
                logger.info(f"  Explanation: {q_data.get('explanation', 'N/A')[:100]}...")
                logger.info(f"  Tags: {q_data.get('tags')}")
                logger.info(f"  Full data: {json.dumps(q_data, indent=2)}")

        # Convert to Question objects
        questions = [Question(**q) for q in questions_data]

        logger.info(f"Successfully generated {len(questions)} questions")
        for idx, q in enumerate(questions):
            logger.info(f"\n[Converted Question {idx + 1}] ======================")
            logger.info(f"  Question: {q.question_text[:100]}...")
            logger.info(f"  Options: {q.options}")
            logger.info(f"  Answer: {q.expected_answer}")

        return QuestionGenerationResponse(
            status="success",
            message=f"Generated {len(questions)} questions successfully",
            data=questions,
            metadata={
                "subject": request.subject,
                "question_type": request.question_type,
                "difficulty_level": request.difficulty_level,
                "num_questions": len(questions),
                "timestamp": get_current_timestamp(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.get(
    "/info",
    response_model=dict,
    summary="Get Question Generation Info",
    description="Get information about question types and difficulty levels"
)
async def get_question_info() -> dict:
    """
    Get information about available question types and difficulty levels.

    Returns:
        dict: Question generation configuration information

    Example:
        GET /api/v1/questions/info
    """
    try:
        settings = get_settings()

        logger.info("Fetching question generation info")

        return {
            "question_types": settings.QUESTION_TYPES,
            "difficulty_levels": settings.DIFFICULTY_LEVELS,
            "default_questions": settings.DEFAULT_QUESTIONS_COUNT,
            "max_questions": settings.MAX_QUESTIONS_COUNT,
        }

    except Exception as e:
        logger.error(f"Error fetching question info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch question info"
        )


@router.post(
    "/customized",
    response_model=QuestionGenerationResponse,
    summary="Generate Customized Question with Chat",
    description="Generate question based on topic, difficulty, Bloom's taxonomy levels, and chat context"
)
async def generate_customized_question(
    topic: str = Query(..., description="Topic for question generation"),
    difficulty: str = Query(..., description="Difficulty level"),
    bloom_levels: str = Query("Remember,Understand,Apply", description="Comma-separated Bloom's taxonomy levels"),
    chat_context: str = Query("", description="Chat context or user input for customization"),
    question_type: str = Query("Multiple Choice", description="Type of question")
) -> QuestionGenerationResponse:
    """
    Generate a customized question based on chat interaction.
    
    Args:
        topic: Main topic for question
        difficulty: Difficulty level (Easy, Medium, Hard)
        bloom_levels: Comma-separated Bloom's taxonomy levels
        chat_context: User's chat message or context
        question_type: Type of question to generate
    
    Returns:
        QuestionGenerationResponse: Generated customized question
    
    Example:
        POST /api/v1/questions/customized?topic=Machine Learning&difficulty=Medium&bloom_levels=Understand,Apply&chat_context=Focus on algorithms
    """
    try:
        validate_subject(topic)
        validate_difficulty_level(difficulty)
        validate_question_type(question_type)
        
        # Construct context with Bloom's taxonomy and chat
        bloom_list = [b.strip() for b in bloom_levels.split(",") if b.strip()]
        full_context = f"Topic: {topic}. Bloom's Taxonomy Levels: {', '.join(bloom_list)}. User Request: {chat_context}"
        
        # Create question generation request
        request = QuestionGenerationRequest(
            subject=topic,
            question_type=question_type,
            difficulty=difficulty,
            count=1,
            additional_context=full_context
        )
        
        # Generate question using agent
        agent = get_agent()
        response = await agent.generate_questions(request)
        
        logger.info(f"Customized question generated for topic: {topic}")
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error generating customized question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate customized question"
        )
