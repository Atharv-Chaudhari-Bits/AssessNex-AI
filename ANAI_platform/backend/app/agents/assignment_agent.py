"""
Assignment Generation Agent with File Generation Capabilities
Uses LangGraph for workflow orchestration and diverse assignment creation
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
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AssignmentType(Enum):
    """Types of assignments"""
    CODING = "coding"
    THEORETICAL = "theoretical"
    MIXED = "mixed"
    PROJECT = "project"
    LAB = "lab"


class DifficultyLevel(Enum):
    """Difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class GeneratedFile:
    """Represents a generated file"""
    filename: str
    content: str
    file_type: str
    description: str
    language: Optional[str] = None


@dataclass
class AssignmentTask:
    """Represents a single assignment task"""
    task_id: str
    title: str
    description: str
    requirements: List[str]
    expected_output: str
    hints: List[str]
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    test_cases: Optional[List[Dict]] = None
    rubric: Optional[Dict] = None
    points: int = 10
    files: List[GeneratedFile] = field(default_factory=list)


@dataclass
class Assignment:
    """Complete assignment structure"""
    assignment_id: str
    title: str
    subject: str
    topic: str
    difficulty: DifficultyLevel
    assignment_type: AssignmentType
    description: str
    learning_objectives: List[str]
    tasks: List[AssignmentTask]
    total_points: int
    due_date: Optional[str] = None
    submission_guidelines: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    generated_files: List[GeneratedFile] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    diversity_seed: str = ""


class AssignmentState(TypedDict):
    """State for assignment generation workflow"""
    # Input
    subject: str
    topic: str
    difficulty: str
    assignment_type: str
    num_tasks: int
    include_solutions: bool
    include_starter_code: bool
    include_test_cases: bool
    diversity_seed: str
    custom_instructions: str
    
    # Processing state
    messages: Annotated[List[Any], operator.add]
    current_step: str
    errors: List[str]
    retry_count: int
    
    # Generated content
    learning_objectives: List[str]
    tasks: List[Dict]
    generated_files: List[Dict]
    submission_guidelines: List[str]
    
    # Output
    assignment: Optional[Dict]
    status: str


