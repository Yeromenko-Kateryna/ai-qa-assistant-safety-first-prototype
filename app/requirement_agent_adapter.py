import json
import re
from app.domain_models import RequirementAnalysis, StageResult, StageStatus
from app.pipeline import run_requirement_analysis_stage

# Proposed Error Codes
AGENT_DRAFT_EMPTY = "AGENT_DRAFT_EMPTY"
AGENT_DRAFT_NOT_JSON = "AGENT_DRAFT_NOT_JSON"
AGENT_DRAFT_ROOT_NOT_OBJECT = "AGENT_DRAFT_ROOT_NOT_OBJECT"
AGENT_DRAFT_UNSAFE_CONTENT = "AGENT_DRAFT_UNSAFE_CONTENT"
AGENT_DRAFT_VALIDATION_FAILED = "AGENT_DRAFT_VALIDATION_FAILED"

# Pre-parse safety check regexes (matching Slice 10 regex rules)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|password|secret|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9_-]{6,}['\"]?"
)
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_.-]{12,}\b")


def reject_secret_like_model_output(draft_text: str) -> None:
    """Checks model draft text for unsafe secret assignments or Bearer tokens.

    Raises ValueError on violation.
    """
    if SECRET_ASSIGNMENT_PATTERN.search(draft_text):
        raise ValueError("Model output contains raw secret assignments")
    if BEARER_PATTERN.search(draft_text):
        raise ValueError("Model output contains raw Bearer token pattern")


def parse_requirement_agent_draft(draft_text: str) -> StageResult[RequirementAnalysis]:
    """Parses, validates, and wraps candidate model draft text into a StageResult.

    Ensures that no raw JSON, raw model text, raw exception text, or stack traces
    leak into the safe StageResult.
    """
    # 1. Reject empty or whitespace-only draft_text
    if not draft_text or not draft_text.strip():
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_EMPTY,
            safe_message="The model draft output is empty or whitespace-only."
        )

    # 2. Obvious Markdown/plain text quick reject (avoid matching valid negative numbers like -1)
    stripped = draft_text.strip()
    if (
        stripped.startswith("#")
        or stripped.startswith("- ")
        or stripped.startswith("* ")
    ):
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_NOT_JSON,
            safe_message="The model draft output is Markdown or plain text instead of JSON."
        )

    # 3. Pre-parse safety checks (reject raw secret-like content before parsing)
    try:
        reject_secret_like_model_output(draft_text)
    except ValueError:
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_UNSAFE_CONTENT,
            committed_output=None,
            safe_message="The model draft output contains prohibited or unsafe content."
        )

    # 4. Parse JSON using stdlib json
    try:
        data = json.loads(draft_text)
    except json.JSONDecodeError:
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_NOT_JSON,
            safe_message="The model draft output is malformed JSON."
        )

    # 5. Require parsed root to be a JSON object
    if not isinstance(data, dict):
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_ROOT_NOT_OBJECT,
            safe_message="The model draft output root must be a JSON object."
        )

    # 6. Post-parse safety check on re-serialized data
    try:
        reject_secret_like_model_output(json.dumps(data))
    except ValueError:
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_UNSAFE_CONTENT,
            committed_output=None,
            safe_message="The model draft output contains prohibited or unsafe content."
        )

    # 7. Run validation by reusing existing run_requirement_analysis_stage(data)
    stage_result = run_requirement_analysis_stage(data)

    # If it fails, map it to AGENT_DRAFT_VALIDATION_FAILED with a generic safe_message
    if stage_result.status == StageStatus.FAILED:
        return StageResult(
            status=StageStatus.FAILED,
            error_code=AGENT_DRAFT_VALIDATION_FAILED,
            committed_output=None,
            safe_message="The model draft output failed validation checks."
        )

    return stage_result
