from pydantic import ValidationError

from app.domain_models import RequirementAnalysis, StageResult, StageStatus
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
