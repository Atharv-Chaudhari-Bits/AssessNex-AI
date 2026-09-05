"""
Explainability and Traceability System for Question Generation.

Provides comprehensive logging of prompt-to-output mappings, decision tracking,
and audit trails for transparency and quality assurance.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionType(str, Enum):
    """Types of decisions logged in the generation process."""
    SUBJECT_SELECTION = "subject_selection"
    QUESTION_TYPE_SELECTION = "question_type_selection"
    DIFFICULTY_CALIBRATION = "difficulty_calibration"
    BLOOM_LEVEL_SELECTION = "bloom_level_selection"
    PROMPT_ENGINEERING = "prompt_engineering"
    VALIDATION_CHECK = "validation_check"
    FORMATTING_DECISION = "formatting_decision"
    REFINEMENT = "refinement"


@dataclass
class GenerationDecision:
    """Records a single decision in the generation process."""
    decision_type: DecisionType
    description: str
    input_params: Dict[str, Any]
    output_params: Dict[str, Any]
    reasoning: str
    confidence_score: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['decision_type'] = self.decision_type.value
        return data


@dataclass
class PromptMapping:
    """Maps a prompt to generated output with metadata."""
    prompt_id: str
    prompt_type: str  # 'question_generation', 'paper_generation', etc.
    input_prompt: str
    llm_model: str
    llm_provider: str
    temperature: float
    max_tokens: int
    generated_output: str
    processing_time_seconds: float
    token_usage: Dict[str, int]
    validation_score: float
    decisions_made: List[GenerationDecision]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['decisions_made'] = [d.to_dict() for d in self.decisions_made]
        return data


class GenerationAuditTrail:
    """
    Maintains detailed audit trail for question and paper generation.

    Tracks all decisions, prompts, outputs, and validation results.
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize audit trail.

        Args:
            log_dir: Directory to store audit logs (default: ./audit_logs)
        """
        self.log_dir = Path(log_dir) if log_dir else Path("audit_logs")
        self.log_dir.mkdir(exist_ok=True)
        self.current_session_id = datetime.utcnow().isoformat()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.info(f"GenerationAuditTrail initialized with log dir: {self.log_dir}")

    def start_session(self, session_type: str, user_id: Optional[str] = None) -> str:
        """
        Start a new audit session.

        Args:
            session_type: Type of session (e.g., 'question_generation', 'paper_generation')
            user_id: Optional user identifier

        Returns:
            str: Session ID
        """
        session_id = f"{session_type}_{datetime.utcnow().isoformat()}"
        self.sessions[session_id] = {
            'session_type': session_type,
            'user_id': user_id,
            'start_time': datetime.utcnow().isoformat(),
            'prompts': [],
            'decisions': [],
            'validations': [],
            'outputs': [],
            'metadata': {}
        }
        logger.info(f"Audit session started: {session_id}")
        return session_id

    def log_prompt_mapping(self, session_id: str, mapping: PromptMapping):
        """
        Log a prompt-output mapping.

        Args:
            session_id: The session ID
            mapping: PromptMapping object
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return

        self.sessions[session_id]['prompts'].append(mapping.to_dict())
        logger.debug(f"Logged prompt mapping {mapping.prompt_id} in session {session_id}")

    def log_decision(self, session_id: str, decision: GenerationDecision):
        """
        Log a generation decision.

        Args:
            session_id: The session ID
            decision: GenerationDecision object
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return

        self.sessions[session_id]['decisions'].append(decision.to_dict())
        logger.debug(f"Logged decision: {decision.decision_type.value}")

    def log_validation(self, session_id: str, question_id: str, validation_result: Dict[str, Any]):
        """
        Log validation results.

        Args:
            session_id: The session ID
            question_id: The question ID being validated
            validation_result: Validation result data
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return

        self.sessions[session_id]['validations'].append({
            'question_id': question_id,
            'result': validation_result,
            'timestamp': datetime.utcnow().isoformat()
        })

    def log_output(self, session_id: str, output: Dict[str, Any], output_type: str):
        """
        Log generated output.

        Args:
            session_id: The session ID
            output: The generated output
            output_type: Type of output (question/paper/assignment)
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return

        self.sessions[session_id]['outputs'].append({
            'type': output_type,
            'data': output,
            'timestamp': datetime.utcnow().isoformat()
        })

    def end_session(self, session_id: str, status: str, summary: Optional[Dict[str, Any]] = None):
        """
        End an audit session.

        Args:
            session_id: The session ID
            status: Final status (success/failure)
            summary: Optional summary information
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return

        self.sessions[session_id]['end_time'] = datetime.utcnow().isoformat()
        self.sessions[session_id]['status'] = status
        if summary:
            self.sessions[session_id]['summary'] = summary

        # Save session to file
        self._save_session(session_id)
        logger.info(f"Audit session ended: {session_id}")

    def _save_session(self, session_id: str):
        """Save session to file."""
        session_data = self.sessions[session_id]
        filename = f"{session_id.replace(':', '-')}.json"
        filepath = self.log_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            logger.info(f"Session saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive report for a session.

        Args:
            session_id: The session ID

        Returns:
            Dict with comprehensive session report
        """
        if session_id not in self.sessions:
            return {'error': f'Session {session_id} not found'}

        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'type': session.get('session_type'),
            'start_time': session.get('start_time'),
            'end_time': session.get('end_time'),
            'status': session.get('status'),
            'total_prompts': len(session.get('prompts', [])),
            'total_decisions': len(session.get('decisions', [])),
            'total_validations': len(session.get('validations', [])),
            'total_outputs': len(session.get('outputs', [])),
            'summary': session.get('summary'),
            'decisions_by_type': self._count_decisions_by_type(session),
        }

    def _count_decisions_by_type(self, session: Dict[str, Any]) -> Dict[str, int]:
        """Count decisions by type in a session."""
        counts = {}
        for decision in session.get('decisions', []):
            dec_type = decision.get('decision_type', 'unknown')
            counts[dec_type] = counts.get(dec_type, 0) + 1
        return counts


class ExplainabilityLogger:
    """
    High-level interface for explainability logging.

    Simplifies logging of generation processes with structured methods.
    """

    def __init__(self, audit_trail: Optional[GenerationAuditTrail] = None):
        """
        Initialize explainability logger.

        Args:
            audit_trail: Optional GenerationAuditTrail instance
        """
        self.audit_trail = audit_trail or GenerationAuditTrail()
        self.current_session_id: Optional[str] = None
        logger.info("ExplainabilityLogger initialized")

    def start_generation_session(self, gen_type: str, user_id: Optional[str] = None) -> str:
        """
        Start a generation session.

        Args:
            gen_type: Type of generation (question/paper/assignment)
            user_id: Optional user ID

        Returns:
            str: Session ID
        """
        self.current_session_id = self.audit_trail.start_session(gen_type, user_id)
        return self.current_session_id

    def log_llm_interaction(
        self,
        prompt: str,
        response: str,
        model: str,
        provider: str,
        params: Dict[str, Any],
        processing_time: float,
        token_usage: Dict[str, int],
        validation_score: float = 1.0,
        decisions: Optional[List[GenerationDecision]] = None
    ):
        """
        Log LLM interaction (prompt and response).

        Args:
            prompt: The input prompt
            response: The generated response
            model: Model name
            provider: Provider name
            params: LLM parameters (temperature, max_tokens, etc.)
            processing_time: Time taken for generation
            token_usage: Token usage stats
            validation_score: Quality/validation score
            decisions: Optional list of decisions made
        """
        if not self.current_session_id:
            logger.warning("No active session")
            return

        prompt_id = f"prompt_{datetime.utcnow().isoformat()}"
        mapping = PromptMapping(
            prompt_id=prompt_id,
            prompt_type="question_generation",
            input_prompt=prompt[:1000],  # Truncate for storage
            llm_model=model,
            llm_provider=provider,
            temperature=params.get('temperature', 0.7),
            max_tokens=params.get('max_tokens', 2048),
            generated_output=response[:2000],  # Truncate for storage
            processing_time_seconds=processing_time,
            token_usage=token_usage,
            validation_score=validation_score,
            decisions_made=decisions or [],
            timestamp=datetime.utcnow().isoformat()
        )

        self.audit_trail.log_prompt_mapping(self.current_session_id, mapping)

    def log_difficulty_calibration(
        self,
        base_difficulty: str,
        adjusted_difficulty: str,
        bloom_level: str,
        reasoning: str,
        confidence: float
    ):
        """Log difficulty calibration decision."""
        if not self.current_session_id:
            return

        decision = GenerationDecision(
            decision_type=DecisionType.DIFFICULTY_CALIBRATION,
            description=f"Calibrated {base_difficulty} → {adjusted_difficulty} (Bloom: {bloom_level})",
            input_params={'base_difficulty': base_difficulty, 'bloom_level': bloom_level},
            output_params={'adjusted_difficulty': adjusted_difficulty},
            reasoning=reasoning,
            confidence_score=confidence,
            timestamp=datetime.utcnow().isoformat()
        )
        self.audit_trail.log_decision(self.current_session_id, decision)

    def log_validation_check(
        self,
        question_id: str,
        validation_result: Dict[str, Any]
    ):
        """Log validation check results."""
        if not self.current_session_id:
            return

        self.audit_trail.log_validation(
            self.current_session_id,
            question_id,
            validation_result
        )

    def end_generation_session(self, status: str, summary: Optional[Dict[str, Any]] = None):
        """
        End the current generation session.

        Args:
            status: Final status (success/failure)
            summary: Optional summary data
        """
        if self.current_session_id:
            self.audit_trail.end_session(self.current_session_id, status, summary)
            report = self.audit_trail.get_session_report(self.current_session_id)
            logger.info(f"Session summary: {report}")
            self.current_session_id = None

    def get_current_session_report(self) -> Dict[str, Any]:
        """Get report for current session."""
        if not self.current_session_id:
            return {'error': 'No active session'}
        return self.audit_trail.get_session_report(self.current_session_id)


# Singleton instance
_explainability_logger = None


def get_explainability_logger() -> ExplainabilityLogger:
    """Get or create explainability logger."""
    global _explainability_logger
    if _explainability_logger is None:
        _explainability_logger = ExplainabilityLogger()
    return _explainability_logger
