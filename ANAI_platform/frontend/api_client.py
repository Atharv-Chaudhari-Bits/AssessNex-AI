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
        name: str,
        course_code: str,
        semester: int,
        subject: str,
        total_questions: int,
        total_marks: int,
        duration_minutes: int,
        distribution: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a question paper using the backend API.

        Args:
            name: Paper name
            course_code: Course code
            semester: Semester number
            subject: Subject area
            total_questions: Total questions in paper
            total_marks: Total marks for paper
            duration_minutes: Duration in minutes
            distribution: Question distribution (difficulty & types)
            progress_callback: Optional callback for progress updates

        Returns:
            Dict[str, Any]: Generated paper response
        """
        try:
            logger.info(f"Generating paper: {name}")
            
            if progress_callback:
                progress_callback("Generating question paper...")

            payload = {
                "name": name,
                "course_code": course_code,
                "semester": semester,
                "subject": subject,
                "total_questions": total_questions,
                "total_marks": total_marks,
                "duration_minutes": duration_minutes,
                "distribution": distribution,
            }

            response = self._make_request(
                "POST",
                f"{StreamlitConfig.API_V1_PREFIX}/papers/generate",
                json=payload,
                progress_callback=progress_callback,
            )

            logger.info(f"Successfully generated paper: {name}")
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
                f"{StreamlitConfig.API_V1_PREFIX}/papers/assignments/generate",
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