class AssignmentGenerationAgent:
    """
    Advanced Assignment Generation Agent using LangGraph
    Features:
    - Multi-step workflow with state management
    - Diverse assignment generation
    - Code file generation
    - Test case generation
    - Solution generation
    - Rubric creation
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_DEPLOYMENT,
            openai_api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0.8,  # Higher for diversity
            max_tokens=4000
        )
        
        # Memory for checkpointing (must be before workflow build)
        self.memory = MemorySaver()
        
        # Create workflow graph
        self.workflow = self._build_workflow()
        
        # Diversity strategies
        self.diversity_strategies = [
            "real_world_scenario",
            "academic_focus",
            "industry_practice",
            "research_oriented",
            "problem_solving",
            "creative_application"
        ]
        
        # Programming language templates
        self.language_templates = {
            "python": {
                "extension": ".py",
                "comment": "#",
                "main_template": 'if __name__ == "__main__":\n    main()',
                "test_framework": "pytest"
            },
            "javascript": {
                "extension": ".js",
                "comment": "//",
                "main_template": "// Run main\nmain();",
                "test_framework": "jest"
            },
            "java": {
                "extension": ".java",
                "comment": "//",
                "main_template": "public static void main(String[] args) {\n    // Main code\n}",
                "test_framework": "junit"
            },
            "cpp": {
                "extension": ".cpp",
                "comment": "//",
                "main_template": "int main() {\n    return 0;\n}",
                "test_framework": "gtest"
            }
        }
        
        logger.info("AssignmentGenerationAgent initialized with LangGraph workflow")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for assignment generation"""
        
        workflow = StateGraph(AssignmentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("generate_objectives", self._generate_objectives_node)
        workflow.add_node("generate_tasks", self._generate_tasks_node)
        workflow.add_node("generate_code_files", self._generate_code_files_node)
        workflow.add_node("generate_test_cases", self._generate_test_cases_node)
        workflow.add_node("generate_solutions", self._generate_solutions_node)
        workflow.add_node("generate_rubric", self._generate_rubric_node)
        workflow.add_node("finalize", self._finalize_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "generate_objectives")
        workflow.add_edge("generate_objectives", "generate_tasks")
        
        # Conditional edges based on assignment type
        workflow.add_conditional_edges(
            "generate_tasks",
            self._route_after_tasks,
            {
                "code_files": "generate_code_files",
                "test_cases": "generate_test_cases",
                "finalize": "finalize",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_code_files",
            self._route_after_code,
            {
                "test_cases": "generate_test_cases",
                "solutions": "generate_solutions",
                "finalize": "finalize"
            }
        )
        
        workflow.add_edge("generate_test_cases", "generate_solutions")
        workflow.add_edge("generate_solutions", "generate_rubric")
        workflow.add_edge("generate_rubric", "finalize")
        workflow.add_edge("handle_error", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _route_after_tasks(self, state: AssignmentState) -> str:
        """Route after task generation"""
        if state.get("errors"):
            return "error"
        
        assignment_type = state.get("assignment_type", "").lower()
        if assignment_type in ["coding", "project", "lab", "mixed"]:
            return "code_files"
        elif state.get("include_test_cases"):
            return "test_cases"
        return "finalize"
    
    def _route_after_code(self, state: AssignmentState) -> str:
        """Route after code file generation"""
        if state.get("include_test_cases"):
            return "test_cases"
        elif state.get("include_solutions"):
            return "solutions"
        return "finalize"
    
    async def _initialize_node(self, state: AssignmentState) -> Dict:
        """Initialize the assignment generation"""
        logger.info(f"Initializing assignment generation for {state['subject']} - {state['topic']}")
        
        # Generate diversity seed if not provided
        diversity_seed = state.get("diversity_seed") or self._generate_diversity_seed()
        
        return {
            "current_step": "initialized",
            "diversity_seed": diversity_seed,
            "messages": [{"role": "system", "content": f"Starting assignment generation with seed: {diversity_seed}"}],
            "status": "in_progress"
        }
    
    async def _generate_objectives_node(self, state: AssignmentState) -> Dict:
        """Generate learning objectives"""
        logger.info("Generating learning objectives")
        
        strategy = self._select_diversity_strategy(state["diversity_seed"])
        
        prompt = f"""Generate 4-6 specific learning objectives for an assignment on:
Subject: {state['subject']}
Topic: {state['topic']}
Difficulty: {state['difficulty']}
Assignment Type: {state['assignment_type']}
Diversity Strategy: {strategy}

The learning objectives should be:
1. Measurable and specific
2. Aligned with {strategy} approach
3. Appropriate for {state['difficulty']} level

Return as JSON array of strings."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert educator creating learning objectives. Return only valid JSON."),
                HumanMessage(content=prompt)
            ])
            
            objectives = self._parse_json_response(response.content, default=[
                f"Understand core concepts of {state['topic']}",
                f"Apply {state['topic']} principles to solve problems",
                f"Analyze and evaluate solutions",
                f"Create original implementations"
            ])
            
            return {
                "learning_objectives": objectives,
                "current_step": "objectives_generated",
                "messages": [{"role": "assistant", "content": f"Generated {len(objectives)} learning objectives"}]
            }
        except Exception as e:
            logger.error(f"Error generating objectives: {e}")
            return {
                "errors": [str(e)],
                "learning_objectives": [f"Master {state['topic']} concepts"],
                "current_step": "objectives_generated"
            }
    
    async def _generate_tasks_node(self, state: AssignmentState) -> Dict:
        """Generate assignment tasks with diversity"""
        logger.info(f"Generating {state['num_tasks']} tasks")
        
        strategy = self._select_diversity_strategy(state["diversity_seed"])
        seed_hash = int(hashlib.md5(state["diversity_seed"].encode()).hexdigest()[:8], 16)
        
        # Create diverse scenarios based on seed
        scenarios = self._get_diverse_scenarios(state["topic"], seed_hash)
        
        prompt = f"""Create {state['num_tasks']} diverse assignment tasks for:
Subject: {state['subject']}
Topic: {state['topic']}
Difficulty: {state['difficulty']}
Type: {state['assignment_type']}
Strategy: {strategy}

Use these scenario themes for diversity: {scenarios[:3]}

For each task, provide:
1. task_id: Unique identifier (task_1, task_2, etc.)
2. title: Concise task title
3. description: Detailed task description (2-3 paragraphs)
4. requirements: List of specific requirements (4-6 items)
5. expected_output: What the student should submit
6. hints: 2-3 helpful hints
7. points: Point value (total should be 100)

Return as JSON array of task objects.
Make each task unique and progressively challenging.
Include real-world applications where possible."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert educator creating diverse, engaging assignments. Return only valid JSON array."),
                HumanMessage(content=prompt)
            ])
            
            tasks = self._parse_json_response(response.content, default=[])
            
            if not tasks:
                tasks = self._generate_fallback_tasks(state)
            
            return {
                "tasks": tasks,
                "current_step": "tasks_generated",
                "messages": [{"role": "assistant", "content": f"Generated {len(tasks)} diverse tasks"}]
            }
        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
            return {
                "errors": [str(e)],
                "tasks": self._generate_fallback_tasks(state),
                "current_step": "tasks_generated"
            }
    
    async def _generate_code_files_node(self, state: AssignmentState) -> Dict:
        """Generate starter code files for coding assignments"""
        logger.info("Generating code files")
        
        if not state.get("include_starter_code", True):
            return {"generated_files": [], "current_step": "code_files_skipped"}
        
        generated_files = []
        lang = self._detect_programming_language(state["subject"], state["topic"])
        lang_config = self.language_templates.get(lang, self.language_templates["python"])
        
        for task in state.get("tasks", []):
            prompt = f"""Generate starter code for this task:
Task: {task.get('title', 'Task')}
Description: {task.get('description', '')}
Requirements: {task.get('requirements', [])}

Programming Language: {lang}
Difficulty: {state['difficulty']}

Provide:
1. Well-commented starter code with TODO markers
2. Function/class stubs with docstrings
3. Example usage in comments
4. Input validation placeholders

Return ONLY the code, no explanations."""

            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=f"You are an expert {lang} programmer. Generate clean, well-documented starter code."),
                    HumanMessage(content=prompt)
                ])
                
                code = self._extract_code(response.content, lang)
                filename = f"{task.get('task_id', 'task')}_starter{lang_config['extension']}"
                
                generated_files.append({
                    "filename": filename,
                    "content": code,
                    "file_type": "starter_code",
                    "language": lang,
                    "description": f"Starter code for {task.get('title', 'task')}"
                })
                
            except Exception as e:
                logger.error(f"Error generating code for task: {e}")
        
        return {
            "generated_files": generated_files,
            "current_step": "code_files_generated",
            "messages": [{"role": "assistant", "content": f"Generated {len(generated_files)} code files"}]
        }
    
    async def _generate_test_cases_node(self, state: AssignmentState) -> Dict:
        """Generate test cases for tasks"""
        logger.info("Generating test cases")
        
        if not state.get("include_test_cases"):
            return {"current_step": "test_cases_skipped"}
        
        lang = self._detect_programming_language(state["subject"], state["topic"])
        lang_config = self.language_templates.get(lang, self.language_templates["python"])
        test_files = []
        
        for task in state.get("tasks", []):
            prompt = f"""Generate comprehensive test cases for:
Task: {task.get('title', 'Task')}
Requirements: {task.get('requirements', [])}
Expected Output: {task.get('expected_output', '')}

Language: {lang}
Test Framework: {lang_config['test_framework']}

Include:
1. Basic functionality tests (3-4)
2. Edge case tests (2-3)
3. Error handling tests (1-2)
4. Performance tests if applicable

Return ONLY the test code."""

            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=f"You are an expert in {lang} testing. Generate comprehensive test cases."),
                    HumanMessage(content=prompt)
                ])
                
                test_code = self._extract_code(response.content, lang)
                filename = f"test_{task.get('task_id', 'task')}{lang_config['extension']}"
                
                test_files.append({
                    "filename": filename,
                    "content": test_code,
                    "file_type": "test_file",
                    "language": lang,
                    "description": f"Test cases for {task.get('title', 'task')}"
                })
                
                # Update task with test cases info
                task["test_cases"] = [
                    {"name": "basic_test", "description": "Basic functionality"},
                    {"name": "edge_case_test", "description": "Edge cases"},
                    {"name": "error_test", "description": "Error handling"}
                ]
                
            except Exception as e:
                logger.error(f"Error generating tests: {e}")
        
        # Add test files to generated files
        all_files = state.get("generated_files", []) + test_files
        
        return {
            "generated_files": all_files,
            "tasks": state["tasks"],
            "current_step": "test_cases_generated"
        }
    
    async def _generate_solutions_node(self, state: AssignmentState) -> Dict:
        """Generate solution files"""
        logger.info("Generating solutions")
        
        if not state.get("include_solutions"):
            return {"current_step": "solutions_skipped"}
        
        lang = self._detect_programming_language(state["subject"], state["topic"])
        lang_config = self.language_templates.get(lang, self.language_templates["python"])
        solution_files = []
        
        for task in state.get("tasks", []):
            prompt = f"""Generate a complete, well-documented solution for:
Task: {task.get('title', 'Task')}
Description: {task.get('description', '')}
Requirements: {task.get('requirements', [])}
Expected Output: {task.get('expected_output', '')}

Language: {lang}
Difficulty: {state['difficulty']}

Provide:
1. Complete working solution
2. Detailed comments explaining logic
3. Time/space complexity analysis in comments
4. Alternative approaches mentioned in comments

Return ONLY the solution code."""

            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=f"You are an expert {lang} programmer. Generate optimal, well-documented solutions."),
                    HumanMessage(content=prompt)
                ])
                
                solution = self._extract_code(response.content, lang)
                filename = f"{task.get('task_id', 'task')}_solution{lang_config['extension']}"
                
                solution_files.append({
                    "filename": filename,
                    "content": solution,
                    "file_type": "solution",
                    "language": lang,
                    "description": f"Solution for {task.get('title', 'task')}"
                })
                
                # Store solution in task
                task["solution_code"] = solution
                
            except Exception as e:
                logger.error(f"Error generating solution: {e}")
        
        all_files = state.get("generated_files", []) + solution_files
        
        return {
            "generated_files": all_files,
            "tasks": state["tasks"],
            "current_step": "solutions_generated"
        }
    
    async def _generate_rubric_node(self, state: AssignmentState) -> Dict:
        """Generate grading rubric"""
        logger.info("Generating rubric")
        
        tasks_summary = "\n".join([
            f"- {t.get('title', 'Task')}: {t.get('points', 10)} points"
            for t in state.get("tasks", [])
        ])
        
        prompt = f"""Create a detailed grading rubric for this assignment:
Subject: {state['subject']}
Topic: {state['topic']}
Tasks:
{tasks_summary}

For each task, define criteria for:
1. Excellent (90-100%)
2. Good (70-89%)
3. Satisfactory (50-69%)
4. Needs Improvement (<50%)

Also include:
- Code quality criteria (if applicable)
- Documentation requirements
- Bonus point opportunities

Return as structured JSON."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert educator creating fair, comprehensive grading rubrics."),
                HumanMessage(content=prompt)
            ])
            
            rubric = self._parse_json_response(response.content, default={})
            
            # Create rubric file
            rubric_content = self._format_rubric_markdown(rubric, state)
            rubric_file = {
                "filename": "GRADING_RUBRIC.md",
                "content": rubric_content,
                "file_type": "rubric",
                "language": "markdown",
                "description": "Grading rubric for the assignment"
            }
            
            all_files = state.get("generated_files", []) + [rubric_file]
            
            # Update tasks with rubric
            for task in state.get("tasks", []):
                task["rubric"] = rubric.get(task.get("task_id"), {})
            
            return {
                "generated_files": all_files,
                "tasks": state["tasks"],
                "current_step": "rubric_generated"
            }
        except Exception as e:
            logger.error(f"Error generating rubric: {e}")
            return {"current_step": "rubric_skipped"}
    
    async def _finalize_node(self, state: AssignmentState) -> Dict:
        """Finalize the assignment"""
        logger.info("Finalizing assignment")
        
        # Generate assignment ID
        assignment_id = f"ASN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{state['diversity_seed'][:6]}"
        
        # Create README file
        readme_content = self._generate_readme(state, assignment_id)
        readme_file = {
            "filename": "README.md",
            "content": readme_content,
            "file_type": "readme",
            "language": "markdown",
            "description": "Assignment instructions and overview"
        }
        
        all_files = state.get("generated_files", []) + [readme_file]
        
        # Calculate total points
        total_points = sum(t.get("points", 10) for t in state.get("tasks", []))
        
        # Build final assignment
        assignment = {
            "assignment_id": assignment_id,
            "title": f"{state['topic']} Assignment",
            "subject": state["subject"],
            "topic": state["topic"],
            "difficulty": state["difficulty"],
            "assignment_type": state["assignment_type"],
            "description": f"Comprehensive {state['assignment_type']} assignment on {state['topic']}",
            "learning_objectives": state.get("learning_objectives", []),
            "tasks": state.get("tasks", []),
            "total_points": total_points,
            "submission_guidelines": [
                "Submit all code files in a single ZIP archive",
                "Include a README with your approach and any assumptions",
                "Ensure all test cases pass before submission",
                "Comment your code thoroughly",
                "Follow the coding style guidelines"
            ],
            "resources": [
                f"Official documentation for {state['topic']}",
                "Course lecture notes",
                "Recommended textbook chapters"
            ],
            "generated_files": all_files,
            "created_at": datetime.now().isoformat(),
            "diversity_seed": state["diversity_seed"]
        }
        
        return {
            "assignment": assignment,
            "status": "completed",
            "current_step": "finalized",
            "messages": [{"role": "assistant", "content": f"Assignment {assignment_id} created successfully"}]
        }
    
    async def _handle_error_node(self, state: AssignmentState) -> Dict:
        """Handle errors in the workflow"""
        errors = state.get("errors", [])
        logger.error(f"Handling errors: {errors}")
        
        return {
            "status": "completed_with_errors",
            "current_step": "error_handled",
            "messages": [{"role": "system", "content": f"Completed with errors: {errors}"}]
        }
    
    # Helper methods
    def _generate_diversity_seed(self) -> str:
        """Generate a unique diversity seed"""
        timestamp = datetime.now().isoformat()
        random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        return hashlib.md5(f"{timestamp}-{random_part}".encode()).hexdigest()[:12]
    
    def _select_diversity_strategy(self, seed: str) -> str:
        """Select a diversity strategy based on seed"""
        seed_int = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
        return self.diversity_strategies[seed_int % len(self.diversity_strategies)]
    
    def _get_diverse_scenarios(self, topic: str, seed: int) -> List[str]:
        """Get diverse scenarios for a topic"""
        base_scenarios = [
            f"E-commerce application using {topic}",
            f"Healthcare system implementing {topic}",
            f"Financial trading platform with {topic}",
            f"Social media analytics using {topic}",
            f"IoT sensor data processing with {topic}",
            f"Gaming leaderboard system using {topic}",
            f"Educational platform implementing {topic}",
            f"Logistics optimization with {topic}"
        ]
        
        # Shuffle based on seed for diversity
        random.seed(seed)
        random.shuffle(base_scenarios)
        return base_scenarios
    
    def _detect_programming_language(self, subject: str, topic: str) -> str:
        """Detect programming language from subject/topic"""
        text = f"{subject} {topic}".lower()
        
        if any(kw in text for kw in ["python", "django", "flask", "pandas", "numpy"]):
            return "python"
        elif any(kw in text for kw in ["javascript", "node", "react", "vue", "angular"]):
            return "javascript"
        elif any(kw in text for kw in ["java", "spring", "maven", "gradle"]):
            return "java"
        elif any(kw in text for kw in ["c++", "cpp", "stl"]):
            return "cpp"
        
        return "python"  # Default
    
    def _extract_code(self, content: str, language: str) -> str:
        """Extract code from LLM response"""
        import re
        
        # Try to find code block
        pattern = rf"```(?:{language}|{language.lower()})?\s*\n(.*?)```"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # If no code block, return cleaned content
        lines = content.strip().split('\n')
        code_lines = [l for l in lines if not l.startswith(('Here', 'This', 'The', 'Below'))]
        return '\n'.join(code_lines)
    
    def _parse_json_response(self, content: str, default: Any) -> Any:
        """Parse JSON from LLM response"""
        import re
        
        # Try to find JSON in response
        content = content.strip()
        
        # Remove markdown code blocks
        json_match = re.search(r"```(?:json)?\s*\n(.*?)```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        # Try to find JSON array or object
        try:
            # Find first [ or {
            start_idx = -1
            for i, c in enumerate(content):
                if c in '[{':
                    start_idx = i
                    break
            
            if start_idx >= 0:
                # Find matching end
                bracket_count = 0
                end_idx = start_idx
                start_char = content[start_idx]
                end_char = ']' if start_char == '[' else '}'
                
                for i in range(start_idx, len(content)):
                    if content[i] == start_char:
                        bracket_count += 1
                    elif content[i] == end_char:
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i + 1
                            break
                
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return default
    
    def _generate_fallback_tasks(self, state: Dict) -> List[Dict]:
        """Generate fallback tasks if LLM fails"""
        return [
            {
                "task_id": "task_1",
                "title": f"Introduction to {state['topic']}",
                "description": f"Implement a basic example demonstrating {state['topic']} concepts.",
                "requirements": [
                    "Implement the core functionality",
                    "Add appropriate documentation",
                    "Include error handling",
                    "Write unit tests"
                ],
                "expected_output": "Working implementation with documentation",
                "hints": ["Start with the basic structure", "Test incrementally"],
                "points": 40
            },
            {
                "task_id": "task_2",
                "title": f"Advanced {state['topic']} Application",
                "description": f"Build an advanced application using {state['topic']}.",
                "requirements": [
                    "Extend the basic implementation",
                    "Add optimization",
                    "Implement additional features",
                    "Performance testing"
                ],
                "expected_output": "Complete application with all features",
                "hints": ["Build on Task 1", "Focus on code quality"],
                "points": 60
            }
        ]
    
    def _format_rubric_markdown(self, rubric: Dict, state: Dict) -> str:
        """Format rubric as markdown"""
        md = f"""# Grading Rubric
