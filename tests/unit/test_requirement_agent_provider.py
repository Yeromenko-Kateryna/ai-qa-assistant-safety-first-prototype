import json
from app.domain_models import StageStatus, SanitizedInputEnvelope, SanitizedSegment
from app.requirement_agent_provider import (
    RequirementAgentProvider,
    run_requirement_agent_with_provider,
    AGENT_PROVIDER_FAILED,
    AGENT_PROVIDER_TIMEOUT,
    AGENT_PROVIDER_EMPTY_DRAFT,
)
from app.requirement_agent_adapter import (
    AGENT_DRAFT_NOT_JSON,
    AGENT_DRAFT_UNSAFE_CONTENT,
)

# Helpers for testing (using valid current model fixtures)
MOCK_ENVELOPE = SanitizedInputEnvelope(
    segments=[
        SanitizedSegment(
            id="SEG-001",
            order=1,
            text="The system shall allow email login.",
            safety_flags=[],
            safety_event_ids=[],
        )
    ],
    safety_events=[],
)

VALID_DRAFT_JSON = json.dumps({
    "summary": {
        "text": "Valid requirements summary.",
        "provenance": {
            "origin": "EXTRACTED",
            "transformation": "SUMMARY",
            "source_segment_ids": ["SEG-001"],
            "derived_from_ids": [],
            "rationale": None
        }
    },
    "requirements": [
        {
            "id": "REQ-001",
            "description": "The system shall process email logins.",
            "category": "FUNCTIONAL",
            "provenance": {
                "origin": "EXTRACTED",
                "transformation": "VERBATIM",
                "source_segment_ids": ["SEG-001"],
                "derived_from_ids": [],
                "rationale": None
            }
        }
    ],
    "acceptance_criteria": [],
    "business_rules": [],
    "ambiguities": [],
    "missing_information": [],
    "assumptions": []
})


class FakeProvider(RequirementAgentProvider):
    """A fake provider that returns pre-configured draft output or raises exceptions."""

    def __init__(self, output: any = "", exception: Exception | None = None):
        self.output = output
        self.exception = exception
        self.seen_input = None

    def generate_draft(self, sanitized_input: SanitizedInputEnvelope) -> str:
        self.seen_input = sanitized_input
        if self.exception is not None:
            raise self.exception
        return self.output


def test_provider_success():
    provider = FakeProvider(output=VALID_DRAFT_JSON)
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.SUCCESS
    assert result.committed_output is not None
    assert result.committed_output.requirements[0].id == "REQ-001"
    assert result.error_code is None


def test_provider_receives_sanitized_envelope():
    provider = FakeProvider(output=VALID_DRAFT_JSON)
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.SUCCESS
    assert provider.seen_input is MOCK_ENVELOPE
    assert provider.seen_input.segments[0].text == "The system shall allow email login."
    assert not hasattr(provider.seen_input, "raw_text")


def test_provider_returns_markdown_fails():
    provider = FakeProvider(output="# Summary\n- Some bullet point")
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_NOT_JSON
    assert result.safe_message is not None


def test_provider_returns_malformed_json_fails():
    provider = FakeProvider(output='{"summary": {"text": "incomplete"')
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_NOT_JSON
    assert result.safe_message is not None


def test_provider_returns_unsafe_draft_fails():
    # Attempt secret assignment in the candidate output summary
    unsafe_dict = json.loads(VALID_DRAFT_JSON)
    unsafe_dict["summary"]["text"] = "Config setting: api_key='123456'"

    provider = FakeProvider(output=json.dumps(unsafe_dict))
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_UNSAFE_CONTENT
    assert result.committed_output is None
    assert result.safe_message is not None


def test_provider_timeout_exception():
    provider = FakeProvider(exception=TimeoutError("Request timed out after 30s"))
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_TIMEOUT
    assert result.committed_output is None
    # Verify raw message is not leaked
    assert "30s" not in result.model_dump_json()
    assert "Request timed out" not in result.model_dump_json()


def test_provider_generic_exception():
    provider = FakeProvider(exception=RuntimeError("Internal DB Connection crashed 192.168.1.1"))
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED
    assert result.committed_output is None
    # Verify raw database exception text or IPs do not leak
    serialized = result.model_dump_json()
    assert "Internal DB Connection" not in serialized
    assert "192.168.1.1" not in serialized
    # Verify sanitized segment text does not leak in provider-level failure
    assert "The system shall allow email login." not in serialized


def test_provider_empty_draft():
    for empty_val in ["", "   ", "\n\n"]:
        provider = FakeProvider(output=empty_val)
        result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

        assert result.status == StageStatus.FAILED
        assert result.error_code == AGENT_PROVIDER_EMPTY_DRAFT
        assert result.committed_output is None


def test_provider_non_string_draft_fails_safely():
    # Returns a dict instead of a string
    provider = FakeProvider(output={"draft": "some draft content value"})
    result = run_requirement_agent_with_provider(MOCK_ENVELOPE, provider)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED
    assert result.committed_output is None

    serialized = result.model_dump_json()
    # Serialization does not contain raw dictionary keys, values, or segment inputs
    assert "draft" not in serialized
    assert "some draft content value" not in serialized
    assert "The system shall allow email login." not in serialized


def test_provider_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
