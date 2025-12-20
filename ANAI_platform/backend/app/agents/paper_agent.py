"""
Question Paper Generation Agent using LangGraph
Robust multi-step workflow for generating complete question papers
"""

import asyncio
import json
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import operator

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..config import settings
from ..utils.logger import get_logger
from .question_generator import QuestionGenerationAgent

logger = get_logger(__name__)


class PaperSection(TypedDict):
    """Section of a question paper"""
    section_id: str
    title: str
    instructions: str
    question_type: str
    num_questions: int
    marks_per_question: int
    questions: List[Dict]


class PaperState(TypedDict):
    """State for paper generation workflow"""
    # Input configuration
    subject: str
    topic: str
    subtopics: List[str]
    difficulty_distribution: Dict[str, int]
    question_type_config: List[Dict]
    total_marks: int
    duration_minutes: int
    exam_name: str
    instructions: List[str]
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
    
    # Output
    paper: Optional[Dict]
    status: str


class QuestionPaperAgent:
    """
    Advanced Question Paper Generation Agent using LangGraph
    
    Features:
    - Multi-section paper generation
    - Difficulty distribution control
    - Bloom's taxonomy integration
    - Diverse question generation
    - Answer key generation
    - Marking scheme generation
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_DEPLOYMENT,
            openai_api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=4000
        )
        
        # Question generator for individual questions
        self.question_generator = QuestionGenerationAgent()
        
        # Memory for checkpointing (must be before workflow build)
        self.memory = MemorySaver()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        # Question type configurations
        self.question_type_configs = {
            "Multiple Choice": {
                "marks": [1, 2],
                "time_per_question": 1.5,  # minutes
                "blooms_levels": ["Remember", "Understand", "Apply"]
            },
            "True/False": {
                "marks": [1],
                "time_per_question": 1,
                "blooms_levels": ["Remember", "Understand"]
            },
            "Fill in the Blank": {
                "marks": [1, 2],
                "time_per_question": 1,
                "blooms_levels": ["Remember", "Understand"]
            },
            "Short Answer": {
                "marks": [2, 3, 4],
                "time_per_question": 4,
                "blooms_levels": ["Understand", "Apply", "Analyze"]
            },
            "Long Answer": {
                "marks": [5, 8, 10],
                "time_per_question": 10,
                "blooms_levels": ["Apply", "Analyze", "Evaluate", "Create"]
            },
            "Numerical": {
                "marks": [3, 5],
                "time_per_question": 5,
                "blooms_levels": ["Apply", "Analyze"]
            },
            "Code Writing": {
                "marks": [5, 10, 15],
                "time_per_question": 12,
                "blooms_levels": ["Apply", "Analyze", "Create"]
            },
            "Diagram Based": {
                "marks": [3, 5],
                "time_per_question": 5,
                "blooms_levels": ["Understand", "Apply", "Analyze"]
            }
        }
        
        logger.info("QuestionPaperAgent initialized with LangGraph workflow")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(PaperState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("generate_header", self._generate_header_node)
        workflow.add_node("plan_sections", self._plan_sections_node)
        workflow.add_node("generate_section", self._generate_section_node)
        workflow.add_node("generate_answer_key", self._generate_answer_key_node)
        workflow.add_node("finalize", self._finalize_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "generate_header")
        workflow.add_edge("generate_header", "plan_sections")
        workflow.add_edge("plan_sections", "generate_section")
        
        # Conditional edge for section generation loop
        workflow.add_conditional_edges(
            "generate_section",
            self._route_after_section,
            {
                "next_section": "generate_section",
                "answer_key": "generate_answer_key",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("generate_answer_key", "finalize")
        workflow.add_edge("handle_error", "finalize")
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
        return "answer_key"
    
    async def _initialize_node(self, state: PaperState) -> Dict:
        """Initialize paper generation"""
        logger.info(f"Initializing paper generation for {state['subject']} - {state['topic']}")
        
        diversity_seed = state.get("diversity_seed") or self._generate_diversity_seed()
        
        return {
            "current_step": "initialized",
            "current_section_idx": 0,
            "diversity_seed": diversity_seed,
            "sections": [],
            "messages": [{"role": "system", "content": f"Starting paper generation with seed: {diversity_seed}"}],
            "status": "in_progress"
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
                "Show all working for numerical problems.",
                "Marks are indicated against each question."
            ])
        }
        
        return {
            "header_info": header_info,
            "current_step": "header_generated",
            "messages": [{"role": "assistant", "content": "Paper header generated"}]
        }
    
    async def _plan_sections_node(self, state: PaperState) -> Dict:
        """Plan paper sections based on question type config"""
        logger.info("Planning paper sections")
        
        question_configs = state.get("question_type_config", [])
        
        if not question_configs:
            # Create default sections
            question_configs = self._create_default_sections(
                state["total_marks"],
                state["duration_minutes"]
            )
        
        # Calculate marks distribution
        sections_plan = []
        section_labels = ["A", "B", "C", "D", "E", "F"]
        
        for i, config in enumerate(question_configs):
            q_type = config.get("type", "Multiple Choice")
            num_q = config.get("count", 5)
            marks = config.get("marks_each", 2)
            
            sections_plan.append({
                "section_id": section_labels[i] if i < len(section_labels) else f"Section_{i+1}",
                "title": f"Section {section_labels[i]}: {q_type}" if i < len(section_labels) else f"Section {i+1}: {q_type}",
                "question_type": q_type,
                "num_questions": num_q,
                "marks_per_question": marks,
                "total_marks": num_q * marks,
                "instructions": self._get_section_instructions(q_type),
                "questions": []
            })
        
        return {
            "question_type_config": question_configs,
            "current_step": "sections_planned",
            "messages": [{"role": "assistant", "content": f"Planned {len(sections_plan)} sections"}]
        }
    
    async def _generate_section_node(self, state: PaperState) -> Dict:
        """Generate questions for current section"""
        current_idx = state.get("current_section_idx", 0)
        question_configs = state.get("question_type_config", [])
        
        if current_idx >= len(question_configs):
            return {"current_step": "all_sections_generated"}
        
        config = question_configs[current_idx]
        q_type = config.get("type", "Multiple Choice")
        num_questions = config.get("count", 5)
        difficulty = config.get("difficulty", "medium")
        
        logger.info(f"Generating section {current_idx + 1}: {q_type} ({num_questions} questions)")
        
        # Determine difficulty distribution for this section
        difficulty_dist = self._get_difficulty_distribution(difficulty, num_questions)
        
        # Generate questions using the question generator
        section_questions = []
        question_number = self._get_starting_question_number(state.get("sections", []))
        
        for diff, count in difficulty_dist.items():
            if count > 0:
                try:
                    # Generate questions - use correct parameter names
                    questions = self.question_generator.generate_questions(
                        subject=state["subject"],
                        question_type=q_type,
                        difficulty_level=diff,
                        num_questions=count,
                        additional_context=f"Topic: {state.get('topic', '')}. Subtopics: {', '.join(state.get('subtopics', []))}"
                    )
                    
                    # Add question numbers and marks
                    for q in questions:
                        q["question_number"] = question_number
                        q["marks"] = config.get("marks_each", 2)
                        section_questions.append(q)
                        question_number += 1
                        
                except Exception as e:
                    logger.error(f"Error generating questions: {e}")
                    # Add fallback question
                    section_questions.append({
                        "question_number": question_number,
                        "question_type": q_type,
                        "question_text": f"[Question generation failed - {q_type}]",
                        "marks": config.get("marks_each", 2),
                        "difficulty_level": diff
                    })
                    question_number += 1
        
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
        
        # Update sections list
        sections = state.get("sections", []).copy()
        sections.append(section)
        
        return {
            "sections": sections,
            "current_section_idx": current_idx + 1,
            "current_step": f"section_{current_idx + 1}_generated",
            "messages": [{"role": "assistant", "content": f"Generated {len(section_questions)} questions for {q_type}"}]
        }
    
    async def _generate_answer_key_node(self, state: PaperState) -> Dict:
        """Generate answer key and marking scheme"""
        logger.info("Generating answer key")
        
        answer_key = []
        marking_scheme = []
        
        for section in state.get("sections", []):
            section_answers = {
                "section_id": section["section_id"],
                "section_title": section["title"],
                "answers": []
            }
            
            for q in section.get("questions", []):
                answer_entry = {
                    "question_number": q.get("question_number"),
                    "answer": q.get("correct_answer") or q.get("expected_answer", ""),
                    "marks": q.get("marks", 2)
                }
                
                # Add explanation if available
                if q.get("explanation"):
                    answer_entry["explanation"] = q["explanation"]
                
                # Add marking scheme for longer answers
                if section["question_type"] in ["Short Answer", "Long Answer", "Code Writing"]:
                    answer_entry["marking_scheme"] = self._generate_marking_points(q)
                
                section_answers["answers"].append(answer_entry)
            
            answer_key.append(section_answers)
        
        # Store answer key in header
        header_info = state.get("header_info", {}).copy()
        header_info["answer_key"] = answer_key
        
        return {
            "header_info": header_info,
            "current_step": "answer_key_generated",
            "messages": [{"role": "assistant", "content": "Answer key generated"}]
        }
    
    async def _finalize_node(self, state: PaperState) -> Dict:
        """Finalize the question paper"""
        logger.info("Finalizing question paper")
        
        # Calculate actual total marks
        actual_total = sum(
            section.get("total_marks", 0)
            for section in state.get("sections", [])
        )
        
        # Calculate total questions
        total_questions = sum(
            len(section.get("questions", []))
            for section in state.get("sections", [])
        )
        
        # Generate paper ID
        paper_id = f"QP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{state['diversity_seed'][:6]}"
        
        # Build final paper
        paper = {
            "paper_id": paper_id,
            "header": state.get("header_info", {}),
            "sections": state.get("sections", []),
            "metadata": {
                "total_marks": actual_total,
                "total_questions": total_questions,
                "duration_minutes": state["duration_minutes"],
                "subject": state["subject"],
                "topic": state["topic"],
                "difficulty_distribution": state.get("difficulty_distribution", {}),
                "generated_at": datetime.now().isoformat(),
                "diversity_seed": state["diversity_seed"]
            }
        }
        
        return {
            "paper": paper,
            "status": "completed",
            "current_step": "finalized",
            "messages": [{"role": "assistant", "content": f"Paper {paper_id} generated with {total_questions} questions ({actual_total} marks)"}]
        }
    
    async def _handle_error_node(self, state: PaperState) -> Dict:
        """Handle errors"""
        errors = state.get("errors", [])
        logger.error(f"Handling errors: {errors}")
        
        return {
            "status": "completed_with_errors",
            "current_step": "error_handled"
        }
    
    # Helper methods
    def _generate_diversity_seed(self) -> str:
        """Generate unique diversity seed"""
        timestamp = datetime.now().isoformat()
        random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        return hashlib.md5(f"{timestamp}-{random_part}".encode()).hexdigest()[:12]
    
    def _create_default_sections(self, total_marks: int, duration: int) -> List[Dict]:
        """Create default section configuration"""
        # Calculate based on time and marks
        sections = []
        
        # Section A: MCQs (20% marks)
        mcq_marks = int(total_marks * 0.2)
        sections.append({
            "type": "Multiple Choice",
            "count": mcq_marks,
            "marks_each": 1,
            "difficulty": "mixed"
        })
        
        # Section B: Short Answer (30% marks)
        short_marks = int(total_marks * 0.3)
        sections.append({
            "type": "Short Answer",
            "count": short_marks // 3,
            "marks_each": 3,
            "difficulty": "medium"
        })
        
        # Section C: Long Answer (50% marks)
        long_marks = total_marks - mcq_marks - short_marks
        sections.append({
            "type": "Long Answer",
            "count": long_marks // 10,
            "marks_each": 10,
            "difficulty": "hard"
        })
        
        return sections
    
    def _get_section_instructions(self, question_type: str) -> str:
        """Get instructions for a section based on question type"""
        instructions = {
            "Multiple Choice": "Choose the correct answer from the given options. Each question carries equal marks.",
            "True/False": "Write 'True' or 'False' for each statement.",
            "Fill in the Blank": "Fill in the blanks with appropriate words/terms.",
            "Short Answer": "Answer the following questions briefly. Each answer should be 2-3 sentences.",
            "Long Answer": "Answer the following questions in detail. Include relevant examples and explanations.",
            "Numerical": "Solve the following numerical problems. Show all working and steps.",
            "Code Writing": "Write code for the following problems. Include comments and handle edge cases.",
            "Diagram Based": "Study the diagram and answer the questions that follow."
        }
        return instructions.get(question_type, "Answer all questions in this section.")
    
    def _get_difficulty_distribution(self, difficulty: str, num_questions: int) -> Dict[str, int]:
        """Get difficulty distribution based on overall difficulty setting"""
        distributions = {
            "easy": {"easy": 0.6, "medium": 0.3, "hard": 0.1},
            "medium": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
            "hard": {"easy": 0.1, "medium": 0.4, "hard": 0.5},
            "mixed": {"easy": 0.33, "medium": 0.34, "hard": 0.33}
        }
        
        dist = distributions.get(difficulty, distributions["medium"])
        result = {}
        remaining = num_questions
        
        for diff in ["easy", "medium"]:
            count = int(num_questions * dist[diff])
            result[diff] = count
            remaining -= count
        
        result["hard"] = remaining
        return result
    
    def _get_starting_question_number(self, sections: List[Dict]) -> int:
        """Get the starting question number based on existing sections"""
        total = 1
        for section in sections:
            total += len(section.get("questions", []))
        return total
    
    def _generate_marking_points(self, question: Dict) -> List[Dict]:
        """Generate marking scheme points for a question"""
        marks = question.get("marks", 2)
        
        # Create marking distribution
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
        exam_name: Optional[str] = None,
        subtopics: Optional[List[str]] = None,
        instructions: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a complete question paper
        
        Args:
            subject: Subject name
            topic: Main topic
            total_marks: Total marks for the paper
            duration_minutes: Duration in minutes
            question_type_config: List of dicts with type, count, marks_each, difficulty
            difficulty_distribution: Dict with easy, medium, hard percentages
            exam_name: Name of the examination
            subtopics: List of subtopics to cover
            instructions: Custom instructions
        
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
            difficulty_distribution = {"easy": 30, "medium": 50, "hard": 20}
        
        # Create initial state
        initial_state: PaperState = {
            "subject": subject,
            "topic": topic,
            "subtopics": subtopics or [],
            "difficulty_distribution": difficulty_distribution,
            "question_type_config": question_type_config,
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
paper_agent = QuestionPaperAgent()
