import pytest
from app.domain_models import (
    SanitizedInputEnvelope,
    SanitizedSegment,
    StageStatus,
)
from app.requirement_agent_runner import (
    FakePromptAwareProvider,
    run_requirement_agent_pipeline_with_fake_provider,
)
from app.requirement_agent_adapter import (
    AGENT_DRAFT_NOT_JSON,
    AGENT_DRAFT_UNSAFE_CONTENT,
)
from app.requirement_agent_provider import (
    AGENT_PROVIDER_FAILED,
    AGENT_PROVIDER_TIMEOUT,
)
import app.requirement_agent_prompt as requirement_agent_prompt

# Setup valid mock draft JSON payload conforming to domain and validation contracts
MOCK_DRAFT_JSON = """{
  "summary": {
    "text": "User wants email authentication.",
    "provenance": {
      "origin": "EXTRACTED",
      "transformation": "SUMMARY",
      "source_segment_ids": ["SEG-001"],
      "derived_from_ids": [],
      "rationale": null
    }
  },
  "requirements": [
    {
      "id": "REQ-001",
      "description": "The system shall allow users to log in with an email.",
      "category": "FUNCTIONAL",
      "provenance": {
        "origin": "EXTRACTED",
        "transformation": "VERBATIM",
        "source_segment_ids": ["SEG-001"],
        "derived_from_ids": [],
        "rationale": null
      }
    }
  ],
  "acceptance_criteria": [],
  "business_rules": [],
  "ambiguities": [],
  "missing_information": [],
  "assumptions": []
}"""

TEST_ENVELOPE = SanitizedInputEnvelope(
    segments=[
        SanitizedSegment(
            id="SEG-001",
            order=1,
            text="The system shall allow email login.",
            safety_flags=[],
            safety_event_ids=[]
        )
    ],
    safety_events=[]
)


def test_runner_valid_draft_success():
    fake_provider = FakePromptAwareProvider(response_text=MOCK_DRAFT_JSON)
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.SUCCESS
    assert result.error_code is None
    assert result.committed_output is not None
    assert result.committed_output.summary.text == "User wants email authentication."


def test_runner_provider_receives_correct_prompt():
    fake_provider = FakePromptAwareProvider(response_text=MOCK_DRAFT_JSON)
    run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert fake_provider.seen_prompt is not None
    assert "The system shall allow email login." in fake_provider.seen_prompt
    assert "Output raw JSON only" in fake_provider.seen_prompt
    assert "### REQUIRED ENTITY FIELDS:" in fake_provider.seen_prompt


def test_runner_does_not_expose_prompt_in_result():
    fake_provider = FakePromptAwareProvider(response_text=MOCK_DRAFT_JSON)
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    serialized = result.model_dump_json()
    assert "Output raw JSON only" not in serialized
    assert "### REQUIRED ENTITY FIELDS:" not in serialized
    assert "seen_prompt" not in serialized
    assert "The system shall allow email login." not in serialized


def test_runner_markdown_draft_fails():
    fake_provider = FakePromptAwareProvider(response_text=f"```json\n{MOCK_DRAFT_JSON}\n```")
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_NOT_JSON


def test_runner_malformed_json_fails():
    fake_provider = FakePromptAwareProvider(response_text="invalid-json")
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_NOT_JSON


def test_runner_unsafe_draft_fails():
    # Setup config containing unsafe API key credentials to trigger safety validator
    unsafe_draft = MOCK_DRAFT_JSON.replace("User wants email authentication.", "Setup config with api_key='supersecretpassword'")
    fake_provider = FakePromptAwareProvider(response_text=unsafe_draft)
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_UNSAFE_CONTENT


def test_runner_prompt_builder_value_error_fails_safely(monkeypatch):
    def failing_prompt_builder(_sanitized_input):
        raise ValueError("prompt contains sensitive internal detail")

    monkeypatch.setattr(
        requirement_agent_prompt,
        "build_requirement_agent_prompt",
        failing_prompt_builder,
    )

    fake_provider = FakePromptAwareProvider(response_text=MOCK_DRAFT_JSON)
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED
    assert result.committed_output is None

    # Verify no details/prompt contents leak in serialized state
    serialized = result.model_dump_json()
    assert "prompt contains sensitive internal detail" not in serialized
    assert "The system shall allow email login." not in serialized
    assert "Output raw JSON only" not in serialized


def test_runner_provider_timeout_fails_safely():
    fake_provider = FakePromptAwareProvider(raises_exc=TimeoutError("API timed out"))
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_TIMEOUT

    # Ensure raw exception message and segments do not leak
    serialized = result.model_dump_json()
    assert "API timed out" not in serialized
    assert "The system shall allow email login." not in serialized


def test_runner_provider_generic_exception_fails_safely():
    fake_provider = FakePromptAwareProvider(raises_exc=RuntimeError("Generic model failure"))
    result = run_requirement_agent_pipeline_with_fake_provider(TEST_ENVELOPE, fake_provider)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED

    # Ensure raw exception message and segments do not leak
    serialized = result.model_dump_json()
    assert "Generic model failure" not in serialized
    assert "The system shall allow email login." not in serialized


def test_runner_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
