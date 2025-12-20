'''
Papers and Assignments endpoints router.
Uses LangGraph-based agents for robust generation.
'''

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from backend.app.utils import get_logger, get_current_timestamp

logger = get_logger(__name__)
router = APIRouter(prefix='/papers', tags=['papers'])

_paper_agent = None
_assignment_agent = None

def get_paper_agent():
    global _paper_agent
    if _paper_agent is None:
        from backend.app.agents.paper_agent import paper_agent
        _paper_agent = paper_agent
    return _paper_agent

def get_assignment_agent():
    global _assignment_agent
    if _assignment_agent is None:
        from backend.app.agents.assignment_agent import assignment_agent
        _assignment_agent = assignment_agent
    return _assignment_agent


class DifficultyDistribution(BaseModel):
    Easy: int = Field(default=0, ge=0)
    Medium: int = Field(default=0, ge=0)
    Hard: int = Field(default=0, ge=0)


class QuestionTypeDistribution(BaseModel):
    MCQ: int = Field(default=0, ge=0)
    ShortAnswer: int = Field(default=0, ge=0)
    LongAnswer: int = Field(default=0, ge=0)
    TrueFalse: int = Field(default=0, ge=0)
    FillBlank: int = Field(default=0, ge=0)
    Numerical: int = Field(default=0, ge=0)
    CodeImplementation: int = Field(default=0, ge=0)
    DiagramBased: int = Field(default=0, ge=0)
    
    def total(self) -> int:
        return (self.MCQ + self.ShortAnswer + self.LongAnswer + 
                self.TrueFalse + self.FillBlank + self.Numerical +
                self.CodeImplementation + self.DiagramBased)
    
    def to_config_list(self) -> List[Dict]:
        type_mapping = {
            'MCQ': ('Multiple Choice', 1),
            'ShortAnswer': ('Short Answer', 3),
            'LongAnswer': ('Long Answer', 8),
            'TrueFalse': ('True/False', 1),
            'FillBlank': ('Fill in the Blank', 1),
            'Numerical': ('Numerical', 4),
            'CodeImplementation': ('Code Writing', 10),
            'DiagramBased': ('Diagram Based', 4)
        }
        configs = []
        for key, (q_type, default_marks) in type_mapping.items():
            count = getattr(self, key, 0)
            if count > 0:
                configs.append({
                    'type': q_type,
                    'count': count,
                    'marks_each': default_marks,
                    'difficulty': 'mixed'
                })
        return configs


class PaperDistribution(BaseModel):
    difficulty: DifficultyDistribution
    types: QuestionTypeDistribution


class PaperGenerationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    course_code: str = Field(..., min_length=1, max_length=20)
    semester: int = Field(..., ge=1, le=8)
    subject: str = Field(..., min_length=1, max_length=100)
    total_questions: int = Field(..., ge=1, le=100)
    total_marks: int = Field(..., ge=10, le=500)
    duration_minutes: int = Field(..., ge=15, le=300)
    distribution: PaperDistribution
    context: Optional[str] = None
    subtopics: Optional[List[str]] = None
    instructions: Optional[List[str]] = None


class PaperGenerationResponse(BaseModel):
    status: str
    message: str
    data: Dict


class AssignmentGenerationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    course_code: str = Field(..., min_length=1, max_length=20)
    subject: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., min_length=1, max_length=200)
    assignment_type: str = Field(default='coding')
    difficulty: str = Field(default='intermediate')
    max_marks: int = Field(default=100, ge=10, le=500)
    duration_days: int = Field(default=7, ge=1, le=365)
    num_tasks: int = Field(default=3, ge=1, le=10)
    description: str = Field(default='', max_length=2000)
    include_solutions: bool = Field(default=True)
    include_starter_code: bool = Field(default=True)
    include_test_cases: bool = Field(default=True)


class AssignmentGenerationResponse(BaseModel):
    status: str
    message: str
    data: Dict


