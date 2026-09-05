"""
Assignment generation agent with Bloom's taxonomy support.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.app.prompts.prompt_manager import PromptBuilder
from backend.app.llm_client import get_llm_client, LLMClient

logger = logging.getLogger(__name__)


class AssignmentGenerationAgent:
    """Agent for generating assignments with Bloom's taxonomy support."""

    # Constants for better maintainability
    DEFAULT_MAX_TOKENS = 4000
    DEFAULT_TEMPERATURE = 0.7
    MAX_DOCUMENT_CHARS = 5000
    BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]

    def __init__(self, prompt_builder: PromptBuilder, llm_client=None):
        """
        Initialize the assignment generation agent.

        Args:
            prompt_builder: PromptBuilder instance for creating prompts
            llm_client: Optional LLM client instance (will use singleton if not provided)
        """
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client or get_llm_client()
        logger.info("AssignmentGenerationAgent initialized")

    def generate_assignment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an assignment based on parameters.
        """
        try:
            logger.info(f"Generating assignment: {params.get('name')}")

            # Build prompt for assignment generation
            prompt = self._build_assignment_prompt(params)
            
            # Call LLM to generate assignment (now with await)
            response = self._call_llm(prompt)
            
            # Parse and structure the response
            assignment = self._structure_assignment_response(
                response, params
            )
            
            logger.info(f"Successfully generated assignment with {len(assignment.get('tasks', []))} tasks")
            return assignment

        except Exception as e:
            logger.error(f"Error generating assignment: {str(e)}")
            raise

    def generate_assignment_from_document(self, document_text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an assignment from document content.
        """
        try:
            logger.info(f"Generating assignment from document: {params.get('name')}")
            
            # Add document context to params
            params['document_text'] = document_text[:5000]
            
            # Build prompt with document context
            prompt = self._build_assignment_prompt(params, include_document=True)
            
            # Call LLM (now with await)
            response = self._call_llm(prompt)
            
            # Structure response
            assignment = self._structure_assignment_response(
                response, params, from_document=True
            )
            
            return assignment

        except Exception as e:
            logger.error(f"Error generating assignment from document: {str(e)}")
            raise

    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate required parameters.

        Args:
            params: Parameters to validate

        Raises:
            ValueError: If required parameters are missing
        """
        required_fields = ['name', 'subject', 'num_tasks', 'max_marks']
        missing_fields = [field for field in required_fields if not params.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with prompt using the llm_client.

        Args:
            prompt: Input prompt

        Returns:
            str: LLM response
        """
        try:
            # Use the existing llm_client - NO AWAIT HERE
            response = self.llm_client.create_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator and assignment creator. Generate high-quality educational assignments with clear tasks, requirements, and evaluation criteria. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Extract content from response
            if isinstance(response, dict):
                return response.get("content", response.get("text", json.dumps(response)))
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}", exc_info=True)
            raise

    def _build_assignment_prompt(
        self, 
        params: Dict[str, Any],
        include_document: bool = False
    ) -> str:
        """
        Build prompt for assignment generation.

        Args:
            params: Assignment parameters
            include_document: Whether to include document context

        Returns:
            str: Formatted prompt
        """
        bloom_distribution = params.get('bloom_distribution', {})
        bloom_levels_str = "\n".join([
            f"- {level}: {weight}%" 
            for level, weight in bloom_distribution.items()
        ]) if bloom_distribution else "Standard distribution across all levels"

        prompt = f"""Generate a comprehensive {params.get('assignment_type', 'coding')} assignment with the following specifications:

## Assignment Details
- Name: {params.get('name', 'Untitled Assignment')}
- Course Code: {params.get('course_code', '')}
- Subject: {params.get('subject', '')}
- Topic: {params.get('topic', params.get('subject', ''))}
- Type: {params.get('assignment_type', 'coding')}
- Number of Tasks: {params.get('num_tasks', 5)}
- Total Marks: {params.get('max_marks', 100)}
- Duration: {params.get('duration_days', 7)} days

## Bloom's Taxonomy Distribution
{bloom_levels_str}

## Assignment Description
{params.get('description', '')}

## Additional Context
{params.get('chat_context', 'No additional context provided.')}

## Requirements
1. Create exactly {params.get('num_tasks', 5)} distinct tasks
2. Distribute {params.get('max_marks', 100)} marks across tasks according to Bloom's levels
3. Each task must clearly indicate its Bloom's level
4. Provide clear instructions and requirements for each task
5. Include helpful hints where appropriate
{f"- Include starter code for applicable tasks" if params.get('include_starter_code', False) else ""}
{f"- Include comprehensive solutions" if params.get('include_solutions', True) else ""}
{f"- Include test cases for verification" if params.get('include_test_cases', False) else ""}

## Output Format
Return the assignment in JSON format with the following structure:
{{
    "tasks": [
        {{
            "task_id": "task_1",
            "title": "Task title",
            "description": "Detailed task description",
            "points": 20,
            "bloom_level": "Apply",
            "requirements": ["Requirement 1", "Requirement 2"],
            "hints": ["Hint 1", "Hint 2"],
            "expected_output": "Description of expected output",
            "starter_code": "Optional starter code",
            "solution_code": "Optional solution code",
            "test_cases": ["Test case 1", "Test case 2"]
        }}
    ],
    "submission_guidelines": [
        "Guideline 1",
        "Guideline 2"
    ],
    "evaluation_criteria": [
        {{
            "criterion": "Criterion name",
            "weight": 0.4,
            "description": "Description",
            "bloom_level": "Apply"
        }}
    ],
    "learning_objectives": [
        "Objective 1",
        "Objective 2"
    ],
    "generated_files": [
        {{
            "filename": "file.py",
            "content": "File content",
            "file_type": "code",
            "language": "python",
            "description": "File description"
        }}
    ]
}}

Ensure all tasks are appropriately calibrated to their assigned Bloom's taxonomy levels.
"""

        if include_document and params.get('document_text'):
            prompt += f"\n\n## Document Context\n{params['document_text']}\n"

        return prompt

    def _structure_assignment_response(
        self,
        response: str,
        params: Dict[str, Any],
        from_document: bool = False
    ) -> Dict[str, Any]:
        """
        Structure the LLM response into assignment format.

        Args:
            response: Raw LLM response
            params: Original parameters
            from_document: Whether generated from document

        Returns:
            Dict[str, Any]: Structured assignment
        """
        # Try to parse as JSON first
        try:
            # Clean the response - sometimes LLM returns with markdown code blocks
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            assignment_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}. Using text parsing.")
            assignment_data = self._parse_text_response(response, params)

        # Ensure required fields with fallbacks
        assignment = {
            "name": params.get('name', 'Untitled Assignment'),
            "course_code": params.get('course_code', ''),
            "subject": params.get('subject', ''),
            "assignment_type": params.get('assignment_type', 'coding'),
            "total_marks": params.get('max_marks', 100),
            "duration_days": params.get('duration_days', 7),
            "description": params.get('description', ''),
            "tasks": assignment_data.get('tasks', self._generate_default_tasks(params)),
            "submission_guidelines": assignment_data.get('submission_guidelines', [
                "Submit your assignment as a single PDF file",
                "Include your name and student ID on the first page",
                "Cite all references used"
            ]),
            "evaluation_criteria": assignment_data.get('evaluation_criteria', self._generate_evaluation_criteria(params)),
            "learning_objectives": assignment_data.get('learning_objectives', self._generate_learning_objectives(params)),
            "generated_files": assignment_data.get('generated_files', []),
            "generated_from_document": from_document,
            "generated_at": datetime.now().isoformat()
        }

        # Add Bloom's distribution info if provided
        if params.get('bloom_distribution'):
            assignment["bloom_distribution"] = params['bloom_distribution']

        return assignment

    def _generate_default_tasks(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default tasks if none provided."""
        tasks = []
        num_tasks = params.get('num_tasks', 5)
        marks_per_task = params.get('max_marks', 100) // max(num_tasks, 1)  # Avoid division by zero
        
        for i in range(num_tasks):
            bloom_level = self.BLOOM_LEVELS[i % len(self.BLOOM_LEVELS)]
            tasks.append({
                "task_id": f"task_{i+1}",
                "title": f"Task {i+1}: {bloom_level} Level Question",
                "description": f"Demonstrate {bloom_level.lower()} level understanding of {params.get('topic', params.get('subject', 'the topic'))}",
                "points": marks_per_task,
                "bloom_level": bloom_level,
                "requirements": [
                    "Read the question carefully",
                    "Provide complete solution",
                    "Show all work"
                ],
                "hints": ["Review the relevant concepts", "Break down the problem into steps"],
                "expected_output": "Complete solution with explanations"
            })
        
        return tasks

    def _generate_evaluation_criteria(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate evaluation criteria based on assignment type."""
        assignment_type = params.get('assignment_type', 'coding')
        quality_criterion = "Code Quality" if assignment_type == 'coding' else "Analysis Quality"
        
        return [
            {
                "criterion": "Correctness",
                "weight": 0.4,
                "description": "Solutions are correct and complete",
                "bloom_level": "Apply"
            },
            {
                "criterion": "Understanding",
                "weight": 0.3,
                "description": "Demonstrates understanding of concepts",
                "bloom_level": "Understand"
            },
            {
                "criterion": quality_criterion,
                "weight": 0.3,
                "description": f"Quality of {quality_criterion.lower()} and documentation",
                "bloom_level": "Evaluate"
            }
        ]

    def _generate_learning_objectives(self, params: Dict[str, Any]) -> List[str]:
        """Generate learning objectives based on subject and topic."""
        subject = params.get('subject', 'the subject')
        topic = params.get('topic', subject)
        
        return [
            f"Apply {subject} concepts to solve practical problems",
            f"Analyze complex scenarios in {topic}",
            f"Evaluate different approaches to problem-solving in {subject}",
            f"Create comprehensive solutions for {topic} challenges"
        ]

    def _parse_text_response(
        self,
        response: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse text response into structured format.

        Args:
            response: Raw text response
            params: Original parameters

        Returns:
            Dict[str, Any]: Structured task data
        """
        tasks = []
        current_task = {}
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_task.get('title'):
                    tasks.append(current_task)
                    current_task = {}
                continue
                
            if line.lower().startswith(('task', 'question')) or re.match(r'^\d+\.', line):
                if current_task.get('title'):
                    tasks.append(current_task)
                current_task = {'title': line}
            elif ':' in line and not current_task.get('description'):
                parts = line.split(':', 1)
                current_task['title'] = parts[0].strip()
                current_task['description'] = parts[1].strip()
            elif not current_task.get('description'):
                current_task['description'] = line
            elif 'point' in line.lower() or 'marks' in line.lower():
                try:
                    points = re.findall(r'\d+', line)
                    if points:
                        current_task['points'] = int(points[0])
                except (ValueError, IndexError):
                    current_task['points'] = params.get('max_marks', 100) // max(params.get('num_tasks', 5), 1)
            else:
                if 'requirements' not in current_task:
                    current_task['requirements'] = []
                current_task['requirements'].append(line)
        
        # Add the last task
        if current_task.get('title'):
            tasks.append(current_task)

        # Ensure each task has required fields
        for i, task in enumerate(tasks):
            task['task_id'] = f"task_{i+1}"
            task['points'] = task.get('points', params.get('max_marks', 100) // max(len(tasks), 1))
            task['bloom_level'] = task.get('bloom_level', self.BLOOM_LEVELS[i % len(self.BLOOM_LEVELS)])
            task['requirements'] = task.get('requirements', [])
            task['hints'] = task.get('hints', [])
            task['expected_output'] = task.get('expected_output', 'Complete solution with explanations')
            
            if params.get('include_starter_code'):
                task['starter_code'] = task.get('starter_code', f'# TODO: Implement {task["title"]}')
            if params.get('include_solutions'):
                task['solution_code'] = task.get('solution_code', f'# Solution for {task["title"]}')
            if params.get('include_test_cases'):
                task['test_cases'] = task.get('test_cases', [])

        return {'tasks': tasks}
