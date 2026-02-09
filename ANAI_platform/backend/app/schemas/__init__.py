"""
Pydantic models and schemas for request/response validation.

This module defines all data structures used throughout the AssessNex AI
backend API for type validation and documentation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, validator

class DifficultyLevel(str, Enum):
    """Enumeration for question difficulty levels."""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class QuestionType(str, Enum):
    """Enumeration for question types."""
    MULTIPLE_CHOICE = "Multiple Choice"
    SHORT_ANSWER = "Short Answer"
    LONG_ANSWER = "Long Answer"
    CODE_IMPLEMENTATION = "Code Implementation"
    ESSAY = "Essay"
    TRUE_FALSE = "True/False"
    FILL_IN_BLANK = "Fill in the Blank"
    SCENARIO = "Scenario-Based"
    CODE_OUTPUT = "Code Output Prediction"
    COMPLEXITY = "Complexity Analysis"
    NUMERICAL_PROBLEM = "Numerical Problem"
    DIAGRAM_BASED = "Diagram-Based"
    ASSIGNMENT = "Assignment"
    QUESTION_PAPER = "Question Paper"


class Subject(str, Enum):
    """Enumeration for available subjects."""
    MACHINE_LEARNING = "Machine Learning"
    DEEP_LEARNING = "Deep Learning"
    NATURAL_LANGUAGE_PROCESSING = "Natural Language Processing"
    COMPUTER_VISION = "Computer Vision"
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    REINFORCEMENT_LEARNING = "Reinforcement Learning"
    DATA_SCIENCE = "Data Science"
    CRYPTOGRAPHY = "Cryptography"


class QuestionGenerationRequest(BaseModel):
    """
    Request model for generating questions.

    Attributes:
        subject: Subject area for question generation
        question_type: Type of questions to generate
        difficulty_level: Difficulty level of questions
        num_questions: Number of questions to generate (1-50)
        additional_context: Optional context for question generation
        diagram_format: Optional format for diagrams (Mermaid/ASCII) - only for Diagram-Based
    """
    subject: Subject = Field(..., description="Subject area for questions")
    question_type: QuestionType = Field(..., description="Type of questions")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    num_questions: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of questions to generate"
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context for question generation"
    )
    diagram_format: Optional[str] = Field(
        default=None,
        description="Format for diagrams: 'Mermaid.js (Interactive Flowcharts)' or 'ASCII Art (Text-based Diagrams)'"
    )

    @validator("num_questions")
    def validate_num_questions(cls, value: int) -> int:
        """
        Validate the number of questions.

        Args:
            value: Number of questions requested

        Returns:
            int: Validated number of questions

        Raises:
            ValueError: If value is outside valid range
        """
        if not (1 <= value <= 50):
            raise ValueError("num_questions must be between 1 and 50")
        return value


class Question(BaseModel):
    """
    Model representing a single generated question.

    Attributes:
        id: Unique identifier for the question
        subject: Subject area of the question
        question_type: Type of the question
        difficulty_level: Difficulty level of the question
        question_text: The actual question text
        options: Optional list of options for multiple choice questions
        expected_answer: Expected answer or answer key
        explanation: Detailed explanation for the answer
        tags: Optional tags for categorization
    """
    id: str = Field(..., description="Unique question identifier")
    subject: str = Field(..., description="Subject area")
    question_type: str = Field(..., description="Type of question")
    difficulty_level: str = Field(..., description="Difficulty level")
    question_text: str = Field(..., description="The question")
    options: Optional[List[str]] = Field(
        default=None,
        description="Options for multiple choice questions"
    )
    expected_answer: str = Field(..., description="Expected answer")
    explanation: str = Field(..., description="Answer explanation")
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags for categorization"
    )
    
    class Config:
        """Pydantic config for lenient parsing."""
        arbitrary_types_allowed = True
        
    @validator("options", pre=True, always=True)
    def validate_options(cls, value):
        """Validate and fix options field."""
        # If value is None, keep it None
        if value is None:
            return None
        # If it's a boolean, convert to None
        if isinstance(value, bool):
            return None
        # If it's a list, ensure all items are strings
        if isinstance(value, list):
            return [str(item) if item is not None else "" for item in value]
        # For anything else, return None
        return None


class QuestionGenerationResponse(BaseModel):
    """
    Response model for question generation requests.

    Attributes:
        status: Success status of the request
        message: Descriptive message
        data: List of generated questions
        metadata: Additional metadata about the generation
    """
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: List[Question] = Field(..., description="Generated questions")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class SubjectListResponse(BaseModel):
    """
    Response model for listing available subjects.

    Attributes:
        subjects: List of available subjects
    """
    subjects: List[str] = Field(..., description="List of available subjects")


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.

    Attributes:
        status: Health status
        version: Application version
        environment: Current environment
    """
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")


