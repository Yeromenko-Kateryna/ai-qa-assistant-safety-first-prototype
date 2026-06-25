from app.domain_models import SanitizedInputEnvelope, SanitizedSegment, StageStatus
from app.requirement_agent_provider import (
    RequirementAgentProvider,
    AGENT_PROVIDER_FAILED,
    AGENT_PROVIDER_TIMEOUT,
    run_requirement_agent_with_provider,
)
import app.requirement_agent_prompt as requirement_agent_prompt
from app.gemini_requirement_agent_provider import GeminiRequirementAgentProvider
from app.gemini_sdk_client_adapter import GeminiSdkClientAdapter

# Stub mock SDK client
class MockSdkModels:
    def __init__(self, response_text=None, raises_exc=None, has_text=True):
        self.response_text = response_text
        self.raises_exc = raises_exc
        self.has_text = has_text
        self.seen_model = None
        self.seen_prompt = None
        self.seen_config = None

    def generate_content(self, model, contents, config=None):
        self.seen_model = model
        self.seen_prompt = contents
        self.seen_config = config
        if self.raises_exc:
            raise self.raises_exc

        class MockResponse:
            if self.has_text:
                text = self.response_text
        return MockResponse()


class MockSdkClient:
    def __init__(self, models):
        self.models = models


class StubResponse:
    def __init__(self, text):
        self.text = text


# Test-local adapter to keep SDK client tests decoupled from Slice 16 runner
class PromptProviderAdapter(RequirementAgentProvider):
    def __init__(self, prompt_provider):
        self.prompt_provider = prompt_provider

    def generate_draft(self, sanitized_input: SanitizedInputEnvelope) -> str:
        prompt = requirement_agent_prompt.build_requirement_agent_prompt(sanitized_input)
        return self.prompt_provider.generate_draft_from_prompt(prompt)


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


def test_sdk_adapter_calls_client_with_correct_parameters():
    mock_models = MockSdkModels(response_text="mock draft output")
    mock_client = MockSdkClient(models=mock_models)

    # Inject mock client directly into adapter
    adapter = GeminiSdkClientAdapter(client=mock_client)
    response = adapter.generate_content("test-model-1.5", "test-prompt")

    assert response.text == "mock draft output"
    assert mock_models.seen_model == "test-model-1.5"
    assert mock_models.seen_prompt == "test-prompt"


def test_sdk_adapter_integration_timeout_wrapped_safely():
    mock_models = MockSdkModels(raises_exc=TimeoutError("Request Timed Out"))
    mock_client = MockSdkClient(models=mock_models)

    adapter = GeminiSdkClientAdapter(client=mock_client)
    provider = GeminiRequirementAgentProvider(client=adapter)
    wrapper = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, wrapper)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_TIMEOUT

    # Ensure no exceptions or prompts leak
    serialized = result.model_dump_json()
    assert "Request Timed Out" not in serialized
    assert "The system shall allow email login." not in serialized


def test_sdk_adapter_integration_auth_error_wrapped_safely():
    mock_models = MockSdkModels(raises_exc=RuntimeError("Billing not enabled"))
    mock_client = MockSdkClient(models=mock_models)

    adapter = GeminiSdkClientAdapter(client=mock_client)
    provider = GeminiRequirementAgentProvider(client=adapter)
    wrapper = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, wrapper)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED

    # Ensure no credentials/exception details leak
    serialized = result.model_dump_json()
    assert "Billing not enabled" not in serialized
    assert "The system shall allow email login." not in serialized


def test_sdk_adapter_integration_missing_text_wrapped_safely():
    mock_models = MockSdkModels(has_text=False)
    mock_client = MockSdkClient(models=mock_models)

    adapter = GeminiSdkClientAdapter(client=mock_client)
    provider = GeminiRequirementAgentProvider(client=adapter)
    wrapper = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, wrapper)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED

    # Ensure no exception details or segment text leaks
    serialized = result.model_dump_json()
    assert "missing the required 'text' attribute" not in serialized
    assert "The system shall allow email login." not in serialized


def test_sdk_adapter_integration_non_string_wrapped_safely():
    mock_models = MockSdkModels(response_text={"not": "a string"})
    mock_client = MockSdkClient(models=mock_models)

    adapter = GeminiSdkClientAdapter(client=mock_client)
    provider = GeminiRequirementAgentProvider(client=adapter)
    wrapper = PromptProviderAdapter(provider)

    result = run_requirement_agent_with_provider(TEST_ENVELOPE, wrapper)
    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_PROVIDER_FAILED
    assert result.committed_output is None

    # Ensure no raw non-string value, segment text, or traceback leaks
    serialized = result.model_dump_json()
    assert "not" not in serialized
    assert "a string" not in serialized
    assert "The system shall allow email login." not in serialized
    assert "Traceback" not in serialized


def test_sdk_client_adapter_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
