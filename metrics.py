"""
Metrics and Evaluation Framework for Generated Educational Content.

Provides comprehensive metrics for accuracy, clarity, diversity, and fairness
evaluation of generated questions and papers.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import Counter
import statistics
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked."""
    ACCURACY = "accuracy"
    CLARITY = "clarity"
    DIVERSITY = "diversity"
    FAIRNESS = "fairness"
    QUALITY = "quality"
    COVERAGE = "coverage"
    ALIGNMENT = "alignment"


@dataclass
class MetricResult:
    """Result of a single metric evaluation."""
    metric_type: MetricType
    metric_name: str
    score: float  # 0-1 range
    details: Dict[str, Any]
    timestamp: str

    def __post_init__(self):
        """Validate score range."""
        if not (0.0 <= self.score <= 1.0):
            logger.warning(f"Metric score {self.score} outside 0-1 range, clamping")
            self.score = max(0.0, min(1.0, self.score))


@dataclass
class EvaluationReport:
    """Comprehensive evaluation report."""
    evaluation_id: str
    evaluation_type: str  # 'question', 'paper', 'assignment'
    content_id: str
    metrics: List[MetricResult]
    overall_score: float
    evaluation_timestamp: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'evaluation_id': self.evaluation_id,
            'evaluation_type': self.evaluation_type,
            'content_id': self.content_id,
            'metrics': [
                {
                    'metric_type': m.metric_type.value,
                    'metric_name': m.metric_name,
                    'score': m.score,
                    'details': m.details
                }
                for m in self.metrics
            ],
            'overall_score': self.overall_score,
            'evaluation_timestamp': self.evaluation_timestamp,
            'recommendations': self.recommendations
        }


class AccuracyEvaluator:
    """Evaluates accuracy of generated content."""

    def evaluate_factual_accuracy(
        self,
        question: str,
        answer: str,
        subject: str
    ) -> Tuple[float, List[str]]:
        """
        Evaluate factual accuracy (simplified - would use domain knowledge DB in production).

        Args:
            question: Question text
            answer: Answer text
            subject: Subject area

        Returns:
            Tuple of (accuracy_score, issues)
        """
        issues = []
        score = 1.0

        # Check for contradictions
        if self._has_contradictions(question, answer):
            issues.append("Answer contradicts question")
            score -= 0.3

        # Check for completeness
        if len(answer.split()) < 5:
            issues.append("Answer appears incomplete")
            score -= 0.2

        # Domain-specific checks
        if subject in ["Machine Learning", "Deep Learning"]:
            if not self._validate_ml_accuracy(question, answer):
                issues.append("ML concepts may be inaccurate")
                score -= 0.2

        return max(0.0, score), issues

    @staticmethod
    def _has_contradictions(question: str, answer: str) -> bool:
        """Check for logical contradictions."""
        # Simplified check
        contradictory_pairs = [
            ("always", "never"),
            ("must", "cannot"),
            ("true", "false"),
        ]

        q_lower = question.lower()
        a_lower = answer.lower()

        for word1, word2 in contradictory_pairs:
            if word1 in q_lower and word2 in a_lower:
                return True

        return False

    @staticmethod
    def _validate_ml_accuracy(question: str, answer: str) -> bool:
        """Validate ML-specific accuracy."""
        ml_concepts = {
            "overfitting": ["training error", "validation error", "regularization"],
            "underfitting": ["model complexity", "training data"],
            "cross validation": ["k-fold", "splits", "test set"],
        }

        q_lower = question.lower()
        for concept, keywords in ml_concepts.items():
            if concept in q_lower:
                # Check if answer mentions relevant keywords
                if any(kw in answer.lower() for kw in keywords):
                    return True
        return True  # Default to valid if not a specific concept