@router.post('/generate', response_model=PaperGenerationResponse)
async def generate_paper(request: PaperGenerationRequest) -> PaperGenerationResponse:
    try:
        logger.info(f'Generating paper: {request.name}')
        
        difficulty_sum = request.distribution.difficulty.Easy + request.distribution.difficulty.Medium + request.distribution.difficulty.Hard
        types_total = request.distribution.types.total()
        
        if difficulty_sum != request.total_questions:
            raise HTTPException(status_code=400, detail=f'Difficulty distribution must sum to {request.total_questions}')
        
        if types_total != request.total_questions:
            raise HTTPException(status_code=400, detail=f'Type distribution must sum to {request.total_questions}')
        
        agent = get_paper_agent()
        question_type_config = request.distribution.types.to_config_list()
        
        difficulty_distribution = {
            'easy': int((request.distribution.difficulty.Easy / request.total_questions) * 100),
            'medium': int((request.distribution.difficulty.Medium / request.total_questions) * 100),
            'hard': int((request.distribution.difficulty.Hard / request.total_questions) * 100)
        }
        
        paper = await agent.generate_paper(
            subject=request.subject,
            topic=request.context or request.subject,
            total_marks=request.total_marks,
            duration_minutes=request.duration_minutes,
            question_type_config=question_type_config,
            difficulty_distribution=difficulty_distribution,
            exam_name=request.name,
            subtopics=request.subtopics,
            instructions=request.instructions
        )
        
        if 'error' in paper:
            raise HTTPException(status_code=500, detail=paper['error'])
        
        paper['course_code'] = request.course_code
        paper['semester'] = request.semester
        paper['generated_at'] = get_current_timestamp()
        
        all_questions = []
        question_num = 1
        for section in paper.get('sections', []):
            for q in section.get('questions', []):
                q['question_number'] = question_num
                q['section'] = section.get('section_id', 'A')
                all_questions.append(q)
                question_num += 1
        
        paper['questions'] = all_questions
        paper['total_questions'] = len(all_questions)
        
        return PaperGenerationResponse(
            status='success',
            message=f'Paper generated with {len(all_questions)} questions',
            data=paper
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error generating paper: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/assignments/generate', response_model=AssignmentGenerationResponse)
async def generate_assignment(request: AssignmentGenerationRequest) -> AssignmentGenerationResponse:
    try:
        logger.info(f'Generating assignment: {request.name}')
        
        agent = get_assignment_agent()
        
        assignment = await agent.generate_assignment(
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty,
            assignment_type=request.assignment_type,
            num_tasks=request.num_tasks,
            include_solutions=request.include_solutions,
            include_starter_code=request.include_starter_code,
            include_test_cases=request.include_test_cases,
            custom_instructions=request.description
        )
        
        if 'error' in assignment:
            raise HTTPException(status_code=500, detail=assignment['error'])
        
        assignment['name'] = request.name
        assignment['course_code'] = request.course_code
        assignment['max_marks'] = request.max_marks
        assignment['duration_days'] = request.duration_days
        assignment['generated_at'] = get_current_timestamp()
        
        num_files = len(assignment.get('generated_files', []))
        num_tasks = len(assignment.get('tasks', []))
        
        return AssignmentGenerationResponse(
            status='success',
            message=f'Assignment generated with {num_tasks} tasks and {num_files} files',
            data=assignment
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error generating assignment: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/templates')
async def get_paper_templates() -> Dict[str, Any]:
    return {
        'status': 'success',
        'templates': {
            'midterm': {'name': 'Midterm', 'duration_minutes': 90, 'total_marks': 50},
            'final': {'name': 'Final', 'duration_minutes': 180, 'total_marks': 100},
            'quiz': {'name': 'Quiz', 'duration_minutes': 30, 'total_marks': 20}
        }
    }


@router.get('/assignment-types')
async def get_assignment_types() -> Dict[str, Any]:
    return {
        'status': 'success',
        'types': {
            'coding': {'name': 'Coding Assignment', 'description': 'Programming tasks'},
            'theoretical': {'name': 'Theoretical', 'description': 'Essay and analysis'},
            'mixed': {'name': 'Mixed', 'description': 'Combination of tasks'},
            'project': {'name': 'Project', 'description': 'Large-scale project'},
            'lab': {'name': 'Lab', 'description': 'Hands-on lab exercises'}
        }
    }