## {state['topic']} Assignment

### Overview
- **Total Points**: 100
- **Difficulty**: {state['difficulty']}
- **Type**: {state['assignment_type']}

### Grading Criteria

"""
        for task in state.get("tasks", []):
            task_id = task.get("task_id", "task")
            title = task.get("title", "Task")
            points = task.get("points", 10)
            
            md += f"""#### {title} ({points} points)

| Criteria | Excellent (90-100%) | Good (70-89%) | Satisfactory (50-69%) | Needs Improvement (<50%) |
|----------|---------------------|---------------|----------------------|-------------------------|
| Functionality | All requirements met perfectly | Most requirements met | Basic requirements met | Missing key requirements |
| Code Quality | Clean, well-documented | Good structure | Acceptable | Poor quality |
| Testing | Comprehensive tests | Good coverage | Basic tests | No/few tests |

"""
        
        md += """### Bonus Points
- Exceptional documentation: +5 points
- Creative solution: +5 points
- Performance optimization: +5 points

### Submission Requirements
- All files in ZIP format
- README with approach description
- All tests passing
"""
        return md
    
    def _generate_readme(self, state: Dict, assignment_id: str) -> str:
        """Generate README file for assignment"""
        tasks_md = ""
        for i, task in enumerate(state.get("tasks", []), 1):
            tasks_md += f"""
