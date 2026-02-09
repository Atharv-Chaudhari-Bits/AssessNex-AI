"""
Multi-tier Validation System for Generated Questions and Papers.

Provides semantic validation, plagiarism detection, originality scoring,
and grammar correction for educational content.
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from backend.app.utils.logger import get_logger
from backend.app.schemas.bloom_taxonomy import ValidationMetadata

logger = get_logger(__name__)


class SemanticValidator:
    """Validates semantic correctness of questions."""

    # Patterns for common semantic issues
    AMBIGUOUS_PATTERNS = [
        r'(?:which|what)\s+(?:of\s+)?(?:the\s+)?(?:following|below)',  # Vague reference
        r'etc\.',  # Incomplete lists
        r'and/or',  # Unclear logical operators
    ]

    INCOMPLETE_PATTERNS = [
        r'^\s*\.\.\.',  # Starts with ellipsis
        r'\.\.\.\s*$',  # Ends with ellipsis
        r'(?<!\w)X\s+(?:and|or)\s+Y(?!\w)',  # Generic placeholder
    ]

    TECHNICAL_ISSUE_PATTERNS = [
        r'undefined\s+(?:variable|function|class)',
        r'(?:incorrect|wrong)\s+syntax',
        r'(?:missing|forgot)\s+(?:import|definition)',
    ]

    def __init__(self):
        """Initialize semantic validator."""
        self.compiled_patterns = {
            'ambiguous': [re.compile(p, re.IGNORECASE) for p in self.AMBIGUOUS_PATTERNS],
            'incomplete': [re.compile(p, re.IGNORECASE) for p in self.INCOMPLETE_PATTERNS],
            'technical': [re.compile(p, re.IGNORECASE) for p in self.TECHNICAL_ISSUE_PATTERNS],
        }

    def validate_question_text(self, question_text: str) -> Tuple[bool, List[str]]:
        """
        Validate question text for semantic issues.

        Args:
            question_text: The question text to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check length
        if len(question_text.strip()) < 10:
            issues.append("Question text too short (< 10 characters)")

        if len(question_text.strip()) > 2000:
            issues.append("Question text too long (> 2000 characters)")

        # Check for ambiguity
        for pattern in self.compiled_patterns['ambiguous']:
            if pattern.search(question_text):
                issues.append(f"Ambiguous phrasing detected")
                break

        # Check for incompleteness
        for pattern in self.compiled_patterns['incomplete']:
            if pattern.search(question_text):
                issues.append(f"Incomplete statement detected")
                break

        # Check for technical issues
        for pattern in self.compiled_patterns['technical']:
            if pattern.search(question_text):
                issues.append(f"Technical correctness issue detected")
                break

        # Check for clarity (multiple consecutive punctuation)
        if re.search(r'[?!.]{2,}', question_text):
            issues.append("Multiple consecutive punctuation marks")

        # Check for unmatched brackets
        if question_text.count('(') != question_text.count(')'):
            issues.append("Unmatched parentheses")

        if question_text.count('[') != question_text.count(']'):
            issues.append("Unmatched square brackets")

        return len(issues) == 0, issues

    def validate_answer_key(self, answer: str, question_type: str) -> Tuple[bool, List[str]]:
        """
        Validate answer key completeness.

        Args:
            answer: The answer key
            question_type: Type of question

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if not answer or not answer.strip():
            issues.append(f"Answer key is empty")
            return False, issues

        # Type-specific validation
        if question_type in ["Multiple Choice", "True/False"]:
            if len(answer.strip()) > 100:
                issues.append("Answer too long for multiple choice")

        elif question_type in ["Short Answer", "Long Answer"]:
            if len(answer.strip()) < 20:
                issues.append("Answer key too brief for this question type")

        elif question_type == "Code Implementation":
            if 'def ' not in answer and 'function' not in answer.lower():
                issues.append("Code answer should contain function definition")

        return len(issues) == 0, issues


class PlagiarismDetector:
    """Detects plagiarism in generated content."""

    def __init__(self):
        """Initialize plagiarism detector."""
        # Store reference database (can be extended with real plagiarism API)
        self.reference_db = set()
        logger.info("PlagiarismDetector initialized")

    def add_reference_text(self, text: str):
        """Add reference text to database."""
        # Simple implementation - can be extended with hashing, n-grams, etc.
        self.reference_db.add(self._normalize_text(text))

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        return ' '.join(text.lower().split())

    def check_plagiarism(self, text: str, source: Optional[str] = None) -> float:
        """
        Check plagiarism score for text.

        Args:
            text: Text to check for plagiarism
            source: Optional source identifier

        Returns:
            float: Plagiarism score (0=original, 1=plagiarized)
        """
        normalized = self._normalize_text(text)

        # Simple exact match check (can be extended with fuzzy matching)
        if normalized in self.reference_db:
            return 1.0

        # Check for substring matches
        for ref in self.reference_db:
            similarity = self._string_similarity(normalized, ref)
            if similarity > 0.9:  # Very high similarity
                return 0.95

        # Default: assume original (0.0 score)
        # In production, integrate with real plagiarism detection API
        return 0.0

    @staticmethod
    def _string_similarity(s1: str, s2: str) -> float:
        """Calculate simple string similarity using Levenshtein ratio."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()


