import pytest
from pydantic import ValidationError

from app.domain_models import RequirementAnalysis, StageResult, StageStatus
from app.pipeline import run_requirement_analysis_stage


def make_valid_candidate_data(unsafe_text: str = "A valid summary") -> dict:
    return {
        "summary": {
            "text": unsafe_text,
            "provenance": {
                "origin": "EXTRACTED",
                "transformation": "VERBATIM",
                "source_segment_ids": ["SEG-001"],
                "derived_from_ids": [],
                "rationale": None,
            },
        },
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Functional requirement text",
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


def test_valid_stage_execution_succeeds() -> None:
    candidate = make_valid_candidate_data()
    result = run_requirement_analysis_stage(candidate)

    assert result.status == StageStatus.SUCCESS
    assert result.committed_output is not None
    assert result.committed_output.summary.text == "A valid summary"
    assert result.error_code is None
    assert result.safe_message is None


def test_structural_failure_returns_failed_without_leaking_payload() -> None:
    unsafe_payload = "UNSAFE_PAYLOAD_VALUE_SECRET"
    candidate = make_valid_candidate_data()
    # Add an unknown extra top-level field to make it structurally invalid (extra="forbid")
    # while keeping the unsafe value inside the candidate passed to the runner.
    candidate["raw_secret_should_not_leak"] = unsafe_payload

    result = run_requirement_analysis_stage(candidate)

    assert result.status == StageStatus.FAILED
    assert result.committed_output is None
    assert result.error_code == "STRUCTURAL_VALIDATION_FAILED"
    assert result.safe_message == "RequirementAnalysis failed structural validation."

    # Verify the unsafe payload and the field key are not leaked in the serialized result
    serialized = result.model_dump_json()
    assert unsafe_payload not in serialized
    assert "raw_secret_should_not_leak" not in serialized



def test_semantic_failure_returns_failed_without_leaking_payload() -> None:
    candidate = make_valid_candidate_data()
    # Add a proposed AC with a bad reference (matrix prefix check failure)
    bad_ref = "RISK-001"
    candidate["acceptance_criteria"] = [
        {
            "id": "AC-001",
            "description": "Proposed AC description",
            "provenance": {
                "origin": "PROPOSED",
                "transformation": "NONE",
                "source_segment_ids": [],
                "derived_from_ids": [bad_ref],
                "rationale": "Proposed AC rationale",
            },
        }
    ]

    result = run_requirement_analysis_stage(candidate)

    assert result.status == StageStatus.FAILED
    assert result.committed_output is None
    assert result.error_code == "SEMANTIC_VALIDATION_FAILED"
    assert result.safe_message == "RequirementAnalysis failed semantic validation."

    # Verify the bad reference value is not leaked in the serialized result
    serialized = result.model_dump_json()
    assert bad_ref not in serialized


def test_semantic_failure_missing_ref_returns_failed_without_leaking_payload() -> None:
    candidate = make_valid_candidate_data()
    # Add a proposed AC with a valid prefix but missing reference ID (REQ-999)
    bad_ref = "REQ-999"
    candidate["acceptance_criteria"] = [
        {
            "id": "AC-001",
            "description": "Proposed AC description",
            "provenance": {
                "origin": "PROPOSED",
                "transformation": "NONE",
                "source_segment_ids": [],
                "derived_from_ids": [bad_ref],
                "rationale": "Proposed AC rationale",
            },
        }
    ]

    result = run_requirement_analysis_stage(candidate)

    assert result.status == StageStatus.FAILED
    assert result.committed_output is None
    assert result.error_code == "SEMANTIC_VALIDATION_FAILED"
    assert result.safe_message == "RequirementAnalysis failed semantic validation."

    # Verify the bad reference value is not leaked in the serialized result
    serialized = result.model_dump_json()
    assert bad_ref not in serialized


def test_stage_result_invariants() -> None:
    # 1. SUCCESS: committed_output required, error_code/safe_message must be None
    # SUCCESS without committed_output
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.SUCCESS,
            committed_output=None,
        )
    # SUCCESS with error_code
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.SUCCESS,
            committed_output=RequirementAnalysis.model_validate(
                make_valid_candidate_data()
            ),
            error_code="SOME_ERROR",
        )
    # SUCCESS with safe_message
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.SUCCESS,
            committed_output=RequirementAnalysis.model_validate(
                make_valid_candidate_data()
            ),
            safe_message="Some message",
        )

    # 2. FAILED: committed_output must be None, error_code and safe_message required
    # FAILED with committed_output
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.FAILED,
            committed_output=RequirementAnalysis.model_validate(
                make_valid_candidate_data()
            ),
            error_code="SOME_ERROR",
            safe_message="Some message",
        )
    # FAILED without error_code
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.FAILED,
            committed_output=None,
            safe_message="Some message",
        )
    # FAILED without safe_message
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.FAILED,
            committed_output=None,
            error_code="SOME_ERROR",
        )

    # 3. NOT_STARTED: committed_output, error_code, and safe_message must be None
    # NOT_STARTED with committed_output
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.NOT_STARTED,
            committed_output=RequirementAnalysis.model_validate(
                make_valid_candidate_data()
            ),
        )
    # NOT_STARTED with error_code
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.NOT_STARTED,
            error_code="SOME_ERROR",
        )
    # NOT_STARTED with safe_message
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.NOT_STARTED,
            safe_message="Some message",
        )

    # 4. SKIPPED: committed_output must be None (error_code/safe_message semantics deferred)
    # SKIPPED with committed_output
    with pytest.raises(ValidationError):
        StageResult[RequirementAnalysis](
            status=StageStatus.SKIPPED,
            committed_output=RequirementAnalysis.model_validate(
                make_valid_candidate_data()
            ),
        )
    # SKIPPED with error_code or safe_message is NOT rejected in Slice 4 (semantics deferred)
    skipped_ok = StageResult[RequirementAnalysis](
        status=StageStatus.SKIPPED,
        committed_output=None,
        error_code="DEFERRED",
        safe_message="Deferred",
    )
    assert skipped_ok.status == StageStatus.SKIPPED


def test_pipeline_import_isolation() -> None:
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