class ErrorResponse(BaseModel):
    """
    Response model for error responses.

    Attributes:
        error: Error type or code
        message: Detailed error message
        details: Optional detailed error information
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )


class SimilarityMatch(BaseModel):
    """
    Model for a similarity match in plagiarism check.

    Attributes:
        reference_id: ID of the reference question
        similarity_score: Score indicating similarity (0-1)
        similarity_type: Type of similarity detected
        overlapping_concepts: List of overlapping concepts
        confidence: Confidence level of the match
    """
    reference_id: str = Field(..., description="Reference question ID")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    similarity_type: str = Field(..., description="Type of similarity")
    overlapping_concepts: List[str] = Field(
        default_factory=list,
        description="Overlapping concepts"
    )
    confidence: float = Field(default=0.5, description="Confidence level")


class DetailedAnalysis(BaseModel):
    """
    Detailed similarity analysis breakdown.

    Attributes:
        concept_overlap: Conceptual overlap score
        wording_similarity: Wording similarity score
        structure_similarity: Structure similarity score
        overall_similarity: Overall weighted similarity
    """
    concept_overlap: float = Field(..., description="Concept overlap score")
    wording_similarity: float = Field(..., description="Wording similarity score")
    structure_similarity: float = Field(..., description="Structure similarity score")
    overall_similarity: float = Field(..., description="Overall similarity score")


class PlagiarismCheckRequest(BaseModel):
    """
    Request model for plagiarism check.

    Attributes:
        current_question: The question to check
        reference_questions: Questions to compare against
        plagiarism_threshold: Threshold for flagging as plagiarized
    """
    current_question: Dict[str, Any] = Field(
        ...,
        description="Question to check"
    )
    reference_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Reference questions for comparison"
    )
    plagiarism_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Plagiarism threshold (0-1)"
    )


class PlagiarismCheckResponse(BaseModel):
    """
    Response model for plagiarism check.

    Attributes:
        uniqueness_score: Uniqueness score (0-1)
        plagiarism_score: Plagiarism score (0-1)
        similarity_matches: List of similar questions found
        is_plagiarized: Whether question is plagiarized
        plagiarism_threshold_exceeded: Whether threshold was exceeded
        recommendations: List of recommendations
        detailed_analysis: Detailed breakdown of analysis
    """
    uniqueness_score: float = Field(
        ...,
        description="Uniqueness score (0-1)"
    )
    plagiarism_score: float = Field(
        ...,
        description="Plagiarism score (0-1)"
    )
    similarity_matches: List[SimilarityMatch] = Field(
        default_factory=list,
        description="Similar questions found"
    )
    is_plagiarized: bool = Field(
        ...,
        description="Is question plagiarized"
    )
    plagiarism_threshold_exceeded: bool = Field(
        ...,
        description="Threshold exceeded"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )
    detailed_analysis: Optional[DetailedAnalysis] = Field(
        default=None,
        description="Detailed analysis breakdown"
    )


class BatchPlagiarismCheckRequest(BaseModel):
    """
    Request model for batch plagiarism check.

    Attributes:
        questions: List of questions to check
        reference_questions: Questions to compare against
        plagiarism_threshold: Threshold for flagging
    """
    questions: List[Dict[str, Any]] = Field(
        ...,
        description="Questions to check"
    )
    reference_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Reference questions"
    )
    plagiarism_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Plagiarism threshold"
    )


class BatchPlagiarismCheckResponse(BaseModel):
    """
    Response model for batch plagiarism check.

    Attributes:
        status: Response status
        message: Response message
        results: List of plagiarism check results
        summary: Summary statistics
    """
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    results: List[PlagiarismCheckResponse] = Field(
        ...,
        description="Check results for each question"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics"
    )


class BloomLevel(str, Enum):
    """Bloom's Taxonomy Levels for pedagogical alignment."""
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"


class QuestionTypeConfiguration(BaseModel):
    """Configuration for question type in a paper section."""
    type: str = Field(..., description="Question type (Multiple Choice, Short Answer, etc.)")
    count: int = Field(..., ge=1, description="Number of questions of this type")
    marks_each: int = Field(..., ge=1, description="Marks per question")
    difficulty: str = Field(default="medium", description="Base difficulty: easy/medium/hard")
    bloom_levels: Optional[List[str]] = Field(
        None,
        description="Preferred Bloom's taxonomy levels for this section"
    )