class OriginalityScorer:
    """Scores originality and uniqueness of questions."""

    def __init__(self):
        """Initialize originality scorer."""
        self.generated_questions = []
        logger.info("OriginalityScorer initialized")

    def score_originality(self, question_text: str, similar_questions: Optional[List[str]] = None) -> float:
        """
        Score originality of a question.

        Args:
            question_text: The question text to score
            similar_questions: Optional list of similar/reference questions

        Returns:
            float: Originality score (0=generic, 1=novel)
        """
        base_score = 1.0

        # Check against previously generated questions
        for prev_q in self.generated_questions:
            similarity = self._calculate_similarity(question_text, prev_q)
            if similarity > 0.85:  # High similarity
                base_score = max(0.0, base_score - 0.3)

        # Check against similar questions if provided
        if similar_questions:
            for sim_q in similar_questions:
                similarity = self._calculate_similarity(question_text, sim_q)
                if similarity > 0.8:
                    base_score = max(0.0, base_score - 0.2)

        # Reward novelty patterns
        novel_patterns = self._detect_novel_patterns(question_text)
        base_score = min(1.0, base_score + len(novel_patterns) * 0.05)

        self.generated_questions.append(question_text)
        return round(base_score, 3)

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    @staticmethod
    def _detect_novel_patterns(text: str) -> List[str]:
        """Detect novel/unique patterns in question."""
        patterns = []

        # Check for specific technical terms
        if re.search(r'\b(?:algorithm|optimization|heuristic|approximation)\b', text, re.IGNORECASE):
            patterns.append("algorithm_focus")

        # Check for complex scenarios
        if re.search(r'\b(?:scenario|case study|real-world|practical)\b', text, re.IGNORECASE):
            patterns.append("scenario_based")

        # Check for multi-step problems
        if text.count('.') >= 3:
            patterns.append("multi_step")

        return patterns


class GrammarChecker:
    """Checks and scores grammatical quality of text."""

    def __init__(self):
        """Initialize grammar checker."""
        # Common grammar patterns and issues
        self.grammar_patterns = {
            'subject_verb_agreement': r'\b(is|are|was|were)\s+(?:the\s+)?(\w+)s?\b',
            'article_usage': r'\b(?:a(?!\s+[aeiou]))\s+[aeiou]',  # 'a' before vowel
            'double_spacing': r'\s{2,}',
            'comma_splice': r'\w+,\s+\w+,\s+\w+',  # Multiple items without 'and'
        }
        logger.info("GrammarChecker initialized")

    def check_grammar(self, text: str) -> Tuple[float, List[str]]:
        """
        Check grammar and score quality.

        Args:
            text: Text to check

        Returns:
            Tuple of (quality_score, list_of_issues)
        """
        issues = []
        score = 1.0

        # Check for double spacing
        if re.search(self.grammar_patterns['double_spacing'], text):
            issues.append("Double spacing detected")
            score -= 0.1

        # Check for basic punctuation
        if not text.rstrip().endswith(('?', '.', '!')):
            issues.append("Missing ending punctuation")
            score -= 0.05

        # Check for proper capitalization
        if text[0].isupper():
            pass  # Good
        else:
            issues.append("Question should start with capital letter")
            score -= 0.05

        # Check for mixed tense (simple check)
        tenses = re.findall(r'\b(?:is|are|was|were|have|has|do|does|did)\b', text, re.IGNORECASE)
        if tenses:
            # Very basic check - in production use proper NLP
            pass

        # Check for readability (not too short, not too long per sentence)
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 40:
                issues.append(f"Sentence too long (>{40} words)")
                score -= 0.1

        return round(max(0.0, score), 3), issues