### Task {i}: {task.get('title', 'Task')}
**Points**: {task.get('points', 10)}

{task.get('description', '')}

**Requirements**:
"""
            for req in task.get("requirements", []):
                tasks_md += f"- {req}\n"
            
            tasks_md += f"""
**Expected Output**: {task.get('expected_output', '')}

**Hints**:
"""
            for hint in task.get("hints", []):
                tasks_md += f"- {hint}\n"
            tasks_md += "\n---\n"
        
        objectives_md = "\n".join([f"- {obj}" for obj in state.get("learning_objectives", [])])
        
        return f"""# {state['topic']} Assignment

**Assignment ID**: {assignment_id}
**Subject**: {state['subject']}
**Difficulty**: {state['difficulty']}
**Type**: {state['assignment_type']}

## Learning Objectives
{objectives_md}

## Tasks
{tasks_md}

## Submission Guidelines
1. Submit all code files in a single ZIP archive
2. Include this README with your submission
3. Document your approach and any assumptions
4. Ensure all test cases pass before submission
5. Follow coding style guidelines

## Resources
- Course lecture notes
- Official documentation
- Recommended textbook chapters

## Grading
See GRADING_RUBRIC.md for detailed grading criteria.

---
*Generated by AssessNex AI*
"""

    async def generate_assignment(
        self,
        subject: str,
        topic: str,
        difficulty: str = "intermediate",
        assignment_type: str = "coding",
        num_tasks: int = 3,
        include_solutions: bool = True,
        include_starter_code: bool = True,
        include_test_cases: bool = True,
        custom_instructions: str = ""
    ) -> Dict:
        """
        Generate a complete assignment with all files
        """
        logger.info(f"Generating {assignment_type} assignment for {subject}/{topic}")
        
        # Create initial state
        initial_state: AssignmentState = {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "assignment_type": assignment_type,
            "num_tasks": num_tasks,
            "include_solutions": include_solutions,
            "include_starter_code": include_starter_code,
            "include_test_cases": include_test_cases,
            "diversity_seed": self._generate_diversity_seed(),
            "custom_instructions": custom_instructions,
            "messages": [],
            "current_step": "start",
            "errors": [],
            "retry_count": 0,
            "learning_objectives": [],
            "tasks": [],
            "generated_files": [],
            "submission_guidelines": [],
            "assignment": None,
            "status": "pending"
        }
        
        # Create unique thread ID for this generation
        thread_id = f"assignment-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            if final_state.get("assignment"):
                logger.info(f"Assignment generated successfully: {final_state['assignment'].get('assignment_id')}")
                return final_state["assignment"]
            else:
                logger.error("Assignment generation failed - no assignment in final state")
                return {"error": "Assignment generation failed", "state": final_state.get("status")}
                
        except Exception as e:
            logger.error(f"Error in assignment generation workflow: {e}")
            return {"error": str(e)}


# Create singleton instance
assignment_agent = AssignmentGenerationAgent()
