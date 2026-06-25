from pydantic import ValidationError

from app.domain_models import RequirementAnalysis, StageResult, StageStatus
from app.input_safety import sanitize_requirement_text
from app.validator import validate_requirement_analysis


def run_requirement_analysis_stage(
    candidate_data: dict,
) -> StageResult[RequirementAnalysis]:
    """Runs structural and semantic validation on RequirementAnalysis candidate."""
    try:
        analysis = RequirementAnalysis.model_validate(candidate_data)
        validate_requirement_analysis(analysis)
        return StageResult(
            status=StageStatus.SUCCESS,
            committed_output=analysis,
            error_code=None,
            safe_message=None,
        )
    except ValidationError:
        return StageResult(
            status=StageStatus.FAILED,
            committed_output=None,
            error_code="STRUCTURAL_VALIDATION_FAILED",
            safe_message="RequirementAnalysis failed structural validation.",
        )
    except ValueError:
        return StageResult(
            status=StageStatus.FAILED,
            committed_output=None,
            error_code="SEMANTIC_VALIDATION_FAILED",
            safe_message="RequirementAnalysis failed semantic validation.",
        )


def run_requirement_analysis_pipeline_from_text(
    raw_text: str,
) -> StageResult[RequirementAnalysis]:
    """Sanitizes raw requirement text and validates a deterministic requirement analysis stub candidate."""
    # 1. Pass raw text through the deterministic safety gate
    envelope = sanitize_requirement_text(raw_text)

    # 2. Extract only the sanitized segment text (raw_text is not stored or passed downstream)
    sanitized_text = envelope.segments[0].text

    # 3. Construct a deterministic stub candidate utilizing the sanitized text
    candidate_data = {
        "summary": {
            "text": sanitized_text,
            "provenance": {
                "origin": "EXTRACTED",
                "transformation": "SUMMARY",
                "source_segment_ids": ["SEG-001"],
                "derived_from_ids": [],
                "rationale": None,
            },
        },
        "requirements": [
            {
                "id": "REQ-001",
                "description": sanitized_text,
                "category": "FUNCTIONAL",
                "provenance": {
                    "origin": "EXTRACTED",
                    "transformation": "VERBATIM",
                    "source_segment_ids": ["SEG-001"],
                    "derived_from_ids": [],
                    "rationale": None,
                },
            }
        ],
        "acceptance_criteria": [],
        "business_rules": [],
        "ambiguities": [],
        "missing_information": [],
        "assumptions": [],
    }

    # 4. Invoke the validated stage runner and return its result
    return run_requirement_analysis_stage(candidate_data)