class MultiTierValidator:
    """
    Comprehensive multi-tier validation system.

    Combines semantic, plagiarism, originality, and grammar validation.
    """

    def __init__(self):
        """Initialize multi-tier validator."""
        self.semantic_validator = SemanticValidator()
        self.plagiarism_detector = PlagiarismDetector()
        self.originality_scorer = OriginalityScorer()
        self.grammar_checker = GrammarChecker()
        logger.info("MultiTierValidator initialized with all sub-validators")

    def validate_question(
        self,
        question_text: str,
        answer_key: str,
        question_type: str,
        similar_questions: Optional[List[str]] = None,
    ) -> ValidationMetadata:
        """
        Perform comprehensive validation of a question.

        Args:
            question_text: The question text
            answer_key: The answer key
            question_type: Type of question
            similar_questions: Optional list of similar questions for comparison

        Returns:
            ValidationMetadata with complete validation results
        """
        # Semantic validation
        semantic_valid, semantic_issues = self.semantic_validator.validate_question_text(question_text)
        answer_valid, answer_issues = self.semantic_validator.validate_answer_key(answer_key, question_type)

        # Plagiarism check
        plagiarism_score = self.plagiarism_detector.check_plagiarism(question_text)

        # Originality scoring
        originality_score = self.originality_scorer.score_originality(question_text, similar_questions)

        # Grammar checking
        grammar_score, grammar_issues = self.grammar_checker.check_grammar(question_text)

        # Calculate clarity score (based on semantic and grammar)
        clarity_score = (1.0 - len(semantic_issues) * 0.1) * grammar_score

        # Overall quality score
        overall_score = (
            (plagiarism_score * 0.0 +  # Lower plagiarism is better (0 is good)
             originality_score * 0.4 +   # Originality is important
             grammar_score * 0.3 +       # Grammar matters
             clarity_score * 0.3)        # Clarity is critical
        )

        all_issues = semantic_issues + answer_issues + grammar_issues

        return ValidationMetadata(
            semantic_validity=semantic_valid and answer_valid,
            semantic_issues=all_issues,
            plagiarism_score=plagiarism_score,
            originality_score=originality_score,
            grammatical_quality=grammar_score,
            clarity_score=clarity_score,
            overall_quality_score=round(overall_score, 3),
            validation_timestamp=datetime.utcnow().isoformat(),
        )

    def validate_paper(self, paper_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate entire question paper for consistency and diversity.

        Args:
            paper_questions: List of questions in the paper

        Returns:
            Dict with validation results for the paper
        """
        validation_results = []
        diversity_issues = []
        question_texts = []

        # Validate individual questions
        for i, question in enumerate(paper_questions):
            q_text = question.get('question_text', '')
            answer = question.get('expected_answer', '')
            q_type = question.get('question_type', '')

            validation = self.validate_question(q_text, answer, q_type, question_texts)
            validation_results.append({
                'question_number': i + 1,
                'validation': validation
            })
            question_texts.append(q_text)

        # Check for diversity (avoid too similar questions)
        from difflib import SequenceMatcher
        for i, q1 in enumerate(question_texts):
            for j, q2 in enumerate(question_texts[i+1:], start=i+1):
                similarity = SequenceMatcher(None, q1.lower(), q2.lower()).ratio()
                if similarity > 0.8:
                    diversity_issues.append(
                        f"Questions {i+1} and {j+1} are very similar ({similarity:.1%})"
                    )

        # Calculate paper-level metrics
        valid_count = sum(1 for r in validation_results if r['validation'].semantic_validity)
        avg_quality = sum(r['validation'].overall_quality_score for r in validation_results) / len(validation_results)
        avg_originality = sum(r['validation'].originality_score for r in validation_results) / len(validation_results)

        return {
            'total_questions': len(paper_questions),
            'valid_questions': valid_count,
            'validity_percentage': (valid_count / len(paper_questions)) * 100,
            'average_quality_score': round(avg_quality, 3),
            'average_originality_score': round(avg_originality, 3),
            'diversity_issues': diversity_issues,
            'individual_validations': validation_results,
            'validation_timestamp': datetime.utcnow().isoformat(),
        }


# Singleton instance
_validator_instance = None


def get_validator() -> MultiTierValidator:
    """Get or create multi-tier validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = MultiTierValidator()
    return _validator_instance
