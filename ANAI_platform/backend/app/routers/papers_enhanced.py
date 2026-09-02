"""
Enhanced Papers endpoints router.

Handles question paper generation with Bloom's taxonomy alignment,
validation, and metrics evaluation.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import json
import asyncio
from backend.app.schemas import (
    PaperGenerationRequest,
    PaperGenerationResponse,
    BloomLevelsResponse,
    DomainOntologyResponse,
    QuestionTypeConfiguration,
)
from backend.app.schemas.bloom_taxonomy import (
    BloomLevel, QUESTION_TYPE_BLOOM_MAPPING, DOMAIN_ONTOLOGIES
)
from backend.app.config import get_settings
# Replace line 23 with:
try:
    from backend.app.agents.paper_agent_enhanced import get_paper_agent
except ImportError:
    # Fallback import
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from backend.app.agents.paper_agent_enhanced import get_paper_agent
from backend.app.utils.logger import get_logger
from backend.app.utils.metrics import get_metrics_calculator
from backend.app.utils.validation import get_validator

logger = get_logger(__name__)
router = APIRouter(prefix="/papers", tags=["papers"])


@router.get(
    "/bloom-levels",
    response_model=BloomLevelsResponse,
    summary="Get Bloom's Taxonomy Levels",
    description="Retrieve available Bloom's taxonomy levels for question alignment"
)
async def get_bloom_levels() -> BloomLevelsResponse:
    """
    Get available Bloom's taxonomy levels.

    Returns:
        BloomLevelsResponse: Available Bloom levels with descriptions

    Example:
        GET /api/v1/papers/bloom-levels
    """
    try:
        descriptions = {
            BloomLevel.REMEMBER.value: "Recall facts and basic concepts",
            BloomLevel.UNDERSTAND.value: "Explain ideas or concepts",
            BloomLevel.APPLY.value: "Use information in new situations",
            BloomLevel.ANALYZE.value: "Draw connections among ideas",
            BloomLevel.EVALUATE.value: "Justify a stand or decision",
            BloomLevel.CREATE.value: "Produce new or original work",
        }

        levels = [level.value for level in BloomLevel]

        return BloomLevelsResponse(
            levels=levels,
            descriptions=descriptions
        )

    except Exception as e:
        logger.error(f"Error fetching Bloom levels: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch Bloom levels")


@router.get(
    "/question-types",
    response_model=dict,
    summary="Get Question Type Configurations",
    description="Retrieve available question types and their Bloom level mappings"
)
async def get_question_types() -> dict:
    """
    Get available question types with Bloom level alignments.

    Returns:
        dict: Question types and their Bloom level mappings

    Example:
        GET /api/v1/papers/question-types
    """
    try:
        question_types = {}
        for qtype, bloom_levels in QUESTION_TYPE_BLOOM_MAPPING.items():
            question_types[qtype] = {
                "bloom_levels": [level.value if hasattr(level, 'value') else level for level in bloom_levels],
                "description": f"Question type: {qtype}"
            }

        return {
            "status": "success",
            "question_types": question_types
        }

    except Exception as e:
        logger.error(f"Error fetching question types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch question types")


@router.get(
    "/domain-ontologies",
    response_model=dict,
    summary="Get Domain Ontologies",
    description="Retrieve domain-specific ontologies and concept hierarchies"
)
async def get_domain_ontologies(
    subject: Optional[str] = Query(None, description="Specific subject to retrieve")
) -> dict:
    """
    Get domain ontologies for subjects.

    Args:
        subject: Optional specific subject

    Returns:
        dict: Domain ontologies with concept hierarchies

    Example:
        GET /api/v1/papers/domain-ontologies?subject=Machine%20Learning
    """
    try:
        if subject:
            if subject not in DOMAIN_ONTOLOGIES:
                raise HTTPException(
                    status_code=404,
                    detail=f"Domain ontology for '{subject}' not found"
                )

            ontology = DOMAIN_ONTOLOGIES[subject]
            return {
                "status": "success",
                "subject": subject,
                "ontology": {
                    "topics": ontology.subtopics,
                    "concepts": ontology.concepts,
                    "relationships": ontology.relationships,
                    "difficulty_calibration": ontology.difficulty_calibration
                }
            }
        else:
            # Return all available subjects
            subjects = list(DOMAIN_ONTOLOGIES.keys())
            return {
                "status": "success",
                "available_subjects": subjects,
                "message": "Use ?subject=<name> to get specific ontology"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching domain ontologies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch domain ontologies")


@router.post(
    "/generate",
    response_model=PaperGenerationResponse,
    summary="Generate Question Paper",
    description="Generate a complete question paper with Bloom's alignment and validation"
)
async def generate_paper(request: PaperGenerationRequest) -> PaperGenerationResponse:
    """
    Generate a complete question paper.

    Features:
    - Bloom's taxonomy alignment
    - Multi-tier validation (semantic, plagiarism, originality, grammar)
    - Metrics evaluation (diversity, fairness, clarity)
    - Explainability logging

    Args:
        request: Paper generation request with configuration

    Returns:
        PaperGenerationResponse: Generated paper with validation and metrics

    Raises:
        HTTPException: If generation fails

    Example:
        POST /api/v1/papers/generate
        {
            "subject": "Machine Learning",
            "topic": "Supervised Learning",
            "subtopics": ["Linear Regression", "Classification"],
            "total_marks": 100,
            "duration_minutes": 180,
            "question_type_config": [
                {
                    "type": "Multiple Choice",
                    "count": 10,
                    "marks_each": 1,
                    "difficulty": "medium",
                    "bloom_levels": ["Remember", "Understand", "Apply"]
                }
            ],
            "bloom_distribution": {
                "Remember": 10,
                "Understand": 25,
                "Apply": 30,
                "Analyze": 20,
                "Evaluate": 10,
                "Create": 5
            },
            "enable_validation": true,
            "enable_metrics": true,
            "enable_explainability": true
        }
    """
    try:
        logger.info(
            f"Paper generation request for {request.subject}/{request.topic} "
            f"({request.total_marks} marks, {request.duration_minutes} min)"
        )

        # Validate question type configurations
        for config in request.question_type_config:
            if config.type not in QUESTION_TYPE_BLOOM_MAPPING:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown question type: {config.type}"
                )

        # Get paper generation agent
        paper_agent = get_paper_agent()

        # Generate paper (async)
        paper = await paper_agent.generate_paper(
            subject=request.subject,
            topic=request.topic,
            total_marks=request.total_marks,
            duration_minutes=request.duration_minutes,
            question_type_config=[config.dict() for config in request.question_type_config],
            difficulty_distribution=request.difficulty_distribution,
            bloom_distribution=request.bloom_distribution,
            exam_name=request.exam_name,
            subtopics=request.subtopics,
            instructions=request.instructions
        )

        if "error" in paper:
            logger.error(f"Paper generation failed: {paper['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Paper generation failed: {paper['error']}"
            )

        # Extract validation and metrics results
        validation_summary = None
        metrics_evaluation = None

        if request.enable_validation:
            val_results = paper.get("validation_summary", {})
            if "metrics" in val_results:
                metrics = val_results["metrics"]
                validation_summary = {
                    "total_questions": metrics.get("total_questions", 0),
                    "valid_questions": metrics.get("valid_questions", 0),
                    "validity_percentage": metrics.get("validity_percentage", 0),
                    "average_quality_score": metrics.get("average_quality_score", 0),
                    "average_originality_score": metrics.get("average_originality_score", 0),
                    "diversity_issues": metrics.get("diversity_issues", [])
                }

        if request.enable_metrics:
            met_results = paper.get("metrics_results", {})
            if "metrics" in met_results:
                met = met_results["metrics"]
                metrics_evaluation = {
                    "overall_score": met.get("overall_score", 0),
                    "diversity_score": met.get("diversity_score", 0),
                    "cognitive_fairness": met.get("cognitive_fairness", 0),
                    "difficulty_fairness": met.get("difficulty_fairness", 0),
                    "recommendations": met.get("recommendations", [])
                }

        logger.info(f"Paper generated successfully: {paper.get('paper_id')}")

        return PaperGenerationResponse(
            status="success",
            message=f"Question paper generated successfully for {request.subject}/{request.topic}",
            paper=paper,
            validation=validation_summary,
            metrics=metrics_evaluation,
            metadata={
                "generation_time": paper.get("metadata", {}).get("generation_time"),
                "total_sections": len(paper.get("sections", [])),
                "total_questions": sum(
                    len(s.get("questions", []))
                    for s in paper.get("sections", [])
                ),
                "total_marks": request.total_marks,
                "duration_minutes": request.duration_minutes
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating paper: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Paper generation failed: {str(e)}"
        )


@router.get(
    "/template-examples",
    response_model=dict,
    summary="Get Paper Generation Template Examples",
    description="Retrieve example configurations for common paper types"
)
async def get_template_examples() -> dict:
    """
    Get example configurations for paper generation.

    Returns:
        dict: Template examples for different paper types

    Example:
        GET /api/v1/papers/template-examples
    """
    templates = {
        "mtx_standard_100_marks": {
            "description": "Standard MTech paper (100 marks, 3 hours)",
            "config": {
                "total_marks": 100,
                "duration_minutes": 180,
                "question_type_config": [
                    {
                        "type": "Multiple Choice",
                        "count": 10,
                        "marks_each": 1,
                        "difficulty": "mixed",
                        "bloom_levels": ["Remember", "Understand", "Apply"]
                    },
                    {
                        "type": "Short Answer",
                        "count": 5,
                        "marks_each": 4,
                        "difficulty": "medium",
                        "bloom_levels": ["Understand", "Apply", "Analyze"]
                    },
                    {
                        "type": "Long Answer",
                        "count": 3,
                        "marks_each": 20,
                        "difficulty": "hard",
                        "bloom_levels": ["Analyze", "Evaluate", "Create"]
                    }
                ]
            }
        },
        "coding_focused_100_marks": {
            "description": "Coding-focused MTech paper",
            "config": {
                "total_marks": 100,
                "duration_minutes": 180,
                "question_type_config": [
                    {
                        "type": "Code Output Prediction",
                        "count": 5,
                        "marks_each": 4,
                        "difficulty": "medium"
                    },
                    {
                        "type": "Code Implementation",
                        "count": 3,
                        "marks_each": 20,
                        "difficulty": "hard"
                    }
                ]
            }
        },
        "conceptual_100_marks": {
            "description": "Conceptual understanding focused paper",
            "config": {
                "total_marks": 100,
                "duration_minutes": 180,
                "question_type_config": [
                    {
                        "type": "Multiple Choice",
                        "count": 15,
                        "marks_each": 2,
                        "difficulty": "medium"
                    },
                    {
                        "type": "Short Answer",
                        "count": 10,
                        "marks_each": 5,
                        "difficulty": "medium"
                    }
                ]
            }
        }
    }

    return {
        "status": "success",
        "templates": templates,
        "message": "Use these configurations as templates for paper generation"
    }


@router.get(
    "/validation-report",
    response_model=dict,
    summary="Get Validation Report Details",
    description="Get detailed validation report for a paper"
)
async def get_validation_report(
    paper_id: str = Query(..., description="Paper ID to get validation report for")
) -> dict:
    """
    Get detailed validation report for a paper.

    Args:
        paper_id: The paper ID

    Returns:
        dict: Detailed validation report

    Example:
        GET /api/v1/papers/validation-report?paper_id=paper_20240121T120000
    """
    try:
        logger.info(f"Retrieving validation report for paper: {paper_id}")

        # In production, fetch from database
        # For now, return placeholder
        return {
            "status": "success",
            "message": f"Validation report for {paper_id}",
            "note": "Validation reports are stored and can be retrieved for analysis"
        }

    except Exception as e:
        logger.error(f"Error retrieving validation report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve validation report")
