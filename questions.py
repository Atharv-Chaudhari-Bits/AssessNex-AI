"""
Questions endpoints router.

Handles all question generation and retrieval endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from typing import Optional, List, Dict, Any
import json
from backend.app.schemas import (
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    SubjectListResponse,
    Question,
    ErrorResponse,
    CustomizedQuestionRequest,
    BloomLevel,
)
from backend.app.config import get_settings
from backend.app.agents import (
    get_agent,
    get_customized_agent,
    BLOOM_TAXONOMY_LEVELS,
)
from backend.app.utils import (
    get_logger,
    validate_subject,
    validate_question_type,
    validate_difficulty_level,
    validate_bloom_level,
    get_current_timestamp,
    parse_document_bytes,
    extract_key_sections,
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
            "bloom_levels": BLOOM_TAXONOMY_LEVELS,
            "default_questions": settings.DEFAULT_QUESTIONS_COUNT,
            "max_questions": settings.MAX_QUESTIONS_COUNT,
        }
    except Exception as e:
        logger.error(f"Error fetching question info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch question info")


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
    """
    try:
        logger.info(
            f"Question generation request: subject={request.subject}, "
            f"type={request.question_type}, difficulty={request.difficulty_level}, "
            f"count={request.num_questions}"
        )

        # Validate inputs
        if not validate_subject(request.subject.value if hasattr(request.subject, 'value') else str(request.subject)):
            raise HTTPException(status_code=400, detail=f"Invalid subject: {request.subject}")

        if not validate_question_type(request.question_type.value if hasattr(request.question_type, 'value') else str(request.question_type)):
            raise HTTPException(status_code=400, detail=f"Invalid question type: {request.question_type}")

        if not validate_difficulty_level(request.difficulty_level.value if hasattr(request.difficulty_level, 'value') else str(request.difficulty_level)):
            raise HTTPException(status_code=400, detail=f"Invalid difficulty level: {request.difficulty_level}")

        # Get agent and generate questions
        agent = get_agent()
        questions_data = agent.generate_questions(
            subject=request.subject.value if hasattr(request.subject, 'value') else str(request.subject),
            question_type=request.question_type.value if hasattr(request.question_type, 'value') else str(request.question_type),
            difficulty_level=request.difficulty_level.value if hasattr(request.difficulty_level, 'value') else str(request.difficulty_level),
            num_questions=request.num_questions,
            additional_context=request.additional_context or "",
            diagram_format=request.diagram_format,
        )

        # Convert to Question objects
        questions = [Question(**q) for q in questions_data]

        logger.info(f"Successfully generated {len(questions)} questions")
        return QuestionGenerationResponse(
            status="success",
            message=f"Generated {len(questions)} questions successfully",
            data=questions,
            metadata={
                "subject": request.subject.value if hasattr(request.subject, 'value') else str(request.subject),
                "question_type": request.question_type.value if hasattr(request.question_type, 'value') else str(request.question_type),
                "difficulty_level": request.difficulty_level.value if hasattr(request.difficulty_level, 'value') else str(request.difficulty_level),
                "num_questions": len(questions),
                "timestamp": get_current_timestamp(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


# ========================================================================
# BLOOM'S TAXONOMY CUSTOMIZED QUESTION ENDPOINTS
# ========================================================================

@router.post(
    "/customized",
    response_model=QuestionGenerationResponse,
    summary="Generate Customized Question with Bloom's Taxonomy",
    description="Generate question calibrated to specific Bloom's taxonomy level with optional document context"
)
async def generate_customized_question(
    request: CustomizedQuestionRequest,  # Use request body instead of query params
) -> QuestionGenerationResponse:
    """
    Generate a customized question calibrated to a specific Bloom's taxonomy level.
    
    This endpoint supports document context and chat-based customization.
    Uses the CustomizedQuestionRequest schema for validation.
    
    Args:
        request: Customized question request with topic, bloom_level, etc.
    
    Returns:
        QuestionGenerationResponse: Generated question with Bloom's calibration
    """
    try:
        # Extract values from request
        topic = request.topic
        bloom_level = request.bloom_level.value if hasattr(request.bloom_level, 'value') else str(request.bloom_level)
        question_type = request.question_type.value if hasattr(request.question_type, 'value') else str(request.question_type)
        chat_context = request.chat_context or ""
        topic_focus = request.topic_focus or ""
        document_text = request.document_text
        additional_context = request.additional_context
        require_bloom_justification = request.require_bloom_justification

        logger.info(f"Customized question request: topic={topic}, bloom_level={bloom_level}, type={question_type}")

        # Validate inputs
        if not validate_subject(topic):
            raise HTTPException(status_code=400, detail=f"Invalid topic: {topic}")
        
        if not validate_question_type(question_type):
            raise HTTPException(status_code=400, detail=f"Invalid question type: {question_type}")
        
        if not validate_bloom_level(bloom_level):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid Bloom's level: {bloom_level}. Must be one of: {', '.join(BLOOM_TAXONOMY_LEVELS)}"
            )
        
        # Parse topic focus
        topic_focus_list = [tf.strip() for tf in topic_focus.split(",")] if topic_focus else []
        
        # Combine all context sources
        full_context_parts = []
        
        if chat_context:
            full_context_parts.append(f"User Request: {chat_context}")
        
        if document_text:
            # Extract key sections from document if it's long
            if len(document_text) > 5000:
                document_text = extract_key_sections(document_text, max_length=5000)
            full_context_parts.append(f"Document Context:\n{document_text}")
        
        if additional_context:
            full_context_parts.append(f"Additional Context: {additional_context}")
        
        if topic_focus_list:
            full_context_parts.append(f"Focus Topics: {', '.join(topic_focus_list)}")
        
        enhanced_context = "\n\n".join(full_context_parts) if full_context_parts else ""
        
        # Add Bloom's calibration instructions
        enhanced_context += f"""
        
CALIBRATION INSTRUCTION:
- Bloom's Taxonomy Level: {bloom_level} - This is the EXACT cognitive level required
- Use action verbs appropriate for {bloom_level} level
- Do NOT generate questions at lower levels (Remember/Understand) or higher levels (Evaluate/Create)
- Each question must clearly demonstrate {bloom_level} level thinking
"""
        
        if require_bloom_justification:
            enhanced_context += f"- In the explanation, explicitly justify why this question targets the {bloom_level} level\n"
        
        # Get the customized agent
        agent = get_customized_agent()
        
        # Generate calibrated question
        questions = agent.generate_customized_questions(
            subject=topic,
            question_type=question_type,
            bloom_level=bloom_level,
            num_questions=1,
            additional_context=enhanced_context,
            topic_focus=topic_focus_list if topic_focus_list else None,
            require_bloom_justification=require_bloom_justification
        )
        
        if not questions:
            raise HTTPException(status_code=500, detail="Failed to generate customized question")
        
        # Format response
        question_data = questions[0]
        
        # Prepare metadata
        metadata = {
            "calibration_type": "bloom_taxonomy",
            "bloom_level": bloom_level,
            "cognitive_demand": question_data.get("cognitive_demand", ""),
            "has_bloom_justification": question_data.get("has_bloom_justification", False),
            "generation_method": "customized_bloom_calibration",
            "chat_context_used": bool(chat_context),
            "document_context_used": bool(document_text),
            "topic_focus_applied": bool(topic_focus_list),
            "additional_context_used": bool(additional_context)
        }
        
        # Include all selected levels if available
        if "all_levels" in question_data:
            metadata["included_levels"] = question_data["all_levels"]
        
        # Create Question object
        question = Question(
            id=question_data.get("question_id", f"q_{get_current_timestamp()}"),
            subject=question_data.get("subject", topic),
            question_type=question_data.get("question_type", question_type),
            difficulty_level=question_data.get("difficulty_level"),
            bloom_level=question_data.get("bloom_level", bloom_level),
            question_text=question_data.get("question_text", ""),
            options=question_data.get("options"),
            expected_answer=question_data.get("expected_answer", ""),
            explanation=question_data.get("explanation", ""),
            tags=question_data.get("tags", []),
            metadata=metadata
        )
        
        response = QuestionGenerationResponse(
            status="success",
            message=f"Generated {bloom_level} level question successfully",
            data=[question],
            metadata=metadata
        )
        
        logger.info(f"Customized question generated for topic: {topic} at Bloom's level: {bloom_level}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating customized question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate customized question: {str(e)}")


@router.post(
    "/customized/with-document",
    response_model=QuestionGenerationResponse,
    summary="Generate Customized Question with Document Upload",
    description="Upload a document and generate a Bloom's taxonomy calibrated question from its content"
)
async def generate_customized_question_with_document(
    topic: str = Query(..., description="Topic for question generation"),
    bloom_level: BloomLevel = Query(..., description="Bloom's taxonomy level"),
    question_type: str = Query("Multiple Choice", description="Type of question"),
    chat_context: str = Query("", description="User's chat message"),
    topic_focus: str = Query("", description="Comma-separated subtopics"),
    additional_context: Optional[str] = Query(None, description="Additional context"),
    require_bloom_justification: bool = Query(True, description="Whether to include justification"),
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, TXT)")
):
    """
    Generate a customized question with document upload.
    First parses the document using the documents endpoints, then generates question with extracted context.
    """
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        logger.info(f"Processing document upload: {file.filename}, type: {file.content_type}")
        
        # Parse the uploaded document locally. Calling our own HTTP API here added
        # unnecessary latency and depended on a non-existent API_BASE_URL setting.
        file_bytes = await file.read()
        filename = (file.filename or "").lower()
        content_type = file.content_type or ""
        if filename.endswith(".pdf") or content_type == "application/pdf":
            file_type = "application/pdf"
        elif filename.endswith(".docx") or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.endswith((".txt", ".md", ".csv")) or content_type in {"text/plain", "text/markdown", "text/csv"}:
            file_type = "text/plain" if content_type not in {"text/markdown", "text/csv"} else content_type
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, TXT, Markdown, or CSV.")

        try:
            document_text = parse_document_bytes(file_bytes, file_type)
        except Exception as exc:
            logger.error("Document parsing failed: %s", exc)
            raise HTTPException(status_code=400, detail=f"Failed to parse document: {exc}") from exc

        if not document_text:
            raise HTTPException(status_code=400, detail="No text could be extracted from document")
        
        # Create request object
        request = CustomizedQuestionRequest(
            topic=topic,
            bloom_level=bloom_level,
            question_type=question_type,
            chat_context=chat_context,
            topic_focus=topic_focus,
            document_text=document_text,
            additional_context=additional_context,
            require_bloom_justification=require_bloom_justification
        )
        
        # Call the main customized endpoint
        return await generate_customized_question(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document-based question generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/customized/batch",
    response_model=List[QuestionGenerationResponse],
    summary="Generate Multiple Customized Questions",
    description="Generate multiple questions with specified Bloom's taxonomy levels"
)
async def generate_customized_questions_batch(
    requests: List[CustomizedQuestionRequest]
) -> List[QuestionGenerationResponse]:
    """
    Generate multiple customized questions in batch.
    
    Each request should be a valid CustomizedQuestionRequest object.
    
    Args:
        requests: List of CustomizedQuestionRequest objects
        
    Returns:
        List[QuestionGenerationResponse]: Generated questions
    """
    responses = []
    errors = []
    
    for idx, req in enumerate(requests):
        try:
            logger.info(f"Processing batch request {idx + 1}/{len(requests)}")
            response = await generate_customized_question(req)
            responses.append(response)
        except Exception as e:
            error_msg = f"Request {idx + 1} failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            # Continue with other requests
    
    if errors and not responses:
        raise HTTPException(status_code=500, detail="All batch requests failed")
    
    return responses


@router.post(
    "/customized/legacy",
    response_model=QuestionGenerationResponse,
    summary="Generate Customized Question (Legacy)",
    description="Legacy endpoint with traditional difficulty levels - maps to Bloom's taxonomy"
)
async def generate_customized_question_legacy(
    topic: str = Query(..., description="Topic for question generation"),
    difficulty: str = Query("Medium", description="Difficulty level (Easy, Medium, Hard)"),
    chat_context: str = Query("", description="Chat context or user input for customization"),
    question_type: str = Query("Multiple Choice", description="Type of question")
) -> QuestionGenerationResponse:
    """
    Legacy endpoint that maps traditional difficulty levels to Bloom's taxonomy.
    """
    # Map traditional difficulty to Bloom's level
    difficulty_to_bloom = {
        "Easy": "Remember",
        "Medium": "Apply",
        "Hard": "Analyze"
    }
    
    bloom_level = difficulty_to_bloom.get(difficulty, "Understand")
    
    # Create request object
    request = CustomizedQuestionRequest(
        topic=topic,
        bloom_level=bloom_level,
        question_type=question_type,
        chat_context=chat_context,
        topic_focus="",
        require_bloom_justification=True
    )
    
    # Call the main endpoint with mapped Bloom's level
    return await generate_customized_question(request)


@router.get(
    "/customized/bloom-levels",
    response_model=Dict[str, Any],
    summary="Get Bloom's Taxonomy Levels",
    description="Get available Bloom's taxonomy levels with descriptions"
)
async def get_bloom_levels_with_descriptions():
    """
    Get Bloom's taxonomy levels with descriptions and action verbs.
    """
    try:
        agent = get_customized_agent()
        levels = {}
        
        for level in BLOOM_TAXONOMY_LEVELS:
            levels[level] = agent.BLOOM_LEVELS.get(level, {
                "description": "No description available",
                "keywords": [],
                "cognitive_demand": "Unknown",
                "question_style": "Unknown"
            })
        
        return {
            "levels": BLOOM_TAXONOMY_LEVELS,
            "details": levels
        }
        
    except Exception as e:
        logger.error(f"Error fetching Bloom levels: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch Bloom's taxonomy levels")