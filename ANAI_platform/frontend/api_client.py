"""
API client for AssessNex AI frontend.

This module provides utilities for communicating with the backend API.
"""

import requests
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import StreamlitConfig


logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with AssessNex AI backend API."""

    def __init__(self, base_url: str = StreamlitConfig.API_BASE_URL):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
        self.timeout = 600  # 10 minutes for long-running requests
        self.session = requests.Session()
        
        # Setup retry strategy for robustness
        self._setup_retries()

        logger.info(f"API Client initialized with base URL: {base_url}")
    
    def _setup_retries(self):
        """Setup retry strategy with exponential backoff."""
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            progress_callback: Optional callback for progress updates
            **kwargs: Additional request parameters

        Returns:
            Dict[str, Any]: API response

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                logger.debug(f"{method} {url} (attempt {retry_count + 1}/{max_retries})")
                
                if progress_callback:
                    progress_callback(f"Attempt {retry_count + 1}/{max_retries}...")

                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs,
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout (attempt {retry_count + 1}): {url}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    if progress_callback:
                        progress_callback(f"Timeout, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Request timeout after {max_retries} retries: {str(e)}")
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {retry_count + 1}): {url}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    if progress_callback:
                        progress_callback(f"Connection error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Connection error after {max_retries} retries: {str(e)}")
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

    def health_check(self) -> bool:
        """
        Check API health.

        Returns:
            bool: True if API is healthy
        """
        try:
            response = self._make_request("GET", "/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def get_subjects(self) -> List[str]:
        """
        Get list of available subjects.

        Returns:
            List[str]: Available subjects
        """
        try:
            logger.info("Fetching subjects")
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/questions/subjects"
            )
            subjects = response.get("subjects", [])
            logger.info(f"Retrieved {len(subjects)} subjects")
            return subjects
        except Exception as e:
            logger.error(f"Error fetching subjects: {str(e)}")
            raise

    def get_question_info(self) -> Dict[str, Any]:
        """
        Get question generation information.

        Returns:
            Dict[str, Any]: Question type and difficulty information
        """
        try:
            logger.info("Fetching question info")
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/questions/info"
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching question info: {str(e)}")
            raise

    def generate_questions(
        self,
        subject: str,
        question_type: str,
        difficulty_level: str,
        num_questions: int,
        additional_context: Optional[str] = None,
        diagram_format: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate questions using the backend API (legacy method).

        Args:
            subject: Subject area
            question_type: Type of questions
            difficulty_level: Difficulty level
            num_questions: Number of questions
            additional_context: Optional additional context
            diagram_format: Optional format for diagrams
            progress_callback: Optional callback for progress updates

        Returns:
            Dict[str, Any]: Generated questions response
        """
        try:
            logger.info(f"Generating {num_questions} {question_type} questions for {subject}")
            
            if progress_callback:
                progress_callback(f"Generating {num_questions} questions...")

            payload = {
                "subject": subject,
                "question_type": question_type,
                "difficulty_level": difficulty_level,
                "num_questions": num_questions,
            }

            if additional_context:
                payload["additional_context"] = additional_context
            if diagram_format:
                payload["diagram_format"] = diagram_format

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/questions/generate",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated questions")
            return response

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise

    # ========================================================================
    # BLOOM'S TAXONOMY CUSTOMIZED QUESTION GENERATION
    # ========================================================================
    
    def generate_customized_question(
        self,
        topic: str,
        bloom_level: str,
        question_type: str = "Multiple Choice",
        chat_context: str = "",
        topic_focus: str = "",
        document_text: Optional[str] = None,
        additional_context: Optional[str] = None,
        require_bloom_justification: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a customized question calibrated to a specific Bloom's taxonomy level.
        
        Args:
            topic: Main subject/topic for question
            bloom_level: Bloom's taxonomy level
            question_type: Type of question to generate
            chat_context: User's chat message or context for customization
            topic_focus: Comma-separated specific subtopics to focus on
            document_text: Extracted text from uploaded document
            additional_context: Additional context from user
            require_bloom_justification: Whether explanations should justify Bloom's level
            progress_callback: Optional callback for progress updates

        Returns:
            Dict[str, Any]: Generated customized question with Bloom's calibration
        """
        try:
            logger.info(f"Generating customized {bloom_level} level question for topic: {topic}")
            
            if progress_callback:
                progress_callback(f"🎯 Generating {bloom_level} level question...")

            # Create request body as JSON
            payload = {
                "topic": topic,
                "bloom_level": bloom_level,
                "question_type": question_type,
                "chat_context": chat_context,
                "topic_focus": topic_focus,
                "document_text": document_text,
                "additional_context": additional_context,
                "require_bloom_justification": require_bloom_justification
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/questions/customized",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated customized {bloom_level} question")
            return response

        except Exception as e:
            logger.error(f"Error generating customized question: {str(e)}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            raise

    def generate_customized_question_with_document(
        self,
        topic: str,
        bloom_level: str,
        file_bytes: bytes,
        file_type: str,
        question_type: str = "Multiple Choice",
        chat_context: str = "",
        topic_focus: str = "",
        additional_context: Optional[str] = None,
        require_bloom_justification: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a customized question with document upload.
        First parses the document, then generates question with extracted context.
        
        Args:
            topic: Main subject/topic for question
            bloom_level: Bloom's taxonomy level
            file_bytes: Uploaded file bytes
            file_type: MIME type of the file
            question_type: Type of question
            chat_context: User's chat message
            topic_focus: Specific subtopics to focus on
            additional_context: Additional context
            require_bloom_justification: Whether to include justification
            progress_callback: Optional callback

        Returns:
            Dict[str, Any]: Generated question
        """
        try:
            # Step 1: Parse document
            if progress_callback:
                progress_callback("📄 Parsing document...")
            
            if file_type == "application/pdf":
                parse_response = self.parse_pdf(file_bytes)
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                parse_response = self.parse_docx(file_bytes)
            else:  # text/plain
                parse_response = {"text": file_bytes.decode('utf-8')}
            
            document_text = parse_response.get("text", "")
            
            if progress_callback:
                progress_callback(f"✅ Document parsed: {len(document_text)} characters")
            
            # Step 2: Generate question with document context
            return self.generate_customized_question(
                topic=topic,
                bloom_level=bloom_level,
                question_type=question_type,
                chat_context=chat_context,
                topic_focus=topic_focus,
                document_text=document_text,
                additional_context=additional_context,
                require_bloom_justification=require_bloom_justification,
                progress_callback=progress_callback
            )
            
        except Exception as e:
            logger.error(f"Error in document-based question generation: {str(e)}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            raise

    def generate_customized_questions_batch(
        self,
        requests: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple customized questions in batch.
        
        Args:
            requests: List of request parameters, each containing:
                - topic: Subject area
                - bloom_level: Bloom's taxonomy level
                - question_type: Type of question
                - chat_context: Optional context
                - topic_focus: Optional specific subtopics
            progress_callback: Optional callback for progress updates

        Returns:
            List[Dict[str, Any]]: Generated questions
        """
        try:
            logger.info(f"Generating batch of {len(requests)} customized questions")
            
            if progress_callback:
                progress_callback(f"📚 Generating {len(requests)} questions...")

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/questions/customized/batch",
                json=requests,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated batch of {len(requests)} questions")
            return response

        except Exception as e:
            logger.error(f"Error generating batch questions: {str(e)}")
            raise

    def generate_customized_question_legacy(
        self,
        topic: str,
        difficulty: str,
        chat_context: str = "",
        question_type: str = "Multiple Choice",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate customized question using legacy difficulty levels.
        Maps Easy/Medium/Hard to Bloom's taxonomy levels.
        
        Args:
            topic: Main topic for question
            difficulty: Traditional difficulty (Easy, Medium, Hard)
            chat_context: User's chat message
            question_type: Type of question
            progress_callback: Optional callback

        Returns:
            Dict[str, Any]: Generated question with Bloom's mapping
        """
        try:
            logger.info(f"Generating legacy customized question with difficulty: {difficulty}")
            
            if progress_callback:
                progress_callback(f"🔄 Converting {difficulty} to Bloom's level...")

            params = {
                "topic": topic,
                "difficulty": difficulty,
                "chat_context": chat_context,
                "question_type": question_type,
            }

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/questions/customized/legacy",
                params=params,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated legacy customized question")
            return response

        except Exception as e:
            logger.error(f"Error generating legacy customized question: {str(e)}")
            raise

    # ========================================================================
    # BLOOM'S TAXONOMY UTILITY METHODS
    # ========================================================================
    
    def get_bloom_taxonomy_levels(self) -> List[str]:
        """
        Get available Bloom's taxonomy levels.
        
        Returns:
            List[str]: List of Bloom's taxonomy levels
        """
        return ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    
    def get_bloom_level_description(self, bloom_level: str) -> Dict[str, str]:
        """
        Get description and action verbs for a Bloom's taxonomy level.
        
        Args:
            bloom_level: Bloom's taxonomy level
            
        Returns:
            Dict with description, cognitive demand, and action verbs
        """
        descriptions = {
            "Remember": {
                "description": "Recall facts, terms, basic concepts",
                "cognitive_demand": "Lowest - simple recall",
                "verbs": "Define, List, Recall, Name, Identify, State",
                "icon": "🔵"
            },
            "Understand": {
                "description": "Explain ideas or concepts",
                "cognitive_demand": "Low - demonstrate comprehension",
                "verbs": "Explain, Describe, Summarize, Interpret, Paraphrase, Classify",
                "icon": "🟢"
            },
            "Apply": {
                "description": "Use information in new situations",
                "cognitive_demand": "Medium - execute or implement",
                "verbs": "Apply, Demonstrate, Implement, Solve, Use, Compute",
                "icon": "🟠"
            },
            "Analyze": {
                "description": "Draw connections among ideas",
                "cognitive_demand": "Medium-High - distinguish, organize, attribute",
                "verbs": "Analyze, Compare, Contrast, Differentiate, Examine, Investigate",
                "icon": "🟣"
            },
            "Evaluate": {
                "description": "Justify a stand or decision",
                "cognitive_demand": "High - check, critique, judge",
                "verbs": "Evaluate, Critique, Assess, Justify, Debate, Recommend",
                "icon": "🔴"
            },
            "Create": {
                "description": "Produce new or original work",
                "cognitive_demand": "Highest - generate, plan, produce",
                "verbs": "Design, Develop, Formulate, Propose, Construct, Synthesize",
                "icon": "🟤"
            }
        }
        return descriptions.get(bloom_level, descriptions["Understand"])

    # ========================================================================
    # ASSIGNMENT METHODS (FIXED FOR QUERY PARAMETERS)
    # ========================================================================

    def generate_assignment(
        self,
        name: str,
        course_code: str,
        subject: str,
        assignment_type: str,
        difficulty: str,
        max_marks: int,
        duration_days: int,
        num_tasks: int,
        description: str,
        include_solutions: bool = True,
        include_starter_code: bool = True,
        include_test_cases: bool = True,
        topic: Optional[str] = None,
        bloom_distribution: Optional[Dict[str, int]] = None,
        chat_context: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an assignment with Bloom's taxonomy support.
        Uses query parameters as expected by the backend.

        Args:
            name: Assignment name
            course_code: Course code
            subject: Subject area
            assignment_type: Type of assignment
            difficulty: Difficulty level
            max_marks: Maximum marks
            duration_days: Duration in days
            num_tasks: Number of tasks
            description: Assignment description
            include_solutions: Whether to include solutions
            include_starter_code: Whether to include starter code
            include_test_cases: Whether to include test cases
            topic: Specific topic
            bloom_distribution: Distribution of Bloom's levels
            chat_context: Additional context from chat
            progress_callback: Optional callback

        Returns:
            Dict[str, Any]: Generated assignment
        """
        try:
            logger.info(f"Generating assignment with Bloom's taxonomy: {name}")
            
            if progress_callback:
                progress_callback("📚 Generating assignment with Bloom's taxonomy...")

            # Map assignment type to backend format
            type_mapping = {
                "Coding Problem": "coding",
                "Essay": "theoretical",
                "Case Study": "theoretical",
                "Problem Solving": "mixed",
                "Research": "theoretical",
                "Project": "project",
                "Theoretical": "theoretical",
                "Practical": "lab"
            }
            backend_type = type_mapping.get(assignment_type, "coding")

            # Prepare query parameters (not JSON body)
            params = {
                "name": name,
                "course_code": course_code,
                "subject": subject,
                "assignment_type": backend_type,
                "difficulty": difficulty.lower() if difficulty != "custom" else "custom",
                "max_marks": max_marks,
                "duration_days": duration_days,
                "num_tasks": num_tasks,
                "description": description,
                "include_solutions": str(include_solutions).lower(),
                "include_starter_code": str(include_starter_code).lower(),
                "include_test_cases": str(include_test_cases).lower()
            }

            # Add optional parameters
            if topic:
                params["topic"] = topic
            
            # Add Bloom's distribution if provided
            if bloom_distribution:
                # Convert dict to JSON string for query parameter
                import json
                params["bloom_distribution"] = json.dumps(bloom_distribution)
            
            if chat_context:
                params["chat_context"] = chat_context

            # Make request with query parameters (not JSON)
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/assignments/generate",
                params=params,  # Using params, not json
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated assignment: {name}")
            return response

        except Exception as e:
            logger.error(f"Error generating assignment: {str(e)}")
            raise

    def generate_assignment_from_document(
        self,
        document_text: str,
        name: str,
        course_code: str,
        subject: str,
        assignment_type: str,
        difficulty: str,
        max_marks: int,
        duration_days: int,
        num_tasks: int,
        description: str,
        bloom_distribution: Optional[Dict[str, int]] = None,
        chat_context: Optional[str] = None,
        topic: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an assignment from document context with Bloom's taxonomy.
        Uses query parameters as expected by the backend.

        Args:
            document_text: Extracted text from document
            name: Assignment name
            course_code: Course code
            subject: Subject area
            assignment_type: Type of assignment
            difficulty: Difficulty level
            max_marks: Maximum marks
            duration_days: Duration in days
            num_tasks: Number of tasks
            description: Assignment description
            bloom_distribution: Distribution of Bloom's levels
            chat_context: Additional context from chat
            topic: Specific topic
            progress_callback: Optional callback

        Returns:
            Dict[str, Any]: Generated assignment
        """
        try:
            logger.info(f"Generating assignment from document with Bloom's taxonomy: {name}")
            
            if progress_callback:
                progress_callback("📄 Generating assignment from document with Bloom's taxonomy...")

            # Map assignment type to backend format
            type_mapping = {
                "Coding Problem": "coding",
                "Essay": "theoretical",
                "Case Study": "theoretical",
                "Problem Solving": "mixed",
                "Research": "theoretical",
                "Project": "project",
                "Theoretical": "theoretical",
                "Practical": "lab"
            }
            backend_type = type_mapping.get(assignment_type, "coding")

            # Prepare query parameters
            params = {
                "name": name,
                "course_code": course_code,
                "subject": subject,
                "assignment_type": backend_type,
                "difficulty": difficulty.lower() if difficulty != "custom" else "custom",
                "max_marks": max_marks,
                "duration_days": duration_days,
                "num_tasks": num_tasks,
                "description": description,
                "document_text": document_text
            }

            # Add optional parameters
            if topic:
                params["topic"] = topic
            
            # Add Bloom's distribution if provided
            if bloom_distribution:
                import json
                params["bloom_distribution"] = json.dumps(bloom_distribution)
            
            if chat_context:
                params["chat_context"] = chat_context

            # Make request with query parameters
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/generate-assignment",
                params=params,  # Using params, not json
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated assignment from document: {name}")
            return response

        except Exception as e:
            logger.error(f"Error generating assignment from document: {str(e)}")
            raise

    # ========================================================================
    # EVALUATION METHODS
    # ========================================================================

    def evaluate_paper(self, paper: Dict[str, Any], answers: Dict[str, str], student_name: str = "Student") -> Dict[str, Any]:
        """Evaluate a generated paper against student answers."""
        return self._make_request(
            "POST",
            f"{StreamlitConfig.API_V1_PREFIX}/evaluation/evaluate",
            json={"paper": paper, "answers": answers, "student_name": student_name},
        )

    def export_evaluation_pdf(self, evaluation: Dict[str, Any]) -> bytes:
        url = f"{self.base_url}{StreamlitConfig.API_V1_PREFIX}/evaluation/export-pdf"
        response = self.session.post(url, json=evaluation, timeout=self.timeout)
        response.raise_for_status()
        return response.content

    # ========================================================================
    # PAPER AND DOCUMENT METHODS
    # ========================================================================

    def generate_paper(
        self,
        exam_name: str,
        subject: str,
        topic: str,
        total_marks: int,
        duration_minutes: int,
        question_type_config: list,
        bloom_distribution: Optional[Dict[str, int]] = None,
        difficulty_distribution: Optional[Dict[str, int]] = None,
        subtopics: Optional[List[str]] = None,
        instructions: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate a question paper using the backend API."""
        try:
            logger.info(f"Generating paper: {exam_name}")
            
            if progress_callback:
                progress_callback("Generating question paper...")

            if bloom_distribution is None:
                bloom_distribution = {
                    "Remember": 10,
                    "Understand": 25,
                    "Apply": 30,
                    "Analyze": 20,
                    "Evaluate": 10,
                    "Create": 5
                }

            payload = {
                "exam_name": exam_name,
                "subject": subject,
                "topic": topic,
                "total_marks": total_marks,
                "duration_minutes": duration_minutes,
                "question_type_config": question_type_config,
                "bloom_distribution": bloom_distribution,
                "difficulty_distribution": difficulty_distribution,
                "subtopics": subtopics,
                "instructions": instructions,
                "enable_validation": True,
                "enable_metrics": True,
                "enable_explainability": True
            }

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/generate",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated paper: {exam_name}")
            return response

        except Exception as e:
            logger.error(f"Error generating paper: {str(e)}")
            raise

    def generate_paper_with_progress(
        self,
        payload: Dict[str, Any],
        progress_callback: Optional[Callable[[str, int], None]] = None,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """Start paper generation as a background job and poll real progress."""
        import time as _time

        start = self._make_request(
            "POST",
            f"{StreamlitConfig.API_V1_PREFIX}/papers/generate/async",
            json=payload,
        )
        job_id = start.get("job_id")
        if not job_id:
            raise RuntimeError("Backend did not return a paper generation job id")

        while True:
            status = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/jobs/{job_id}",
            )
            message = status.get("message", "Generating the question paper")
            progress = int(status.get("progress", 0))
            if progress_callback:
                progress_callback(message, progress)

            if status.get("status") == "completed":
                result = status.get("result") or {}
                return result
            if status.get("status") == "failed":
                raise RuntimeError(status.get("error") or message or "Paper generation failed")
            _time.sleep(poll_interval)


    def export_paper(self, paper: Dict[str, Any], fmt: str = "pdf", include_answers: bool = False) -> bytes:
        """Return a professional paper export as raw bytes."""
        url = f"{self.base_url}{StreamlitConfig.API_V1_PREFIX}/papers/export"
        response = self.session.post(url, params={"format": fmt, "include_answers": str(include_answers).lower()}, json=paper, timeout=self.timeout)
        response.raise_for_status()
        return response.content

    def save_question_to_bank(self, question: Dict[str, Any], topic: str = "") -> Dict[str, Any]:
        return self._make_request("POST", f"{StreamlitConfig.API_V1_PREFIX}/papers/question-bank/save", params={"topic": topic}, json=question)

    def search_question_bank(self, q: str = "", subject: Optional[str] = None, difficulty: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return self._make_request("GET", f"{StreamlitConfig.API_V1_PREFIX}/papers/question-bank/search", params={"q": q or None, "subject": subject, "difficulty": difficulty, "limit": limit})

    def get_bloom_levels(self) -> Dict[str, Any]:
        """Get available Bloom's taxonomy levels."""
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/bloom-levels"
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching Bloom levels: {str(e)}")
            raise

    def get_question_types(self) -> Dict[str, Any]:
        """Get question type to Bloom level mappings."""
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/question-types"
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching question types: {str(e)}")
            raise

    def get_domain_ontologies(self, subject: str) -> Dict[str, Any]:
        """Get domain-specific concepts and relationships."""
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/domain-ontologies",
                params={"subject": subject}
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching domain ontologies: {str(e)}")
            raise

    def get_template_examples(self) -> Dict[str, Any]:
        """Get template configuration examples."""
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/template-examples"
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching template examples: {str(e)}")
            raise

    def generate_paper_with_payload(
        self,
        payload: Dict[str, Any],
        progress_callback: Optional[Callable[..., None]] = None
    ) -> Dict[str, Any]:
        """Generate a question paper while exposing real backend progress."""
        try:
            def callback(message: str, progress: int):
                if progress_callback:
                    try:
                        progress_callback(message, progress)
                    except TypeError:
                        progress_callback(message)

            return self.generate_paper_with_progress(
                payload,
                progress_callback=callback,
            )
        except Exception as e:
            logger.error(f"Error generating paper: {str(e)}")
            raise

    def get_validation_report(self, paper_id: str) -> Dict[str, Any]:
        """Get detailed validation report for a paper."""
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/validation-report",
                params={"paper_id": paper_id}
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching validation report: {str(e)}")
            raise

    def parse_pdf(self, file_bytes: bytes, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Parse PDF file and extract text."""
        try:
            if progress_callback:
                progress_callback("📄 Parsing PDF...")
            
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/parse-pdf",
                files={"file": ("document.pdf", file_bytes, "application/pdf")},
                progress_callback=progress_callback,
            )
            
            logger.info("Successfully parsed PDF")
            return response
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise

    def parse_docx(self, file_bytes: bytes, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Parse DOCX file and extract text."""
        try:
            if progress_callback:
                progress_callback("📝 Parsing DOCX...")
            
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/parse-docx",
                files={"file": ("document.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                progress_callback=progress_callback,
            )
            
            logger.info("Successfully parsed DOCX")
            return response
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            raise

    def parse_document(self, file_bytes: bytes, file_type: str, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Parse any supported document type and extract text.
        
        Args:
            file_bytes: File bytes
            file_type: MIME type of the file
            progress_callback: Optional callback

        Returns:
            Dict with extracted text and metadata
        """
        if file_type == "application/pdf":
            return self.parse_pdf(file_bytes, progress_callback)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self.parse_docx(file_bytes, progress_callback)
        else:  # text/plain
            try:
                text = file_bytes.decode('utf-8')
                return {"text": text, "format": "txt"}
            except Exception as e:
                raise Exception(f"Error parsing text file: {str(e)}")

    def generate_questions_from_document(
        self,
        document_text: str,
        subject: str,
        question_type: str,
        difficulty: str,
        count: int,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Generate questions from document context."""
        try:
            if progress_callback:
                progress_callback("🔄 Generating questions from document...")
            
            payload = {
                "document_text": document_text,
                "subject": subject,
                "question_type": question_type,
                "difficulty": difficulty,
                "count": count,
            }
            
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/generate-questions",
                json=payload,
                progress_callback=progress_callback,
            )
            
            logger.info("Successfully generated questions from document")
            return response
        except Exception as e:
            logger.error(f"Error generating questions from document: {str(e)}")
            raise

    def generate_paper_from_document(
        self,
        document_text: str,
        name: str,
        course_code: str,
        subject: str,
        total_questions: int,
        total_marks: int,
        duration_minutes: int,
        distribution: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate a question paper from document context."""
        try:
            if progress_callback:
                progress_callback("📚 Generating paper from document...")
            
            payload = {
                "document_text": document_text,
                "name": name,
                "course_code": course_code,
                "subject": subject,
                "total_questions": total_questions,
                "total_marks": total_marks,
                "duration_minutes": duration_minutes,
                "distribution": distribution,
            }
            
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/generate-paper",
                json=payload,
                progress_callback=progress_callback,
            )
            
            logger.info("Successfully generated paper from document")
            return response
        except Exception as e:
            logger.error(f"Error generating paper from document: {str(e)}")
            raise

    def close(self):
        """Close the session."""
        self.session.close()
        logger.info("API Client session closed")


def get_api_client() -> APIClient:
    """
    Get API client instance.

    Returns:
        APIClient: API client instance
    """
    return APIClient()