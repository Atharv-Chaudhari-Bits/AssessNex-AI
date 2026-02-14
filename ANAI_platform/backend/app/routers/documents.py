"""
Document-based question generation router.

Handles document parsing and context-aware question generation.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Callable
import PyPDF2
import io
import json
from datetime import datetime

from backend.app.config import get_settings
from backend.app.agents import get_agent
from backend.app.utils import get_logger, validate_subject, validate_difficulty_level

from backend.app.prompts.prompt_manager import PromptBuilder
from backend.app.agents.assignment_agent import AssignmentGenerationAgent

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentQuestionRequest(BaseModel):
    """Request model for document-based question generation."""
    document_text: str
    question_prompt: str
    subject: str = "General"
    question_type: str = "Multiple Choice"
    difficulty_level: str = "Medium"
    num_questions: int = 5
    additional_context: Optional[str] = None


class DocumentParseResponse(BaseModel):
    """Response model for document parsing."""
    text: str
    word_count: int
    page_count: Optional[int] = None
    status: str = "success"


class SummarizeRequest(BaseModel):
    """Request model for document summarization."""
    document_text: str
    max_length: int = 500


class ConceptExtractRequest(BaseModel):
    """Request model for concept extraction."""
    document_text: str


@router.post(
    "/parse-pdf",
    response_model=DocumentParseResponse,
    summary="Parse PDF Document",
    description="Extract text from PDF file"
)
async def parse_pdf(file: UploadFile = File(...)) -> DocumentParseResponse:
    """
    Parse PDF file and extract text content.

    Args:
        file: PDF file to parse

    Returns:
        DocumentParseResponse: Extracted text and metadata

    Raises:
        HTTPException: If PDF parsing fails
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        logger.info(f"Parsing PDF: {file.filename}")

        # Read PDF content
        pdf_content = await file.read()
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract text from all pages
        extracted_text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                continue

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF")

        word_count = len(extracted_text.split())
        page_count = len(pdf_reader.pages)

        logger.info(
            f"Successfully parsed PDF: {page_count} pages, {word_count} words"
        )

        return DocumentParseResponse(
            text=extracted_text.strip(),
            word_count=word_count,
            page_count=page_count,
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


@router.post(
    "/parse-docx",
    response_model=DocumentParseResponse,
    summary="Parse DOCX Document",
    description="Extract text from DOCX file"
)
async def parse_docx(file: UploadFile = File(...)) -> DocumentParseResponse:
    """
    Parse DOCX file and extract text content.

    Args:
        file: DOCX file to parse

    Returns:
        DocumentParseResponse: Extracted text and metadata

    Raises:
        HTTPException: If DOCX parsing fails
    """
    try:
        if not file.filename.lower().endswith('.docx'):
            raise HTTPException(status_code=400, detail="File must be a DOCX")

        logger.info(f"Parsing DOCX: {file.filename}")

        from docx import Document

        docx_content = await file.read()
        docx_file = io.BytesIO(docx_content)
        doc = Document(docx_file)

        # Extract text from all paragraphs
        extracted_text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                extracted_text += paragraph.text + "\n"

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text found in DOCX")

        word_count = len(extracted_text.split())

        logger.info(f"Successfully parsed DOCX: {word_count} words")

        return DocumentParseResponse(
            text=extracted_text.strip(),
            word_count=word_count,
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DOCX parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse DOCX: {str(e)}")


@router.post(
    "/generate-questions",
    summary="Generate Questions from Document",
    description="Generate AI questions based on document context and user prompt"
)
async def generate_questions_from_document(request: DocumentQuestionRequest):
    """
    Generate questions from document content based on user request.

    This endpoint creates a context-aware question generation where the
    LLM uses the provided document as context to generate relevant questions.

    Args:
        request: Document question generation request with:
            - document_text: The document content to use as context
            - question_prompt: User's request for what questions to generate
            - subject: Subject area for questions
            - question_type: Type of questions (Multiple Choice, Essay, etc.)
            - difficulty_level: Difficulty level (Easy, Medium, Hard)
            - num_questions: Number of questions to generate
            - additional_context: Optional additional context

    Returns:
        dict: Generated questions with metadata

    Raises:
        HTTPException: If validation or generation fails

    Example:
        POST /api/v1/documents/generate-questions
        {
            "document_text": "Machine Learning is...",
            "question_prompt": "Generate questions about supervised learning",
            "subject": "Machine Learning",
            "question_type": "Multiple Choice",
            "difficulty_level": "Medium",
            "num_questions": 5
        }
    """
    try:
        # Validate inputs
        if not request.document_text.strip():
            raise HTTPException(status_code=400, detail="Document text cannot be empty")

        if not request.question_prompt.strip():
            raise HTTPException(status_code=400, detail="Question prompt cannot be empty")

        if not validate_difficulty_level(request.difficulty_level):
            raise HTTPException(status_code=400, detail="Invalid difficulty level")

        logger.info(
            f"Document question generation: subject={request.subject}, "
            f"prompt={request.question_prompt[:50]}..., "
            f"difficulty={request.difficulty_level}"
        )

        # Get the question generation agent
        agent = get_agent("question_generation")

        # Create context-aware prompt that includes document
        document_context = f"""
Use the following document as context for generating questions:

---DOCUMENT START---
{request.document_text[:2000]}  # Limit to first 2000 chars for token efficiency
---DOCUMENT END---

User Request: {request.question_prompt}
"""

        # Generate questions using the agent with document context
        response = agent.generate_questions(
            subject=request.subject,
            question_type=request.question_type,
            difficulty_level=request.difficulty_level,
            num_questions=request.num_questions,
            additional_context=document_context,
        )

        logger.info(f"Successfully generated {len(response)} questions from document")

        return {
            "status": "success",
            "data": response,
            "metadata": {
                "document_length": len(request.document_text),
                "subject": request.subject,
                "question_type": request.question_type,
                "difficulty_level": request.difficulty_level,
                "count": len(response),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document question generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate questions from document: {str(e)}"
        )


@router.post(
    "/summarize",
    summary="Summarize Document",
    description="Generate a concise summary of document content"
)
async def summarize_document(request: SummarizeRequest):
    """
    Generate a concise summary of the document content.

    Args:
        request: Contains document_text to summarize

    Returns:
        dict: Summary and metadata
    """
    try:
        document_text = request.document_text
        max_length = request.max_length

        if not document_text.strip():
            raise HTTPException(status_code=400, detail="Document text cannot be empty")

        logger.info(f"Summarizing document ({len(document_text)} chars)")

        # Use LLM to summarize
        from backend.app.llm_client import llm_client

        summary_response = await llm_client.create_completion(
            messages=[
                {
                    "role": "system",
                    "content": f"Provide a concise summary of the following document in maximum {max_length} words."
                },
                {
                    "role": "user",
                    "content": document_text
                }
            ],
            temperature=0.7,
            max_tokens=max_length,
        )

        # Extract summary from response
        if isinstance(summary_response, dict):
            summary = summary_response.get("content", summary_response.get("text", ""))
        elif hasattr(summary_response, 'content'):
            summary = summary_response.content
        else:
            summary = str(summary_response)

        return {
            "status": "success",
            "summary": summary,
            "metadata": {
                "original_length": len(document_text),
                "original_words": len(document_text.split()),
                "summary_words": len(summary.split())
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document summarization error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize document: {str(e)}"
        )


@router.post(
    "/extract-concepts",
    summary="Extract Key Concepts",
    description="Extract key concepts and topics from document"
)
async def extract_concepts(request: ConceptExtractRequest):
    """
    Extract key concepts, topics, and entities from document.

    Args:
        request: Contains document_text

    Returns:
        dict: Extracted concepts organized by category
    """
    try:
        document_text = request.document_text

        if not document_text.strip():
            raise HTTPException(status_code=400, detail="Document text cannot be empty")

        logger.info(f"Extracting concepts from document ({len(document_text)} chars)")

        # Use LLM to extract concepts
        from backend.app.llm_client import llm_client

        response = await llm_client.create_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Extract key concepts, definitions, and important topics from the document. "
                              "Organize them into categories. Return as JSON with keys: definitions, topics, entities, relationships"
                },
                {
                    "role": "user",
                    "content": document_text[:3000]  # Limit for efficiency
                }
            ],
            temperature=0.5,
            max_tokens=1000,
        )

        # Extract content from response
        if isinstance(response, dict):
            content = response.get("content", response.get("text", "{}"))
        elif hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        try:
            concepts = json.loads(content)
        except json.JSONDecodeError:
            concepts = {
                "definitions": [],
                "topics": [],
                "entities": [],
                "relationships": []
            }

        return {
            "status": "success",
            "concepts": concepts,
            "metadata": {
                "document_length": len(document_text),
                "document_words": len(document_text.split()),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Concept extraction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract concepts: {str(e)}"
        )


# ============================================================================
# PAPER GENERATION FROM DOCUMENT
# ============================================================================

class DocumentPaperRequest(BaseModel):
    """Request model for paper generation from document."""
    document_text: str
    name: str
    course_code: str
    subject: str
    total_questions: int = 15
    total_marks: int = 100
    duration_minutes: int = 90
    distribution: dict


@router.post(
    "/generate-paper",
    summary="Generate Paper from Document",
    description="Generate a complete question paper from document context"
)
async def generate_paper_from_document(request: DocumentPaperRequest):
    """
    Generate question paper from document content.

    Args:
        request: Paper generation request with document context

    Returns:
        Generated paper with questions based on document
    """
    try:
        logger.info(f"Generating paper from document: {request.name}")

        agent = get_agent()

        # Use the document text as context for paper generation
        prompt = f"""
        Generate a {request.total_questions} question paper based on this document content.
        
        Document:
        {request.document_text[:3000]}
        
        Paper Details:
        - Name: {request.name}
        - Course Code: {request.course_code}
        - Subject: {request.subject}
        - Total Marks: {request.total_marks}
        - Duration: {request.duration_minutes} minutes
        - Distribution: {request.distribution}
        
        Create diverse questions covering the document topics.
        """

        response = agent.generate(
            task="paper_generation",
            prompt=prompt
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        questions = response.get("questions", [])

        logger.info(f"Generated {len(questions)} questions for paper: {request.name}")

        return {
            "status": "success",
            "data": {
                "name": request.name,
                "course_code": request.course_code,
                "subject": request.subject,
                "total_questions": len(questions),
                "total_marks": request.total_marks,
                "duration_minutes": request.duration_minutes,
                "questions": questions,
                "source": "document",
                "metadata": {
                    "document_length": len(request.document_text),
                    "generated_from_document": True
                }
            },
            "message": f"Paper generated successfully with {len(questions)} questions"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paper generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate paper: {str(e)}"
        )


# ============================================================================
# ASSIGNMENT GENERATION FROM DOCUMENT
# ============================================================================

class DocumentAssignmentRequest(BaseModel):
    """Request model for assignment generation from document."""
    document_text: str
    name: str
    course_code: str
    subject: str
    assignment_type: str
    difficulty: str
    max_marks: int = 100
    duration_days: int = 7
    num_tasks: int = 3
    description: str


@router.post(
    "/generate-assignment-legacy",
    summary="Generate Assignment from Document (Legacy)",
    description="Generate an assignment from document context using legacy method"
)
async def generate_assignment_from_document_legacy(request: DocumentAssignmentRequest):
    """
    Generate assignment from document content using legacy method.

    Args:
        request: Assignment generation request with document context

    Returns:
        Generated assignment with tasks based on document
    """
    try:
        logger.info(f"Generating assignment from document (legacy): {request.name}")

        agent = get_agent()

        # Use the document text as context for assignment generation
        prompt = f"""
        Generate a {request.num_tasks} task assignment based on this document content.
        
        Document:
        {request.document_text[:3000]}
        
        Assignment Details:
        - Name: {request.name}
        - Course Code: {request.course_code}
        - Subject: {request.subject}
        - Type: {request.assignment_type}
        - Difficulty: {request.difficulty}
        - Max Marks: {request.max_marks}
        - Due in: {request.duration_days} days
        - Description: {request.description}
        
        Create diverse tasks covering the document topics.
        """

        response = agent.generate(
            task="assignment_generation",
            prompt=prompt
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        tasks = response.get("tasks", [])

        logger.info(f"Generated {len(tasks)} tasks for assignment: {request.name}")

        return {
            "status": "success",
            "data": {
                "name": request.name,
                "course_code": request.course_code,
                "subject": request.subject,
                "assignment_type": request.assignment_type,
                "difficulty": request.difficulty,
                "max_marks": request.max_marks,
                "duration_days": request.duration_days,
                "tasks": tasks,
                "source": "document",
                "metadata": {
                    "document_length": len(request.document_text),
                    "generated_from_document": True
                }
            },
            "message": f"Assignment generated successfully with {len(tasks)} tasks"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assignment generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate assignment: {str(e)}"
        )


# ============================================================================
# REGULAR ASSIGNMENT GENERATION (Non-Document Based)
# ============================================================================

@router.post("/assignments/generate")
async def generate_assignment(
    name: str = Query(..., description="Assignment name"),
    course_code: str = Query(..., description="Course code"),
    subject: str = Query(..., description="Subject area"),
    assignment_type: str = Query(..., description="Type of assignment"),
    difficulty: str = Query(..., description="Difficulty level"),
    max_marks: int = Query(..., description="Maximum marks"),
    duration_days: int = Query(..., description="Duration in days"),
    num_tasks: int = Query(..., description="Number of tasks"),
    description: str = Query(..., description="Assignment description"),
    include_solutions: bool = Query(True, description="Include solutions"),
    include_starter_code: bool = Query(False, description="Include starter code"),
    include_test_cases: bool = Query(False, description="Include test cases"),
    topic: Optional[str] = Query(None, description="Specific topic"),
    bloom_distribution: Optional[str] = Query(None, description="Bloom's distribution JSON"),
    chat_context: Optional[str] = Query(None, description="Chat context"),
) -> Dict[str, Any]:
    """
    Generate an assignment with Bloom's taxonomy support.
    """
    try:
        logger.info(f"Generating assignment: {name}")
        
        # Parse bloom_distribution if provided
        bloom_dict = {}
        if bloom_distribution:
            try:
                bloom_dict = json.loads(bloom_distribution)
                logger.info(f"Parsed Bloom distribution: {bloom_dict}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse bloom_distribution: {bloom_distribution}, error: {e}")
        
        # Prepare parameters for agent
        params = {
            "name": name,
            "course_code": course_code,
            "subject": subject,
            "topic": topic or subject,
            "assignment_type": assignment_type,
            "difficulty": difficulty,
            "max_marks": max_marks,
            "duration_days": duration_days,
            "num_tasks": num_tasks,
            "description": description,
            "include_solutions": include_solutions,
            "include_starter_code": include_starter_code,
            "include_test_cases": include_test_cases,
            "bloom_distribution": bloom_dict,
            "chat_context": chat_context or ""
        }
        
        # Initialize agent
        prompt_builder = PromptBuilder()
        agent = AssignmentGenerationAgent(prompt_builder)
        
        # Generate assignment - REMOVED await
        assignment = agent.generate_assignment(params)
        
        logger.info(f"Successfully generated assignment with {len(assignment.get('tasks', []))} tasks")
        return assignment
        
    except Exception as e:
        logger.error(f"Assignment generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-assignment")
async def generate_assignment_from_document(
    document_text: str = Query(..., description="Document text"),
    name: str = Query(..., description="Assignment name"),
    course_code: str = Query(..., description="Course code"),
    subject: str = Query(..., description="Subject area"),
    assignment_type: str = Query(..., description="Type of assignment"),
    difficulty: str = Query(..., description="Difficulty level"),
    max_marks: int = Query(..., description="Maximum marks"),
    duration_days: int = Query(..., description="Duration in days"),
    num_tasks: int = Query(..., description="Number of tasks"),
    description: str = Query(..., description="Assignment description"),
    bloom_distribution: Optional[str] = Query(None, description="Bloom's distribution JSON"),
    chat_context: Optional[str] = Query(None, description="Chat context"),
    topic: Optional[str] = Query(None, description="Specific topic"),
) -> Dict[str, Any]:
    """
    Generate an assignment from document context with Bloom's taxonomy.
    """
    try:
        logger.info(f"Generating assignment from document: {name}")
        
        # Parse bloom_distribution if provided
        bloom_dict = {}
        if bloom_distribution:
            try:
                bloom_dict = json.loads(bloom_distribution)
                logger.info(f"Parsed Bloom distribution: {bloom_dict}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse bloom_distribution: {bloom_distribution}, error: {e}")
        
        # Prepare parameters
        params = {
            "name": name,
            "course_code": course_code,
            "subject": subject,
            "topic": topic or subject,
            "assignment_type": assignment_type,
            "difficulty": difficulty,
            "max_marks": max_marks,
            "duration_days": duration_days,
            "num_tasks": num_tasks,
            "description": description,
            "bloom_distribution": bloom_dict,
            "chat_context": chat_context or "",
            "document_text": document_text
        }
        
        # Initialize agent
        prompt_builder = PromptBuilder()
        agent = AssignmentGenerationAgent(prompt_builder)
        
        # Generate assignment from document - REMOVED await
        assignment = agent.generate_assignment_from_document(document_text, params)
        
        logger.info(f"Successfully generated assignment from document with {len(assignment.get('tasks', []))} tasks")
        return assignment
        
    except Exception as e:
        logger.error(f"Assignment generation from document error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))