class ClarityEvaluator:
    """Evaluates clarity of questions."""

    def evaluate_clarity(self, question_text: str) -> Tuple[float, List[str]]:
        """
        Evaluate clarity of question text.

        Args:
            question_text: The question text

        Returns:
            Tuple of (clarity_score, issues)
        """
        issues = []
        score = 1.0

        # Check reading complexity
        reading_level = self._estimate_reading_level(question_text)
        if reading_level > 4:  # Grade 4+ (advanced for MTech)
            issues.append(f"High reading complexity level: {reading_level}")
            score -= 0.1

        # Check for jargon clarity
        if self._has_undefined_jargon(question_text):
            issues.append("Question uses undefined technical jargon")
            score -= 0.2

        # Check sentence structure
        sentences = [s.strip() for s in question_text.split('.') if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        if avg_sentence_length > 30:
            issues.append(f"Average sentence too long: {avg_sentence_length:.0f} words")
            score -= 0.1

        # Check for ambiguity
        if self._has_ambiguous_references(question_text):
            issues.append("Question has ambiguous pronouns or references")
            score -= 0.2

        return max(0.0, score), issues

    @staticmethod
    def _estimate_reading_level(text: str) -> float:
        """Estimate Flesch-Kincaid reading level (simplified)."""
        words = text.split()
        sentences = text.count('.') + text.count('?') + text.count('!')
        syllables = sum(len(word) // 3 for word in words)  # Simplified syllable counting

        if sentences == 0:
            return 1.0

        reading_level = (0.39 * len(words) / max(1, sentences)) + (11.8 * syllables / max(1, len(words))) - 15.59
        return max(1.0, min(18.0, reading_level))

    @staticmethod
    def _has_undefined_jargon(text: str) -> bool:
        """Check for potential undefined jargon."""
        technical_terms = ['algorithm', 'optimization', 'convergence', 'gradient', 'epoch']
        terms_used = sum(1 for term in technical_terms if term in text.lower())
        return terms_used > 3  # Arbitrary threshold

    @staticmethod
    def _has_ambiguous_references(text: str) -> bool:
        """Check for ambiguous pronouns like 'it', 'this', 'that'."""
        import re
        ambiguous_pronouns = re.findall(r'\b(it|this|that|these|those)\b', text, re.IGNORECASE)
        return len(ambiguous_pronouns) > 2


class DiversityEvaluator:
    """Evaluates diversity in question sets."""

    def evaluate_question_diversity(self, questions: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate diversity across a set of questions.

        Args:
            questions: List of question texts

        Returns:
            Tuple of (diversity_score, details)
        """
        if len(questions) < 2:
            return 1.0, {'note': 'Only one question, cannot assess diversity'}

        details = {
            'total_questions': len(questions),
            'unique_topics': len(self._extract_topics(questions)),
            'word_diversity': self._calculate_word_diversity(questions),
            'question_length_variance': self._calculate_length_variance(questions),
            'template_diversity': self._analyze_template_diversity(questions)
        }

        # Calculate composite diversity score
        diversity_score = (
            (details['unique_topics'] / len(questions)) * 0.4 +  # Topic diversity (40%)
            details['word_diversity'] * 0.3 +                     # Vocabulary diversity (30%)
            details['template_diversity'] * 0.3                   # Template diversity (30%)
        )

        return min(1.0, diversity_score), details

    @staticmethod
    def _extract_topics(questions: List[str]) -> set:
        """Extract topics from questions."""
        topics = set()
        topic_keywords = {
            'algorithm': ['algorithm', 'sorting', 'searching'],
            'complexity': ['time', 'space', 'complexity'],
            'optimization': ['optimize', 'efficient', 'fast'],
            'data': ['data', 'database', 'structure'],
        }

        for question in questions:
            q_lower = question.lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in q_lower for kw in keywords):
                    topics.add(topic)

        return topics

    @staticmethod
    def _calculate_word_diversity(questions: List[str]) -> float:
        """Calculate vocabulary diversity using Type-Token Ratio."""
        all_words = []
        for question in questions:
            words = question.lower().split()
            all_words.extend(words)

        if not all_words:
            return 0.0

        unique_words = len(set(all_words))
        type_token_ratio = unique_words / len(all_words)
        return min(1.0, type_token_ratio * 2)  # Scale up since TTR is typically 0.3-0.5

    @staticmethod
    def _calculate_length_variance(questions: List[str]) -> float:
        """Calculate variance in question lengths."""
        lengths = [len(q.split()) for q in questions]
        if len(lengths) < 2:
            return 1.0

        variance = statistics.variance(lengths)
        mean_length = statistics.mean(lengths)

        # Coefficient of variation
        if mean_length > 0:
            cv = variance / (mean_length ** 2)
            return min(1.0, cv)
        return 0.5

    @staticmethod
    def _analyze_template_diversity(questions: List[str]) -> float:
        """Analyze diversity of question templates."""
        # Check for repeated question patterns
        patterns = Counter()
        for question in questions:
            # Simple pattern: first few words
            pattern = ' '.join(question.split()[:3])
            patterns[pattern] += 1

        # If all questions have unique patterns, score = 1.0
        unique_patterns = len(patterns)
        total_questions = sum(patterns.values())

        if total_questions == 0:
            return 1.0

        return unique_patterns / total_questions


class FairnessEvaluator:
    """Evaluates fairness in generated content."""

    def evaluate_cognitive_fairness(self, questions: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate fairness across Bloom's taxonomy levels.

        Args:
            questions: List of question dictionaries with bloom_level

        Returns:
            Tuple of (fairness_score, details)
        """
        if not questions:
            return 1.0, {'note': 'No questions to evaluate'}

        # Count questions by Bloom level
        bloom_counts = Counter()
        for question in questions:
            bloom_level = question.get('bloom_level', 'Unknown')
            bloom_counts[bloom_level] += 1

        # Calculate distribution fairness
        # Ideal: even distribution across Bloom levels
        expected_per_level = len(questions) / len(bloom_counts) if bloom_counts else 0

        chi_squared = sum(
            ((count - expected_per_level) ** 2) / max(1, expected_per_level)
            for count in bloom_counts.values()
        ) if expected_per_level > 0 else 0

        # Normalize to 0-1 (lower chi-squared = more fair)
        fairness_score = 1.0 / (1.0 + chi_squared / len(bloom_counts)) if bloom_counts else 1.0

        return min(1.0, fairness_score), {
            'bloom_distribution': dict(bloom_counts),
            'chi_squared': chi_squared,
            'distribution_fairness': fairness_score
        }

    def evaluate_difficulty_fairness(self, questions: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate fairness in difficulty distribution.

        Args:
            questions: List of question dictionaries with difficulty_level

        Returns:
            Tuple of (fairness_score, details)
        """
        if not questions:
            return 1.0, {'note': 'No questions to evaluate'}

        difficulty_counts = Counter()
        for question in questions:
            difficulty = question.get('difficulty_level', 'Medium')
            difficulty_counts[difficulty] += 1

        # Ideal for MTech: 20% Easy, 50% Medium, 30% Hard
        ideal_distribution = {
            'Easy': 0.2,
            'Medium': 0.5,
            'Hard': 0.3
        }

        total = len(questions)
        actual_distribution = {k: v / total for k, v in difficulty_counts.items()}

        # Calculate deviation from ideal
        deviation = sum(
            abs(actual_distribution.get(level, 0) - ideal_distribution.get(level, 0))
            for level in ideal_distribution.keys()
        )

        fairness_score = 1.0 - (deviation / 2)  # Normalize deviation

        return max(0.0, fairness_score), {
            'difficulty_distribution': dict(difficulty_counts),
            'ideal_distribution': ideal_distribution,
            'actual_distribution': actual_distribution,
            'deviation': deviation
        }


class MetricsCalculator:
    """
    Comprehensive metrics calculator for question and paper evaluation.

    Combines accuracy, clarity, diversity, and fairness metrics.
    """

    def __init__(self):
        """Initialize metrics calculator."""
        self.accuracy_evaluator = AccuracyEvaluator()
        self.clarity_evaluator = ClarityEvaluator()
        self.diversity_evaluator = DiversityEvaluator()
        self.fairness_evaluator = FairnessEvaluator()
        logger.info("MetricsCalculator initialized")

    def evaluate_question(
        self,
        question_id: str,
        question_text: str,
        answer: str,
        subject: str,
        bloom_level: Optional[str] = None,
        difficulty_level: Optional[str] = None
    ) -> EvaluationReport:
        """
        Evaluate a single question comprehensively.

        Args:
            question_id: Unique question identifier
            question_text: The question text
            answer: The answer/solution
            subject: Subject area
            bloom_level: Optional Bloom's taxonomy level
            difficulty_level: Optional difficulty level

        Returns:
            EvaluationReport with all metrics
        """
        metrics = []

        # Accuracy evaluation
        accuracy_score, accuracy_issues = self.accuracy_evaluator.evaluate_factual_accuracy(
            question_text, answer, subject
        )
        metrics.append(MetricResult(
            metric_type=MetricType.ACCURACY,
            metric_name="Factual Accuracy",
            score=accuracy_score,
            details={'issues': accuracy_issues},
            timestamp=datetime.utcnow().isoformat()
        ))

        # Clarity evaluation
        clarity_score, clarity_issues = self.clarity_evaluator.evaluate_clarity(question_text)
        metrics.append(MetricResult(
            metric_type=MetricType.CLARITY,
            metric_name="Clarity",
            score=clarity_score,
            details={'issues': clarity_issues},
            timestamp=datetime.utcnow().isoformat()
        ))

        # Calculate overall score
        overall_score = (accuracy_score + clarity_score) / 2

        # Generate recommendations
        recommendations = []
        if accuracy_score < 0.8:
            recommendations.append("Verify factual accuracy with domain experts")
        if clarity_score < 0.8:
            recommendations.append("Simplify question language or provide more context")

        return EvaluationReport(
            evaluation_id=f"eval_{question_id}_{datetime.utcnow().isoformat()}",
            evaluation_type="question",
            content_id=question_id,
            metrics=metrics,
            overall_score=overall_score,
            evaluation_timestamp=datetime.utcnow().isoformat(),
            recommendations=recommendations
        )

    def evaluate_paper(
        self,
        paper_id: str,
        questions: List[Dict[str, Any]]
    ) -> EvaluationReport:
        """
        Evaluate an entire question paper.

        Args:
            paper_id: Paper identifier
            questions: List of questions in the paper

        Returns:
            EvaluationReport for the paper
        """
        metrics = []

        # Diversity evaluation
        question_texts = [q.get('question_text', '') for q in questions]
        diversity_score, diversity_details = self.diversity_evaluator.evaluate_question_diversity(question_texts)
        metrics.append(MetricResult(
            metric_type=MetricType.DIVERSITY,
            metric_name="Question Diversity",
            score=diversity_score,
            details=diversity_details,
            timestamp=datetime.utcnow().isoformat()
        ))

        # Cognitive fairness
        fairness_score, fairness_details = self.fairness_evaluator.evaluate_cognitive_fairness(questions)
        metrics.append(MetricResult(
            metric_type=MetricType.FAIRNESS,
            metric_name="Cognitive Fairness (Bloom's)",
            score=fairness_score,
            details=fairness_details,
            timestamp=datetime.utcnow().isoformat()
        ))

        # Difficulty fairness
        difficulty_fairness_score, difficulty_details = self.fairness_evaluator.evaluate_difficulty_fairness(questions)
        metrics.append(MetricResult(
            metric_type=MetricType.FAIRNESS,
            metric_name="Difficulty Fairness",
            score=difficulty_fairness_score,
            details=difficulty_details,
            timestamp=datetime.utcnow().isoformat()
        ))

        # Calculate overall score
        overall_score = (diversity_score + fairness_score + difficulty_fairness_score) / 3

        # Recommendations
        recommendations = []
        if diversity_score < 0.7:
            recommendations.append("Increase question diversity - some questions are too similar")
        if fairness_score < 0.7:
            recommendations.append("Balance Bloom's taxonomy levels more evenly across questions")
        if difficulty_fairness_score < 0.7:
            recommendations.append("Adjust difficulty distribution to match MTech standards (20%-50%-30%)")

        return EvaluationReport(
            evaluation_id=f"eval_{paper_id}_{datetime.utcnow().isoformat()}",
            evaluation_type="paper",
            content_id=paper_id,
            metrics=metrics,
            overall_score=overall_score,
            evaluation_timestamp=datetime.utcnow().isoformat(),
            recommendations=recommendations
        )


# Singleton instance
_metrics_calculator = None


def get_metrics_calculator() -> MetricsCalculator:
    """Get or create metrics calculator."""
    global _metrics_calculator
    if _metrics_calculator is None:
        _metrics_calculator = MetricsCalculator()
    return _metrics_calculator
