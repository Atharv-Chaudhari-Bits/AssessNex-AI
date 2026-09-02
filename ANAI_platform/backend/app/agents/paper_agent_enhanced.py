"""
Enhanced Question Paper Generation Agent using LangGraph.

Robust multi-step workflow for generating complete question papers.
Reuses question generation facility and integrates advanced features:
- Bloom's taxonomy alignment
- Multi-tier validation
- Explainability logging
- Metrics evaluation
- Dynamic templates
"""

import asyncio
import json
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated, Union
from dataclasses import dataclass, field
from enum import Enum
import operator

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
# Replace this:
from langgraph.graph import StateGraph, END

# With this:
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    from langgraph.graph import StateGraph, END as EndNode
    END = EndNode

from langgraph.checkpoint.memory import MemorySaver

from backend.app.config import settings
from backend.app.utils.logger import get_logger
from backend.app.agents.question_generator import QuestionGenerationAgent
from backend.app.schemas.bloom_taxonomy import (
    BloomLevel, QUESTION_TYPE_BLOOM_MAPPING, BLOOM_DIFFICULTY_WEIGHTS,
    DOMAIN_ONTOLOGIES
)
from backend.app.utils.validation import get_validator
from backend.app.utils.explainability import (
    get_explainability_logger, GenerationDecision, DecisionType
)
from backend.app.utils.metrics import get_metrics_calculator
from pydantic import BaseModel, field_validator

logger = get_logger(__name__)


class PaperSection(TypedDict):
    """Section of a question paper"""
    section_id: str
    title: str
    instructions: str
    question_type: str
    num_questions: int
    marks_per_question: int
    bloom_levels: List[str]  # Bloom's taxonomy levels for this section
    questions: List[Dict]


class PaperState(TypedDict):
    """State for paper generation workflow"""
    # Input configuration
    subject: str
    topic: str
    subtopics: List[str]
    difficulty_distribution: Dict[str, int]
    question_type_config: List[Dict]
    bloom_distribution: Dict[str, int]  # NEW: Bloom's taxonomy distribution
    total_marks: int
    duration_minutes: int
    exam_name: str
    instructions: Optional[Union[str, List[str]]] = None
    diversity_seed: str
    
    # Processing state
    current_step: str
    current_section_idx: int
    messages: Annotated[List[Any], operator.add]
    errors: List[str]
    retry_count: int
    
    # Generated content
    sections: List[Dict]
    header_info: Dict
    
    # Validation and metrics
    validation_results: List[Dict]
    metrics_results: Dict
    
    # Output
    paper: Optional[Dict]
    status: str

    @field_validator("instructions", mode="before")
    @classmethod
    def normalize_instructions(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]          # 👈 STRING → LIST
        return v

