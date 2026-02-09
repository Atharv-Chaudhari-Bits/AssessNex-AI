"""
Bloom's Taxonomy Schema and Ontologies.

Defines Bloom's taxonomy levels, domain ontologies, and pedagogical metadata
for enhanced question generation and assessment alignment.

References:
- Bloom's Taxonomy Revision (Anderson & Krathwohl, 2001)
- Pedagogical alignment for MTech level education
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class BloomLevel(str, Enum):
    """
    Bloom's Taxonomy Levels (Revised).

    From lowest to highest order of cognitive complexity.
    """
    REMEMBER = "Remember"          # Level 1: Recall facts and basic concepts
    UNDERSTAND = "Understand"      # Level 2: Explain ideas or concepts
    APPLY = "Apply"                # Level 3: Use information in new situations
    ANALYZE = "Analyze"            # Level 4: Draw connections among ideas
    EVALUATE = "Evaluate"          # Level 5: Justify a stand or decision
    CREATE = "Create"              # Level 6: Produce new or original work


# Mapping of question types to appropriate Bloom levels
QUESTION_TYPE_BLOOM_MAPPING = {
    "Multiple Choice": [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND, BloomLevel.APPLY],
    "True/False": [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND],
    "Fill in the Blank": [BloomLevel.REMEMBER, BloomLevel.UNDERSTAND],
    "Short Answer": [BloomLevel.UNDERSTAND, BloomLevel.APPLY, BloomLevel.ANALYZE],
    "Long Answer": [BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE],
    "Numerical Problem": [BloomLevel.APPLY, BloomLevel.ANALYZE],
    "Code Implementation": [BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.CREATE],
    "Code Output Prediction": [BloomLevel.UNDERSTAND, BloomLevel.APPLY, BloomLevel.ANALYZE],
    "Complexity Analysis": [BloomLevel.ANALYZE, BloomLevel.EVALUATE],
    "Scenario-Based": [BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.EVALUATE],
    "Essay": [BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE],
    "Diagram-Based": [BloomLevel.UNDERSTAND, BloomLevel.APPLY, BloomLevel.ANALYZE],
}


# Cognitive complexity weights for difficulty calibration
BLOOM_DIFFICULTY_WEIGHTS = {
    BloomLevel.REMEMBER: 1.0,      # Lowest complexity
    BloomLevel.UNDERSTAND: 1.5,
    BloomLevel.APPLY: 2.0,
    BloomLevel.ANALYZE: 2.5,
    BloomLevel.EVALUATE: 3.0,
    BloomLevel.CREATE: 3.5,         # Highest complexity
}


class BloomMetadata(BaseModel):
    """
    Metadata for Bloom's Taxonomy alignment.

    Provides rich pedagogical information about questions.
    """
    bloom_level: BloomLevel = Field(
        ...,
        description="Bloom's taxonomy level for this question"
    )
    cognitive_complexity: float = Field(
        ...,
        ge=1.0,
        le=3.5,
        description="Numerical cognitive complexity score based on Bloom level"
    )
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="Learning objectives this question addresses"
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills required to answer this question"
    )
    prerequisite_knowledge: List[str] = Field(
        default_factory=list,
        description="Prior knowledge required"
    )
    cognitive_processes: List[str] = Field(
        default_factory=list,
        description="Cognitive processes involved (remembering, understanding, applying, etc.)"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = False


class DomainOntology(BaseModel):
    """
    Domain-specific ontology for question generation.

    Provides structured knowledge about subject domains.
    """
    subject: str = Field(..., description="Subject area")
    topic: str = Field(..., description="Main topic")
    subtopics: List[str] = Field(
        default_factory=list,
        description="Subtopics within this domain"
    )
    concepts: List[str] = Field(
        default_factory=list,
        description="Key concepts in this domain"
    )
    relationships: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Concept relationships (e.g., prerequisites, depends_on, related_to)"
    )
    learning_pathways: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recommended learning progressions"
    )
    difficulty_calibration: Dict[str, float] = Field(
        default_factory=dict,
        description="Topic-specific difficulty adjustments"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


# Domain ontologies for common AI/ML subjects
DOMAIN_ONTOLOGIES = {
    "Machine Learning": DomainOntology(
        subject="Machine Learning",
        topic="Fundamentals and Advanced Techniques",
        subtopics=[
            "Supervised Learning",
            "Unsupervised Learning",
            "Reinforcement Learning",
            "Feature Engineering",
            "Model Evaluation",
            "Hyperparameter Tuning",
            "Ensemble Methods",
            "Time Series Analysis"
        ],
        concepts=[
            "Regression", "Classification", "Clustering", "Dimensionality Reduction",
            "Overfitting", "Underfitting", "Bias-Variance Tradeoff", "Cross Validation",
            "Loss Functions", "Optimization", "Gradient Descent", "Neural Networks"
        ],
        relationships={
            "Supervised Learning": ["Classification", "Regression"],
            "Unsupervised Learning": ["Clustering", "Dimensionality Reduction"],
            "Feature Engineering": ["Supervised Learning", "Unsupervised Learning"],
            "Model Evaluation": ["Cross Validation", "Loss Functions"],
        },
        difficulty_calibration={
            "Supervised Learning": 1.0,
            "Feature Engineering": 1.5,
            "Ensemble Methods": 2.0,
            "Hyperparameter Tuning": 2.0,
        }
    ),
    "Deep Learning": DomainOntology(
        subject="Deep Learning",
        topic="Neural Networks and Advanced Architectures",
        subtopics=[
            "Artificial Neural Networks",
            "Convolutional Neural Networks",
            "Recurrent Neural Networks",
            "Attention Mechanisms",
            "Transformers",
            "Generative Models",
            "Optimization Techniques",
            "Regularization Methods"
        ],
        concepts=[
            "Forward Propagation", "Backpropagation", "Activation Functions",
            "Convolution", "Pooling", "LSTM", "GRU", "Attention", "Transformer",
            "Batch Normalization", "Dropout", "L1/L2 Regularization"
        ],
        relationships={
            "Convolutional Neural Networks": ["Convolution", "Pooling"],
            "Recurrent Neural Networks": ["LSTM", "GRU"],
            "Transformers": ["Attention Mechanisms"],
            "Generative Models": ["Neural Networks"],
        },
        difficulty_calibration={
            "Artificial Neural Networks": 1.5,
            "Convolutional Neural Networks": 2.0,
            "Transformers": 2.5,
            "Generative Models": 2.5,
        }
    ),
    "Natural Language Processing": DomainOntology(
        subject="Natural Language Processing",
        topic="Language Understanding and Generation",
        subtopics=[
            "Text Preprocessing",
            "Tokenization",
            "Word Embeddings",
            "Language Models",
            "Machine Translation",
            "Sentiment Analysis",
            "Named Entity Recognition",
            "Question Answering"
        ],
        concepts=[
            "Tokenization", "Stemming", "Lemmatization", "Word2Vec", "GloVe", "FastText",
            "N-grams", "TF-IDF", "BERT", "GPT", "Attention", "Sequence-to-Sequence"
        ],
        relationships={
            "Word Embeddings": ["Word2Vec", "GloVe", "FastText"],
            "Language Models": ["BERT", "GPT"],
            "Machine Translation": ["Sequence-to-Sequence", "Attention"],
        },
        difficulty_calibration={
            "Text Preprocessing": 1.0,
            "Word Embeddings": 1.5,
            "Language Models": 2.5,
            "Question Answering": 2.5,
        }
    ),
    "Computer Vision": DomainOntology(
        subject="Computer Vision",
        topic="Image Analysis and Understanding",
        subtopics=[
            "Image Fundamentals",
            "Image Processing",
            "Feature Detection",
            "Object Detection",
            "Semantic Segmentation",
            "Instance Segmentation",
            "Image Classification",
            "3D Vision"
        ],
        concepts=[
            "Pixels", "Filters", "Convolution", "Edge Detection", "Keypoints",
            "SIFT", "SURF", "HOG", "YOLO", "R-CNN", "Mask R-CNN", "U-Net"
        ],
        relationships={
            "Object Detection": ["Feature Detection", "Convolutional Networks"],
            "Semantic Segmentation": ["Convolutional Networks"],
            "3D Vision": ["Depth Estimation", "Point Clouds"],
        },
        difficulty_calibration={
            "Image Fundamentals": 1.0,
            "Object Detection": 2.0,
            "3D Vision": 2.5,
        }
    ),
}


class PedagogicalAlignment(BaseModel):
    """
    Pedagogical alignment information for a question.

    Ensures questions align with learning objectives and curriculum standards.
    """
    bloom_level: BloomLevel = Field(..., description="Bloom's taxonomy level")
    learning_outcome: str = Field(
        ...,
        description="Specific learning outcome this question assesses"
    )
    curriculum_standard: Optional[str] = Field(
        None,
        description="Relevant curriculum standard (if applicable)"
    )
    assessment_type: str = Field(
        default="formative",
        description="Type of assessment (formative/summative)"
    )
    difficulty_adjusted: bool = Field(
        default=False,
        description="Whether difficulty has been adjusted based on calibration"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = False


class ValidationMetadata(BaseModel):
    """
    Validation results and metadata for a question.

    Tracks semantic checks, plagiarism, originality, and quality metrics.
    """
    semantic_validity: bool = Field(
        default=True,
        description="Whether question is semantically valid"
    )
    semantic_issues: List[str] = Field(
        default_factory=list,
        description="List of semantic issues found"
    )
    plagiarism_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Plagiarism score (0=original, 1=plagiarized)"
    )
    originality_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Originality score (0=generic, 1=novel)"
    )
    grammatical_quality: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Grammar and clarity quality score"
    )
    clarity_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Question clarity score"
    )
    overall_quality_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall quality score (average of all metrics)"
    )
    validation_timestamp: Optional[str] = Field(
        None,
        description="When validation was performed (ISO format)"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
