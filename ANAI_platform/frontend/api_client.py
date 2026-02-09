"""
API client for AssessNex AI frontend.

This module provides utilities for communicating with the backend API.
"""

import requests
import logging
import time
from typing import Dict, List, Any, Optional, Callable
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
            total=3,  # Total retries
            backoff_factor=2,  # 2^x seconds backoff (1s, 2s, 4s)
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
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
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
                    logger.info(f"Retrying in {wait_time} seconds...")
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

        Raises:
            requests.exceptions.RequestException: If health check fails
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

        Raises:
            requests.exceptions.RequestException: If request fails
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

        Raises:
            requests.exceptions.RequestException: If request fails
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
        Generate questions using the backend API.

        Args:
            subject: Subject area
            question_type: Type of questions
            difficulty_level: Difficulty level
            num_questions: Number of questions
            additional_context: Optional additional context
            diagram_format: Optional format for diagrams (Mermaid/ASCII)
            progress_callback: Optional callback for progress updates

        Returns:
            Dict[str, Any]: Generated questions response

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        try:
            logger.info(
                f"Generating {num_questions} {question_type} questions "
                f"for {subject} at {difficulty_level} level"
            )
            
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
            if progress_callback:
                progress_callback("✅ Questions generated successfully!")

            return response

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            raise

    def generate_paper(
        self,
        exam_name: str,
        subject: str,
        topic: str,
        total_marks: int,
        duration_minutes: int,
        question_type_config: list,
        bloom_distribution: dict | None = None,
        difficulty_distribution: dict | None = None,
        subtopics: list | None = None,
        instructions: str | None = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a question paper using the backend API.
        """
        try:
            logger.info(f"Generating paper: {exam_name}")

            if progress_callback:
                progress_callback("Generating question paper...")

            # Default Bloom distribution if not provided
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

            if difficulty_distribution is not None:
                payload["difficulty_distribution"] = difficulty_distribution

            if subtopics:
                payload["subtopics"] = subtopics

            if instructions:
                payload["instructions"] = instructions

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/generate",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated paper: {exam_name}")
            if progress_callback:
                progress_callback("✅ Paper generated successfully!")

            return response

        except Exception as e:
            logger.error(f"Error generating paper: {str(e)}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            raise

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
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an assignment using the backend API.

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
            include_solutions: Include solution files
            include_starter_code: Include starter code files
            include_test_cases: Include test case files
            topic: Specific topic (defaults to subject)
            progress_callback: Optional callback for progress updates

        Returns:
            Dict[str, Any]: Generated assignment response
        """
        try:
            logger.info(f"Generating assignment: {name}")
            
            if progress_callback:
                progress_callback("Generating assignment with LangGraph workflow...")

            # Map frontend assignment types to backend types
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

            payload = {
                "name": name,
                "course_code": course_code,
                "subject": subject,
                "topic": topic or subject,
                "assignment_type": backend_type,
                "difficulty": difficulty.lower(),
                "max_marks": max_marks,
                "duration_days": duration_days,
                "num_tasks": num_tasks,
                "description": description,
                "include_solutions": include_solutions,
                "include_starter_code": include_starter_code,
                "include_test_cases": include_test_cases,
            }

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/assignments/generate",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated assignment: {name}")
            if progress_callback:
                progress_callback("✅ Assignment generated successfully!")

            return response

        except Exception as e:
            logger.error(f"Error generating assignment: {str(e)}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            raise

    def get_bloom_levels(self) -> Dict[str, Any]:
        """
        Get available Bloom's taxonomy levels.

        Returns:
            Dict with Bloom levels and descriptions
        """
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/bloom-levels"
            )
            logger.info("Successfully fetched Bloom levels")
            return response
        except Exception as e:
            logger.error(f"Error fetching Bloom levels: {str(e)}")
            raise

    def get_question_types(self) -> Dict[str, Any]:
        """
        Get question type to Bloom level mappings.

        Returns:
            Dict with question types and their Bloom constraints
        """
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/question-types"
            )
            logger.info("Successfully fetched question types")
            return response
        except Exception as e:
            logger.error(f"Error fetching question types: {str(e)}")
            raise

    def get_domain_ontologies(self, subject: str) -> Dict[str, Any]:
        """
        Get domain-specific concepts and relationships.

        Args:
            subject: The subject domain

        Returns:
            Dict with domain ontology information
        """
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/domain-ontologies",
                params={"subject": subject}
            )
            logger.info(f"Successfully fetched domain ontologies for {subject}")
            return response
        except Exception as e:
            logger.error(f"Error fetching domain ontologies: {str(e)}")
            raise

    def get_template_examples(self) -> Dict[str, Any]:
        """
        Get template configuration examples.

        Returns:
            Dict with template examples
        """
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/template-examples"
            )
            logger.info("Successfully fetched template examples")
            return response
        except Exception as e:
            logger.error(f"Error fetching template examples: {str(e)}")
            raise

    def generate_paper_with_payload(
        self,
        payload: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate a question paper with Bloom's taxonomy support.

        Args:
            payload: Paper generation request payload
            progress_callback: Optional callback for progress updates

        Returns:
            Generated paper with validation and metrics
        """
        try:
            if progress_callback:
                progress_callback("📤 Uploading configuration...")

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/generate",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info("Successfully generated question paper")
            if progress_callback:
                progress_callback("✅ Question paper generated successfully!")

            return response

        except Exception as e:
            logger.error(f"Error generating paper: {str(e)}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            raise

    def get_validation_report(self, paper_id: str) -> Dict[str, Any]:
        """
        Get detailed validation report for a paper.

        Args:
            paper_id: The ID of the generated paper

        Returns:
            Dict with validation details
        """
        try:
            response = self._make_request(
                "GET",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/validation-report",
                params={"paper_id": paper_id}
            )
            logger.info(f"Successfully fetched validation report for paper {paper_id}")
            return response
        except Exception as e:
            logger.error(f"Error fetching validation report: {str(e)}")
            raise

    def parse_pdf(self, file_bytes: bytes, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Parse PDF file and extract text.

        Args:
            file_bytes: PDF file bytes
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with extracted text and metadata
        """
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
        """
        Parse DOCX file and extract text.

        Args:
            file_bytes: DOCX file bytes
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with extracted text and metadata
        """
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

    def generate_questions_from_document(
        self,
        document_text: str,
        subject: str,
        question_type: str,
        difficulty: str,
        count: int,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate questions from document context.

        Args:
            document_text: Extracted document text
            subject: Subject area
            question_type: Type of questions
            difficulty: Difficulty level
            count: Number of questions
            progress_callback: Optional callback

        Returns:
            Generated questions from document
        """
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
        """
        Generate a question paper from document context.

        Args:
            document_text: Extracted document text
            name: Paper name
            course_code: Course code
            subject: Subject area
            total_questions: Total questions
            total_marks: Total marks
            duration_minutes: Duration in minutes
            distribution: Question distribution
            progress_callback: Optional callback

        Returns:
            Generated paper from document
        """
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
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an assignment from document context.

        Args:
            document_text: Extracted document text
            name: Assignment name
            course_code: Course code
            subject: Subject
            assignment_type: Type of assignment
            difficulty: Difficulty level
            max_marks: Max marks
            duration_days: Duration in days
            num_tasks: Number of tasks
            description: Description
            progress_callback: Optional callback

        Returns:
            Generated assignment from document
        """
        try:
            if progress_callback:
                progress_callback("📋 Generating assignment from document...")
            
            payload = {
                "document_text": document_text,
                "name": name,
                "course_code": course_code,
                "subject": subject,
                "assignment_type": assignment_type,
                "difficulty": difficulty,
                "max_marks": max_marks,
                "duration_days": duration_days,
                "num_tasks": num_tasks,
                "description": description,
            }
            
            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/documents/generate-assignment",
                json=payload,
                progress_callback=progress_callback,
            )
            
            logger.info("Successfully generated assignment from document")
            return response
        except Exception as e:
            logger.error(f"Error generating assignment from document: {str(e)}")
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
