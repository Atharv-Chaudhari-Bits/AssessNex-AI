"""
Question Paper Generation prompts and templates.

For creating balanced, mixed question papers with specified
difficulty distributions and question type mixtures.
"""

QUESTION_PAPER_GENERATION = """
For Question Paper Generation:

PURPOSE:
Generate a complete question paper with:
- Mix of question types
- Specific difficulty percentage distribution
- Total duration and marks
- Balanced concept coverage

PAPER SPECIFICATION INPUT:
{
    "subject": "Machine Learning",
    "total_questions": 10,
    "total_marks": 100,
    "duration_minutes": 120,
    "difficulty_distribution": {
        "Easy": 30,          # 30% easy questions
        "Medium": 50,        # 50% medium questions
        "Hard": 20           # 20% hard questions
    },
    "question_type_distribution": {
        "Multiple Choice": 40,
        "Short Answer": 30,
        "Programming": 20,
        "Essay": 10
    },
    "topics_to_cover": [
        "Supervised Learning",
        "Unsupervised Learning",
        "Neural Networks",
        "Model Evaluation"
    ],
    "marks_per_type": {
        "Multiple Choice": 2,
        "Short Answer": 5,
        "Programming": 15,
        "Essay": 10
    }
}

OUTPUT STRUCTURE:
{
    "paper": {
        "title": "Machine Learning - Final Exam",
        "subject": "Machine Learning",
        "duration_minutes": 120,
        "total_marks": 100,
        "instructions": [
            "All questions are compulsory",
            "Multiple choice: Each correct answer is 2 marks",
            ...
        ],
        "sections": [
            {
                "section_name": "Section A: Multiple Choice",
                "questions": [...],
                "marks": 20,
                "instructions": "Choose the correct answer"
            },
            {
                "section_name": "Section B: Short Answer",
                "questions": [...],
                "marks": 30,
                "instructions": "Answer in 2-3 sentences"
            },
            ...
        ]
    },
    "answer_key": [...],
    "distribution_analysis": {
        "difficulty_actual": {...},
        "type_actual": {...},
        "topics_covered": [...]
    }
}
"""

BALANCED_PAPER_TEMPLATE = """
BALANCED QUESTION PAPER GENERATION:

CONSTRAINTS TO SATISFY:
1. Difficulty Distribution
   - Easy questions should test basic concepts
   - Medium questions should require application
   - Hard questions should require synthesis/analysis

2. Topic Coverage
   - All specified topics must be covered
   - Distribution should be proportional if specified
   - Avoid repetition of same topic

3. Question Type Mix
   - Variety in question types
   - Each type should have diverse sub-types
   - Mix theoretical and practical questions

4. Time Management
   - Allocate marks appropriately
   - Ensure questions fit within time limit
   - Consider reading and thinking time

ALGORITHM FOR BALANCED GENERATION:
1. Calculate questions needed per category
   - questions_per_difficulty = total_questions * difficulty_percent
   - questions_per_type = total_questions * type_percent

2. For each category combination:
   - Generate question of that difficulty and type
   - Ensure topic diversity
   - Validate marks allocation

3. Arrange questions:
   - Group by difficulty (typically Easy -> Hard)
   - Or group by type (typically MCQ -> Essay)
   - Add clear section markers

4. Validate:
   - Sum of marks = total_marks
   - Distribution matches specification
   - All topics covered
   - Logical question ordering
"""

PAPER_ARRANGEMENT_STRATEGIES = """
STRATEGIES FOR ARRANGING QUESTIONS:

Strategy 1 - Difficulty Progression:
Section 1: Easy questions (warm up)
Section 2: Medium questions (main content)
Section 3: Hard questions (challenge)
Benefit: Students build confidence gradually

Strategy 2 - Question Type Grouping:
Section 1: Multiple Choice (quick, objective)
Section 2: Short Answer (conceptual)
Section 3: Problems (application)
Section 4: Essay (analysis)
Benefit: Students can change thinking mode per section

Strategy 3 - Topic-Based Organization:
Section 1: Topic A (multiple question types)
Section 2: Topic B (multiple question types)
Section 3: Topic C (multiple question types)
Benefit: Logical flow for topic coverage

Strategy 4 - Mixed (Recommended for MTech):
Early Easy Questions (MCQ, short): Build confidence
Progressive Medium Questions: Core concepts
Focused Hard Questions: Synthesis and application
Final Essay/Programming: Comprehensive understanding
"""

ANSWER_KEY_GENERATION = """
FOR GENERATING ANSWER KEY:

STRUCTURE:
{
    "question_number": 1,
    "answer": "B",  // For MCQ
    "marks": 2,
    "explanation": "...",
    "common_mistakes": [
        "Option A chosen by students who confuse X with Y",
        "Option C chosen due to incomplete understanding"
    ],
    "alternative_answers": [],  // If applicable
    "marking_rubric": null  // For subjective questions
}

FOR SUBJECTIVE QUESTIONS:
{
    "question_number": 5,
    "marks": 5,
    "marking_rubric": {
        "Identifies main concept": 1,
        "Provides correct formula": 1,
        "Applies concept correctly": 1,
        "Clear explanation": 1,
        "Example or derivation": 1
    },
    "model_answer": "...",
    "expected_components": [
        "Definition of regularization",
        "Formula for L1/L2",
        "Difference explanation",
        "Use case example"
    ]
}
"""

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

# Dictionary for paper generation
PAPER_GENERATION_TYPES = {
    "basic_specification": QUESTION_PAPER_GENERATION,
    "balanced_algorithm": BALANCED_PAPER_TEMPLATE,
    "arrangement_strategies": PAPER_ARRANGEMENT_STRATEGIES,
    "answer_key": ANSWER_KEY_GENERATION,
}

# Dictionary for advanced features
ADVANCED_TYPES = {
    "paper_generation": QUESTION_PAPER_GENERATION,
    "plagiarism_check": PLAGIARISM_CHECK_PROMPT,
}
