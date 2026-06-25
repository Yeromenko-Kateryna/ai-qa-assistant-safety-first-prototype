import pytest
from app.domain_models import SanitizedInputEnvelope, SanitizedSegment, StageStatus
from app.requirement_agent_provider import (
    RequirementAgentProvider,
    AGENT_PROVIDER_FAILED,
    AGENT_PROVIDER_TIMEOUT,
    AGENT_PROVIDER_EMPTY_DRAFT,
    run_requirement_agent_with_provider,
)
import app.requirement_agent_prompt as requirement_agent_prompt
from app.gemini_requirement_agent_provider import GeminiRequirementAgentProvider

# Stub response matching SDK-free client contract
class StubResponse:
    def __init__(self, text=None, has_text=True):
        if has_text:
            self.text = text


# Stub client matching client.generate_content(model_name, prompt) -> object
class FakeInjectedGeminiClient:
    def __init__(self, response_obj=None, raises_exc=None):
        self.response_obj = response_obj
        self.raises_exc = raises_exc
        self.seen_model = None
        self.seen_prompt = None

    def generate_content(self, model_name: str, prompt: str) -> object:
        self.seen_model = model_name
        self.seen_prompt = prompt
        if self.raises_exc:
            raise self.raises_exc
        return self.response_obj


# Test-local adapter to keep Gemini provider boundary decoupled from Slice 16 fake runner
class PromptProviderAdapter(RequirementAgentProvider):
    def __init__(self, prompt_provider):
        self.prompt_provider = prompt_provider

    def generate_draft(self, sanitized_input: SanitizedInputEnvelope) -> str:
        prompt = requirement_agent_prompt.build_requirement_agent_prompt(sanitized_input)
        return self.prompt_provider.generate_draft_from_prompt(prompt)


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


# 1. Direct provider tests

def test_gemini_provider_direct_generate_success():
    response = StubResponse(text=MOCK_DRAFT_JSON)
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client, model_name="test-model")

    draft = provider.generate_draft_from_prompt("Test prompt")
    assert draft == MOCK_DRAFT_JSON
    assert fake_client.seen_model == "test-model"
    assert fake_client.seen_prompt == "Test prompt"


def test_gemini_provider_direct_empty_returns_empty_string():
    response = StubResponse(text="   ")
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)

    draft = provider.generate_draft_from_prompt("Test prompt")
    assert draft == ""


def test_gemini_provider_direct_none_returns_empty_string():
    response = StubResponse(text=None)
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)

    draft = provider.generate_draft_from_prompt("Test prompt")
    assert draft == ""


def test_gemini_provider_direct_non_string_raises_value_error():
    response = StubResponse(text=12345)
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)

    with pytest.raises(ValueError, match="Expected response 'text' to be string"):
        provider.generate_draft_from_prompt("Test prompt")


def test_gemini_provider_direct_missing_text_field_raises_value_error():
    response = StubResponse(has_text=False)
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)

    with pytest.raises(ValueError, match="missing the required 'text' attribute"):
        provider.generate_draft_from_prompt("Test prompt")


def test_gemini_provider_direct_response_none_raises_value_error():
    fake_client = FakeInjectedGeminiClient(response_obj=None)
    provider = GeminiRequirementAgentProvider(client=fake_client)

    with pytest.raises(ValueError, match="Response object is None"):
        provider.generate_draft_from_prompt("Test prompt")


def test_gemini_provider_direct_client_none_raises_value_error():
    provider = GeminiRequirementAgentProvider(client=None)

    with pytest.raises(ValueError, match="Injected Gemini client is missing"):
        provider.generate_draft_from_prompt("Test prompt")


# 2. Integration safe wrapping tests through PromptProviderAdapter

def test_gemini_provider_integration_empty_maps_to_empty_draft():
    response = StubResponse(text="")
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)
    adapter = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, adapter)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_EMPTY_DRAFT


def test_gemini_provider_integration_timeout_wrapped_safely():
    fake_client = FakeInjectedGeminiClient(raises_exc=TimeoutError("Request Timed Out"))
    provider = GeminiRequirementAgentProvider(client=fake_client)
    adapter = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, adapter)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_TIMEOUT

    # Assert raw exception text does not leak
    serialized = result.model_dump_json()
    assert "Request Timed Out" not in serialized
    assert "The system shall allow email login." not in serialized


def test_gemini_provider_integration_auth_failure_wrapped_safely():
    fake_client = FakeInjectedGeminiClient(raises_exc=RuntimeError("Billing not enabled / Invalid credentials"))
    provider = GeminiRequirementAgentProvider(client=fake_client)
    adapter = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, adapter)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED

    # Assert credentials exception message and segments do not leak
    serialized = result.model_dump_json()
    assert "Billing not enabled" not in serialized
    assert "Invalid credentials" not in serialized
    assert "The system shall allow email login." not in serialized


def test_gemini_provider_integration_non_string_wrapped_safely():
    response = StubResponse(text=123.45)
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)
    adapter = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, adapter)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED

    # Assert raw value does not leak
    serialized = result.model_dump_json()
    assert "123.45" not in serialized
    assert "The system shall allow email login." not in serialized


def test_gemini_provider_integration_missing_text_wrapped_safely():
    response = StubResponse(has_text=False)
    fake_client = FakeInjectedGeminiClient(response_obj=response)
    provider = GeminiRequirementAgentProvider(client=fake_client)
    adapter = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, adapter)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED

    # Assert error details do not leak
    serialized = result.model_dump_json()
    assert "missing the required 'text' attribute" not in serialized
    assert "The system shall allow email login." not in serialized


def test_gemini_provider_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