class PaperGenerationRequest(BaseModel):
    """
    Enhanced request model for paper generation.

    Supports Bloom's taxonomy alignment and dynamic configuration.
    """
    subject: str = Field(..., description="Subject area for the paper")
    topic: str = Field(..., description="Main topic of the examination")
    subtopics: Optional[List[str]] = Field(
        default=None,
        description="Specific subtopics to cover"
    )
    total_marks: int = Field(
        default=100,
        ge=50,
        le=500,
        description="Total marks for the paper"
    )
    duration_minutes: int = Field(
        default=180,
        ge=30,
        le=480,
        description="Examination duration in minutes"
    )
    question_type_config: List[QuestionTypeConfiguration] = Field(
        ...,
        description="Configuration for each question type section"
    )
    difficulty_distribution: Optional[Dict[str, int]] = Field(
        None,
        description="Distribution percentages: {easy: 20, medium: 50, hard: 30}"
    )
    bloom_distribution: Optional[Dict[str, int]] = Field(
        None,
        description="Bloom's taxonomy distribution: {Remember: 10, Understand: 25, Apply: 30, Analyze: 20, Evaluate: 10, Create: 5}"
    )
    exam_name: Optional[str] = Field(
        None,
        description="Name of the examination"
    )
    instructions: Optional[Union[str, List[str]]] = Field(
        None,
        description="Custom examination instructions"
    )
    enable_validation: bool = Field(
        default=True,
        description="Enable multi-tier validation of questions"
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics evaluation of the paper"
    )
    enable_explainability: bool = Field(
        default=True,
        description="Enable explainability logging"
    )
    # 🔥 NORMALIZE TO LIST[str]
    @validator("instructions", pre=True)
    def normalize_instructions(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v

class PaperSection(BaseModel):
    """A section of a question paper."""
    section_id: str = Field(..., description="Section identifier (A, B, C, etc.)")
    title: str = Field(..., description="Section title")
    question_type: str = Field(..., description="Type of questions in this section")
    num_questions: int = Field(..., description="Number of questions in section")
    marks_per_question: int = Field(..., description="Marks per question")
    total_marks: int = Field(..., description="Total marks for section")
    instructions: str = Field(..., description="Section-specific instructions")
    questions: List[Question] = Field(..., description="Questions in this section")


class PaperHeader(BaseModel):
    """Header information for a question paper."""
    exam_name: str = Field(..., description="Name of examination")
    subject: str = Field(..., description="Subject")
    topic: str = Field(..., description="Main topic")
    total_marks: int = Field(..., description="Total marks")
    duration: str = Field(..., description="Duration (e.g., '180 minutes')")
    date: str = Field(..., description="Examination date")
    instructions: List[str] = Field(..., description="General instructions")
    answer_key: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Answer key with explanations"
    )


class ValidationSummary(BaseModel):
    """Summary of validation results."""
    total_questions: int = Field(..., description="Total questions validated")
    valid_questions: int = Field(..., description="Number of valid questions")
    validity_percentage: float = Field(..., description="Percentage of valid questions")
    average_quality_score: float = Field(..., description="Average quality score (0-1)")
    average_originality_score: float = Field(..., description="Average originality score (0-1)")
    diversity_issues: List[str] = Field(default_factory=list, description="Identified diversity issues")


class MetricsEvaluation(BaseModel):
    """Metrics evaluation results for a paper."""
    overall_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    diversity_score: float = Field(..., ge=0, le=1, description="Question diversity score")
    cognitive_fairness: float = Field(..., ge=0, le=1, description="Bloom's taxonomy fairness")
    difficulty_fairness: float = Field(..., ge=0, le=1, description="Difficulty distribution fairness")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


class PaperGenerationResponse(BaseModel):
    """
    Response model for paper generation.

    Attributes:
        status: Response status (success/failure)
        message: Response message
        paper: Generated question paper
        validation: Validation results (if enabled)
        metrics: Metrics evaluation (if enabled)
        metadata: Additional metadata
    """
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    paper: Optional[Dict[str, Any]] = Field(None, description="Generated question paper")
    validation: Optional[ValidationSummary] = Field(None, description="Validation results")
    metrics: Optional[MetricsEvaluation] = Field(None, description="Metrics evaluation")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (generation time, etc.)"
    )


class BloomLevelsResponse(BaseModel):
    """Response providing available Bloom's taxonomy levels."""
    levels: List[str] = Field(..., description="Available Bloom's levels")
    descriptions: Dict[str, str] = Field(..., description="Descriptions of each level")


class DomainOntologyResponse(BaseModel):
    """Response providing domain ontology information."""
    subject: str = Field(..., description="Subject area")
    topics: List[str] = Field(..., description="Available topics")
    concepts: Dict[str, List[str]] = Field(..., description="Concepts per topic")
    recommendations: Dict[str, str] = Field(..., description="Recommendations per topic")