class QuestionPaperAgent:
    """
    Advanced Question Paper Generation Agent.
    
    Features:
    - Reuses QuestionGenerationAgent for all questions
    - Bloom's taxonomy alignment
    - Multi-tier validation
    - Explainability logging
    - Metrics evaluation
    - Dynamic question distribution
    """

    def __init__(self):
        """Initialize the paper generation agent."""
        self.question_generator = QuestionGenerationAgent()
        self.validator = get_validator()
        self.explainability_logger = get_explainability_logger()
        self.metrics_calculator = get_metrics_calculator()
        self.llm = AzureChatOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_DEPLOYMENT,
            temperature=0.7,
            max_tokens=2048,
        )
        self.memory = MemorySaver()
        self.workflow = self._build_workflow()
        
        # Question type to Bloom's level mapping
        self.question_type_configs = {
            "Multiple Choice": {
                "marks": [1, 2],
                "time_per_question": 1.5,
                "bloom_levels": ["Remember", "Understand", "Apply"]
            },
            "Short Answer": {
                "marks": [2, 3, 4],
                "time_per_question": 4,
                "bloom_levels": ["Understand", "Apply", "Analyze"]
            },
            "Long Answer": {
                "marks": [5, 8, 10],
                "time_per_question": 10,
                "bloom_levels": ["Apply", "Analyze", "Evaluate", "Create"]
            },
            "Numerical Problem": {
                "marks": [3, 5],
                "time_per_question": 5,
                "bloom_levels": ["Apply", "Analyze"]
            },
            "Code Implementation": {
                "marks": [5, 10, 15],
                "time_per_question": 12,
                "bloom_levels": ["Apply", "Analyze", "Create"]
            },
            "Diagram Based": {
                "marks": [3, 5],
                "time_per_question": 5,
                "bloom_levels": ["Understand", "Apply", "Analyze"]
            },
            "True/False": {
                "marks": [1],
                "time_per_question": 1,
                "bloom_levels": ["Remember", "Understand"]
            },
            "Fill in the Blank": {
                "marks": [1, 2],
                "time_per_question": 1,
                "bloom_levels": ["Remember", "Understand"]
            },
        }
        
        logger.info("QuestionPaperAgent initialized with integrated validation and metrics")

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(PaperState)
        
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("generate_header", self._generate_header_node)
        workflow.add_node("plan_sections", self._plan_sections_node)
        workflow.add_node("generate_section", self._generate_section_node)
        workflow.add_node("validate_questions", self._validate_questions_node)
        workflow.add_node("generate_answer_key", self._generate_answer_key_node)
        workflow.add_node("evaluate_metrics", self._evaluate_metrics_node)
        workflow.add_node("finalize", self._finalize_node)
        
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "generate_header")
        workflow.add_edge("generate_header", "plan_sections")
        workflow.add_edge("plan_sections", "generate_section")
        
        workflow.add_conditional_edges(
            "generate_section",
            self._route_after_section,
            {
                "next_section": "generate_section",
                "validate": "validate_questions",
                "error": "finalize"
            }
        )
        
        workflow.add_edge("validate_questions", "generate_answer_key")
        workflow.add_edge("generate_answer_key", "evaluate_metrics")
        workflow.add_edge("evaluate_metrics", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile(checkpointer=self.memory)

    def _route_after_section(self, state: PaperState) -> str:
        """Route after generating a section"""
        if state.get("errors"):
            return "error"
        
        current_idx = state.get("current_section_idx", 0)
        total_sections = len(state.get("question_type_config", []))
        
        if current_idx < total_sections:
            return "next_section"
        return "validate"

    async def _initialize_node(self, state: PaperState) -> Dict:
        """Initialize paper generation"""
        logger.info(f"Initializing paper generation for {state['subject']} - {state['topic']}")
        
        # Start explainability session
        session_id = self.explainability_logger.start_generation_session(
            "paper_generation"
        )
        
        diversity_seed = state.get("diversity_seed") or self._generate_diversity_seed()
        
        return {
            "current_step": "initialized",
            "current_section_idx": 0,
            "diversity_seed": diversity_seed,
            "sections": [],
            "messages": [{"role": "system", "content": f"Starting paper generation (session: {session_id})"}],
            "status": "in_progress",
            "validation_results": [],
            "metrics_results": {}
        }

    async def _generate_header_node(self, state: PaperState) -> Dict:
        """Generate paper header information"""
        logger.info("Generating paper header")
        
        header_info = {
            "exam_name": state.get("exam_name", f"{state['subject']} Examination"),
            "subject": state["subject"],
            "topic": state["topic"],
            "total_marks": state["total_marks"],
            "duration": f"{state['duration_minutes']} minutes",
            "date": datetime.now().strftime("%B %d, %Y"),
            "instructions": state.get("instructions", [
                "Answer all questions.",
                "Write clearly and legibly.",
                "Show all working for problems.",
                "Marks are indicated against each question."
            ])
        }
        
        return {
            "header_info": header_info,
            "current_step": "header_generated",
            "messages": [{"role": "assistant", "content": "Paper header generated"}]
        }

    async def _plan_sections_node(self, state: PaperState) -> Dict:
        """Plan paper sections based on question type config and Bloom distribution"""
        logger.info("Planning paper sections with Bloom's taxonomy alignment")
        
        question_configs = state.get("question_type_config", [])
        bloom_distribution = state.get("bloom_distribution", {
            "Remember": 10, "Understand": 25, "Apply": 30,
            "Analyze": 20, "Evaluate": 10, "Create": 5
        })
        
        if not question_configs:
            question_configs = self._create_default_sections(
                state["total_marks"],
                state["duration_minutes"]
            )
        
        sections_plan = []
        section_labels = ["A", "B", "C", "D", "E", "F"]
        
        for i, config in enumerate(question_configs):
            q_type = config.get("type", "Multiple Choice")
            num_q = config.get("count", 5)
            marks = config.get("marks_each", 2)
            
            # Get appropriate Bloom levels for this question type
            allowed_bloom_levels = QUESTION_TYPE_BLOOM_MAPPING.get(q_type, [])
            
            sections_plan.append({
                "section_id": section_labels[i] if i < len(section_labels) else f"Section_{i+1}",
                "title": f"Section {section_labels[i]}: {q_type}" if i < len(section_labels) else f"Section {i+1}: {q_type}",
                "question_type": q_type,
                "num_questions": num_q,
                "marks_per_question": marks,
                "total_marks": num_q * marks,
                "bloom_levels": allowed_bloom_levels,
                "instructions": self._get_section_instructions(q_type),
                "questions": []
            })
        
        return {
            "question_type_config": question_configs,
            "bloom_distribution": bloom_distribution,
            "current_step": "sections_planned",
            "messages": [{"role": "assistant", "content": f"Planned {len(sections_plan)} sections with Bloom's alignment"}]
        }

    async def _generate_section_node(self, state: PaperState) -> Dict:
        """Generate questions for current section using QuestionGenerationAgent"""
        current_idx = state.get("current_section_idx", 0)
        question_configs = state.get("question_type_config", [])
        bloom_distribution = state.get("bloom_distribution", {})
        
        if current_idx >= len(question_configs):
            return {"current_step": "all_sections_generated"}
        
        config = question_configs[current_idx]
        q_type = config.get("type", "Multiple Choice")
        num_questions = config.get("count", 5)
        difficulty = config.get("difficulty", "medium")
        
        logger.info(f"Generating section {current_idx + 1}: {q_type} ({num_questions} questions)")
        
        # Determine Bloom levels for this section
        allowed_bloom_levels = QUESTION_TYPE_BLOOM_MAPPING.get(q_type, [])
        
        # Generate questions using QuestionGenerationAgent (REUSE!)
        section_questions = []
        question_number = self._get_starting_question_number(state.get("sections", []))
        
        try:
            # Use question_generator to create questions
            questions = self.question_generator.generate_questions(
                subject=state["subject"],
                question_type=q_type,
                difficulty_level=difficulty,
                num_questions=num_questions,
                additional_context=f"Topic: {state.get('topic', '')}. Subtopics: {', '.join(state.get('subtopics', []))}"
            )
            
            # Enrich with Bloom level and metadata
            for j, q in enumerate(questions):
                # Assign Bloom level based on difficulty and question type
                bloom_level = self._select_bloom_level(difficulty, allowed_bloom_levels, j, num_questions)
                
                q["question_number"] = question_number
                q["marks"] = config.get("marks_each", 2)
                q["bloom_level"] = bloom_level
                q["cognitive_complexity"] = BLOOM_DIFFICULTY_WEIGHTS.get(bloom_level, 1.5)
                
                section_questions.append(q)
                question_number += 1
            
            # Log Bloom distribution decision
            decision = GenerationDecision(
                decision_type=DecisionType.BLOOM_LEVEL_SELECTION,
                description=f"Selected Bloom levels for {q_type}: {[q.get('bloom_level') for q in section_questions]}",
                input_params={"question_type": q_type, "num_questions": num_questions},
                output_params={"bloom_levels": [q.get('bloom_level') for q in section_questions]},
                reasoning=f"Based on {q_type} allowed Bloom levels and difficulty '{difficulty}'",
                confidence_score=0.95,
                timestamp=datetime.utcnow().isoformat()
            )
            self.explainability_logger.log_difficulty_calibration(
                base_difficulty=difficulty,
                adjusted_difficulty=difficulty,
                bloom_level=str([q.get('bloom_level') for q in section_questions]),
                reasoning="Calibrated using question type constraints",
                confidence=0.95
            )
                
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return {"errors": [str(e)], "current_step": "generation_error"}
        
        # Create section
        section_labels = ["A", "B", "C", "D", "E", "F"]
        section = {
            "section_id": section_labels[current_idx] if current_idx < len(section_labels) else f"Section_{current_idx+1}",
            "title": f"Section {section_labels[current_idx]}: {q_type}" if current_idx < len(section_labels) else f"Section {current_idx+1}: {q_type}",
            "question_type": q_type,
            "num_questions": len(section_questions),
            "marks_per_question": config.get("marks_each", 2),
            "total_marks": len(section_questions) * config.get("marks_each", 2),
            "instructions": self._get_section_instructions(q_type),
            "questions": section_questions
        }
        
        sections = state.get("sections", []).copy()
        sections.append(section)
        
        return {
            "sections": sections,
            "current_section_idx": current_idx + 1,
            "current_step": f"section_{current_idx + 1}_generated",
            "messages": [{"role": "assistant", "content": f"Generated {len(section_questions)} questions for {q_type}"}]
        }

    async def _validate_questions_node(self, state: PaperState) -> Dict:
        """Validate all generated questions"""
        logger.info("Validating all generated questions")
        
        validation_results = []
        
        for section in state.get("sections", []):
            for question in section.get("questions", []):
                # Use multi-tier validator
                validation = self.validator.validate_question(
                    question_text=question.get("question_text", ""),
                    answer_key=question.get("expected_answer", ""),
                    question_type=section.get("question_type", "")
                )
                
                validation_results.append({
                    "question_number": question.get("question_number"),
                    "validation": validation
                })
                
                # Log validation
                self.explainability_logger.log_validation_check(
                    question.get("id", "unknown"),
                    {
                        "semantic_validity": validation.semantic_validity,
                        "quality_score": validation.overall_quality_score,
                        "issues": validation.semantic_issues
                    }
                )
        
        # Validate entire paper
        all_questions = []
        for section in state.get("sections", []):
            all_questions.extend(section.get("questions", []))
        
        paper_validation = self.validator.validate_paper(all_questions)
        
        logger.info(f"Validation complete: {paper_validation['valid_questions']}/{paper_validation['total_questions']} questions valid")
        
        return {
            "validation_results": validation_results,
            "current_step": "questions_validated",
            "messages": [{"role": "assistant", "content": f"Validated {len(all_questions)} questions"}]
        }

    async def _generate_answer_key_node(self, state: PaperState) -> Dict:
        """Generate answer key and marking scheme"""
        logger.info("Generating answer key and marking scheme")
        
        answer_key = []
        
        for section in state.get("sections", []):
            section_answers = {
                "section_id": section["section_id"],
                "section_title": section["title"],
                "answers": []
            }
            
            for q in section.get("questions", []):
                answer_entry = {
                    "question_number": q.get("question_number"),
                    "answer": q.get("expected_answer", ""),
                    "marks": q.get("marks", 2),
                    "bloom_level": q.get("bloom_level", "Unknown")
                }
                
                if q.get("explanation"):
                    answer_entry["explanation"] = q["explanation"]
                
                if section["question_type"] in ["Short Answer", "Long Answer", "Code Implementation"]:
                    answer_entry["marking_scheme"] = self._generate_marking_points(q)
                
                section_answers["answers"].append(answer_entry)
            
            answer_key.append(section_answers)
        
        header_info = state.get("header_info", {}).copy()
        header_info["answer_key"] = answer_key
        
        return {
            "header_info": header_info,
            "current_step": "answer_key_generated",
            "messages": [{"role": "assistant", "content": "Answer key generated"}]
        }

    async def _evaluate_metrics_node(self, state: PaperState) -> Dict:
        """Evaluate paper using metrics calculator"""
        logger.info("Evaluating paper metrics")
        
        all_questions = []
        for section in state.get("sections", []):
            all_questions.extend(section.get("questions", []))
        
        # Evaluate paper
        evaluation = self.metrics_calculator.evaluate_paper(
            f"paper_{datetime.utcnow().isoformat()}",
            all_questions
        )
        
        metrics_results = evaluation.to_dict()
        
        logger.info(f"Paper evaluation: Overall Score = {evaluation.overall_score:.3f}")
        logger.info(f"Recommendations: {evaluation.recommendations}")
        
        return {
            "metrics_results": metrics_results,
            "current_step": "metrics_evaluated",
            "messages": [{"role": "assistant", "content": "Paper metrics evaluated"}]
        }

    async def _finalize_node(self, state: PaperState) -> Dict:
        """Finalize the question paper"""
        logger.info("Finalizing question paper")
        
        # Construct final paper
        paper = {
            "paper_id": f"paper_{datetime.utcnow().isoformat()}",
            "header": state.get("header_info", {}),
            "sections": state.get("sections", []),
            "validation_summary": {
                "total_validations": len(state.get("validation_results", [])),
                "metrics": state.get("metrics_results", {})
            },
            "metadata": {
                "generation_time": datetime.utcnow().isoformat(),
                "status": "completed" if not state.get("errors") else "failed",
                "errors": state.get("errors", [])
            }
        }
        
        # End explainability session
        self.explainability_logger.end_generation_session(
            status="success" if not state.get("errors") else "failed",
            summary={
                "total_sections": len(state.get("sections", [])),
                "total_questions": sum(len(s.get("questions", [])) for s in state.get("sections", [])),
                "metrics_score": state.get("metrics_results", {}).get("overall_score", 0)
            }
        )
        
        return {
            "paper": paper,
            "current_step": "finalized",
            "status": "completed"
        }

    def _select_bloom_level(self, difficulty: str, allowed_levels: List[str], position: int, total: int) -> str:
        """
        Select appropriate Bloom level for a question.
        
        Args:
            difficulty: Base difficulty level
            allowed_levels: List of allowed Bloom levels for this question type
            position: Position of question in section
            total: Total questions in section
            
        Returns:
            str: Selected Bloom level
        """
        # Simple distribution: early questions easier, later questions harder
        if position < total * 0.3:
            # First 30%: lower Bloom levels
            filtered = [l for l in allowed_levels if l in [BloomLevel.REMEMBER.value, BloomLevel.UNDERSTAND.value]]
        elif position < total * 0.7:
            # Middle 40%: medium Bloom levels
            filtered = [l for l in allowed_levels if l in [BloomLevel.UNDERSTAND.value, BloomLevel.APPLY.value]]
        else:
            # Last 30%: higher Bloom levels
            filtered = [l for l in allowed_levels if l in [BloomLevel.ANALYZE.value, BloomLevel.EVALUATE.value, BloomLevel.CREATE.value]]
        
        # Fallback to allowed_levels if filtered is empty
        if not filtered:
            filtered = allowed_levels
        
        # Consider difficulty for finer adjustment
        if difficulty.lower() == "hard" and BloomLevel.CREATE.value in filtered:
            return BloomLevel.CREATE.value
        elif difficulty.lower() == "easy" and BloomLevel.REMEMBER.value in filtered:
            return BloomLevel.REMEMBER.value
        
        return filtered[0] if filtered else allowed_levels[0] if allowed_levels else "Apply"

    def _get_section_instructions(self, question_type: str) -> str:
        """Get instructions for a section based on question type"""
        instructions = {
            "Multiple Choice": "Select the correct option for each question.",
            "True/False": "Mark each statement as True or False.",
            "Short Answer": "Answer in 2-3 sentences.",
            "Long Answer": "Answer in detail (5-10 sentences or more).",
            "Numerical Problem": "Solve the numerical problems and show all working.",
            "Code Implementation": "Write code for the following problems. Include comments and handle edge cases.",
            "Diagram Based": "Study the diagram and answer the questions that follow.",
            "Fill in the Blank": "Fill in the blanks with appropriate terms."
        }
        return instructions.get(question_type, "Answer all questions in this section.")

    def _generate_diversity_seed(self) -> str:
        """Generate a seed for diversity in question generation"""
        return hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:8]

    def _create_default_sections(self, total_marks: int, duration_minutes: int) -> List[Dict]:
        """Create default section configuration"""
        return [
            {"type": "Multiple Choice", "count": int(total_marks / 20), "marks_each": 1, "difficulty": "mixed"},
            {"type": "Short Answer", "count": int(total_marks / 40), "marks_each": 4, "difficulty": "medium"},
            {"type": "Long Answer", "count": max(1, int(total_marks / 100)), "marks_each": 10, "difficulty": "hard"}
        ]

    def _get_starting_question_number(self, sections: List[Dict]) -> int:
        """Get the next question number"""
        total = 1
        for section in sections:
            total += len(section.get("questions", []))
        return total

    def _generate_marking_points(self, question: Dict) -> List[Dict]:
        """Generate marking scheme points for a question"""
        marks = question.get("marks", 2)
        
        points = []
        if marks >= 5:
            points = [
                {"criterion": "Understanding of concept", "marks": int(marks * 0.3)},
                {"criterion": "Correct approach/method", "marks": int(marks * 0.3)},
                {"criterion": "Accuracy of answer", "marks": int(marks * 0.25)},
                {"criterion": "Presentation/Clarity", "marks": marks - int(marks * 0.85)}
            ]
        else:
            points = [
                {"criterion": "Correct answer", "marks": marks}
            ]
        
        return points

    async def generate_paper(
        self,
        subject: str,
        topic: str,
        total_marks: int = 100,
        duration_minutes: int = 180,
        question_type_config: Optional[List[Dict]] = None,
        difficulty_distribution: Optional[Dict[str, int]] = None,
        bloom_distribution: Optional[Dict[str, int]] = None,
        exam_name: Optional[str] = None,
        subtopics: Optional[List[str]] = None,
        instructions: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a complete question paper with advanced features.
        
        Args:
            subject: Subject name
            topic: Main topic
            total_marks: Total marks (default: 100)
            duration_minutes: Duration in minutes (default: 180)
            question_type_config: Configuration for question types
            difficulty_distribution: Difficulty distribution percentages
            bloom_distribution: Bloom's taxonomy level distribution
            exam_name: Name of the examination
            subtopics: List of subtopics to cover
            instructions: Custom exam instructions
        
        Returns:
            Complete question paper dictionary
        """
        logger.info(f"Generating paper for {subject}/{topic} ({total_marks} marks, {duration_minutes} min)")
        
        # Default configurations
        if not question_type_config:
            question_type_config = [
                {"type": "Multiple Choice", "count": 10, "marks_each": 1, "difficulty": "mixed"},
                {"type": "Short Answer", "count": 5, "marks_each": 4, "difficulty": "medium"},
                {"type": "Long Answer", "count": 3, "marks_each": 10, "difficulty": "hard"}
            ]
        
        if not difficulty_distribution:
            difficulty_distribution = {"easy": 20, "medium": 50, "hard": 30}
        
        # NEW: Default Bloom distribution (higher-order thinking emphasized)
        if not bloom_distribution:
            bloom_distribution = {
                "Remember": 10,
                "Understand": 25,
                "Apply": 30,
                "Analyze": 20,
                "Evaluate": 10,
                "Create": 5
            }
        
        # Create initial state
        initial_state: PaperState = {
            "subject": subject,
            "topic": topic,
            "subtopics": subtopics or [],
            "difficulty_distribution": difficulty_distribution,
            "question_type_config": question_type_config,
            "bloom_distribution": bloom_distribution,
            "total_marks": total_marks,
            "duration_minutes": duration_minutes,
            "exam_name": exam_name or f"{subject} Examination",
            "instructions": instructions or [],
            "diversity_seed": self._generate_diversity_seed(),
            "current_step": "start",
            "current_section_idx": 0,
            "messages": [],
            "errors": [],
            "retry_count": 0,
            "sections": [],
            "header_info": {},
            "validation_results": [],
            "metrics_results": {},
            "paper": None,
            "status": "pending"
        }
        
        # Create unique thread ID
        thread_id = f"paper-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            if final_state.get("paper"):
                logger.info(f"Paper generated: {final_state['paper'].get('paper_id')}")
                return final_state["paper"]
            else:
                logger.error("Paper generation failed")
                return {"error": "Paper generation failed", "state": final_state.get("status")}
                
        except Exception as e:
            logger.error(f"Error in paper generation: {e}")
            return {"error": str(e)}


# Create singleton instance
_paper_agent_instance = None


def get_paper_agent() -> QuestionPaperAgent:
    """Get or create paper agent instance."""
    global _paper_agent_instance
    if _paper_agent_instance is None:
        _paper_agent_instance = QuestionPaperAgent()
    return _paper_agent_instance
