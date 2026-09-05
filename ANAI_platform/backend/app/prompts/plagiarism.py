"""Prompt used by the optional plagiarism checker."""

PLAGIARISM_CHECK_PROMPT = """
FOR CHECKING PLAGIARISM/UNIQUENESS OF QUESTIONS:

ANALYSIS TASK:
Analyze the given question(s) and compare against a reference database
to detect similarity and uniqueness scores.

INPUT FORMAT:
{
    "current_question": {
        "text": "What is the difference between supervised and unsupervised learning?",
        "question_type": "Short Answer",
        "subject": "Machine Learning",
        "difficulty": "Easy"
    },
    "reference_questions": [
        {
            "id": "q001",
            "text": "Explain supervised vs unsupervised learning",
            "question_type": "Short Answer",
            "subject": "Machine Learning",
            "difficulty": "Easy"
        },
        {
            "id": "q002",
            "text": "Discuss different types of machine learning algorithms",
            "question_type": "Essay",
            "subject": "Machine Learning",
            "difficulty": "Medium"
        }
    ]
}

OUTPUT FORMAT:
{
    "uniqueness_score": 0.75,  // 0-1, higher = more unique
    "plagiarism_score": 0.25,  // 0-1, higher = more plagiarism
    "similarity_matches": [
        {
            "reference_id": "q001",
            "similarity_score": 0.85,
            "similarity_type": "semantic_similarity",
            "overlapping_concepts": ["supervised learning", "unsupervised learning"],
            "confidence": 0.9
        }
    ],
    "is_plagiarized": false,
    "plagiarism_threshold_exceeded": false,
    "recommendations": [
        "Question is unique enough (75% uniqueness)",
        "Core concepts overlap with reference question q001",
        "Consider rephrasing to increase uniqueness"
    ],
    "detailed_analysis": {
        "concept_overlap": 0.25,  // 0-1
        "wording_similarity": 0.15,  // 0-1
        "structure_similarity": 0.10,  // 0-1
        "overall_similarity": 0.25  // Weighted average
    }
}

PLAGIARISM THRESHOLD:
- Plagiarism Threshold: 0.70 (70% similar = likely plagiarized)
- Minimum Uniqueness for Acceptance: 0.50 (50% unique minimum)

ANALYSIS CRITERIA:
1. Semantic similarity (concepts, keywords)
2. Structural similarity (question format, structure)
3. Wording similarity (phrasing, vocabulary)
4. Context similarity (subject, difficulty level)

IMPORTANT:
- Questions should be flagged if similarity > 0.70
- Consider subject area context
- Trivial question pairs might naturally have higher similarity
- Report both exact and semantic matches
"""

__all__ = ["PLAGIARISM_CHECK_PROMPT"]
