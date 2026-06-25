import pytest
from app.domain_models import StageStatus
from app.pipeline import run_requirement_analysis_pipeline_from_text


def test_pipeline_integration_success():
    raw_text = "The authentication page shall process email login requests."
    expected_sanitized_text = raw_text

    result = run_requirement_analysis_pipeline_from_text(raw_text)

    # Invariants verification
    assert result.status == StageStatus.SUCCESS
    assert result.committed_output is not None
    assert result.error_code is None
    assert result.safe_message is None

    # Validated stub candidate details
    committed = result.committed_output
    assert committed.summary.text == expected_sanitized_text
    assert len(committed.requirements) == 1
    assert committed.requirements[0].id == "REQ-001"
    assert committed.requirements[0].description == expected_sanitized_text
    assert committed.requirements[0].category.value == "FUNCTIONAL"

    # Rest of the lists are empty by design
    assert committed.acceptance_criteria == []
    assert committed.business_rules == []
    assert committed.ambiguities == []
    assert committed.missing_information == []
    assert committed.assumptions == []


def test_pipeline_integration_redacted_secrets():
    raw_secret_value = "supersecretpass123"
    raw_secret_expr = f"password='{raw_secret_value}'"
    raw_input = f"Configure database connection: {raw_secret_expr} in properties."

    result = run_requirement_analysis_pipeline_from_text(raw_input)
    assert result.status == StageStatus.SUCCESS

    committed = result.committed_output
    assert committed is not None
    assert committed.summary.text == committed.requirements[0].description

    # Assert secret and secret expression are redacted from output texts
    assert raw_secret_value not in committed.summary.text
    assert raw_secret_expr not in committed.summary.text
    assert "[REDACTED_SECRET_" in committed.summary.text

    assert raw_secret_value not in committed.requirements[0].description
    assert raw_secret_expr not in committed.requirements[0].description
    assert "[REDACTED_SECRET_" in committed.requirements[0].description

    # Ensure no secrets leak in serialized StageResult representation
    serialized = result.model_dump_json()
    assert raw_secret_value not in serialized
    assert raw_secret_expr not in serialized

    # Strengthen secret leakage checks: Assert full expression labels are also absent
    assert "password" not in committed.summary.text.lower()
    assert "password" not in committed.requirements[0].description.lower()
    assert "password" not in serialized.lower()


def test_pipeline_integration_empty_input_raises_value_error():
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        run_requirement_analysis_pipeline_from_text("")
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        run_requirement_analysis_pipeline_from_text("   \n   ")


def test_pipeline_integration_long_input_raises_value_error():
    long_text = "A" * 2001
    with pytest.raises(
        ValueError, match="exceeds single segment limit of 2,000 characters"
    ):
        run_requirement_analysis_pipeline_from_text(long_text)


def test_pipeline_integration_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
