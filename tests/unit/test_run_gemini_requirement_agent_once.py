import sys
from app.domain_models import StageStatus
import scripts.run_gemini_requirement_agent_once as runner

def test_runner_import_isolation():
    # Verify that importing the script does not load genai or check keys
    assert "google.genai" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "app.agent" not in sys.modules


def test_is_git_status_clean():
    # 1. Clean output: only branch indicator
    assert runner.is_git_status_clean("## main")
    assert runner.is_git_status_clean("## main\n")
    assert runner.is_git_status_clean("  \n## main\n  ")
    assert runner.is_git_status_clean("")

    # 2. Dirty output: branch plus untracked or modified files
    assert not runner.is_git_status_clean("## main\n M app/agent.py")
    assert not runner.is_git_status_clean("## main\n?? scripts/new_script.py")
    assert not runner.is_git_status_clean(" M app/agent.py")
    assert not runner.is_git_status_clean("?? scripts/new_script.py")


def test_missing_api_key_blocks_before_request():
    fake_environ = {"GEMINI_MODEL_NAME": "test-model"}
    def fake_import():
        raise AssertionError("import_genai should not be called if environment is incomplete")

    summary = runner.execute_request(fake_environ, fake_import)
    assert not summary["api_key_present"]
    assert summary["model_name_present"]
    assert not summary["request_attempted"]
    assert summary["request_count"] == 0
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_PROVIDER_FAILED"


def test_missing_model_name_blocks_before_request():
    fake_environ = {"GEMINI_API_KEY": "test-key"}
    def fake_import():
        raise AssertionError("import_genai should not be called if environment is incomplete")

    summary = runner.execute_request(fake_environ, fake_import)
    assert summary["api_key_present"]
    assert not summary["model_name_present"]
    assert not summary["request_attempted"]
    assert summary["request_count"] == 0
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_PROVIDER_FAILED"


class StubResponse:
    def __init__(self, text):
        self.text = text


def test_successful_request_attempts_exactly_one_request():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    # Valid requirements JSON structure
    mock_success_json = """{
      "summary": {
        "text": "Status indicator system.",
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
          "description": "The system shall display a system status indicator.",
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

    response = StubResponse(text=mock_success_json)

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key

        request_count = 0

        def generate_content(self, model_name, prompt):
            FakeClient.request_count += 1
            return response

    FakeClient.request_count = 0

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["api_key_present"]
    assert summary["model_name_present"]
    assert summary["sdk_readiness"]
    assert summary["model_configured"]
    assert summary["request_attempted"]
    assert summary["request_count"] == 1
    assert FakeClient.request_count == 1
    assert summary["stage_status"] == "SUCCESS"
    assert summary["error_code"] is None
    assert summary["committed_output_exists"]
    assert summary["requirement_count"] == 1


def test_provider_timeout_mapping():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            raise TimeoutError("Timeout occurred")

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["request_attempted"]
    assert summary["request_count"] == 1
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_PROVIDER_TIMEOUT"


def test_provider_empty_response_mapping():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    response = StubResponse(text="")

    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["request_attempted"]
    assert summary["request_count"] == 1
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_PROVIDER_EMPTY_DRAFT"


def test_provider_malformed_json_response_mapping():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    response = StubResponse(text="not a json string")

    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["request_attempted"]
    assert summary["request_count"] == 1
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_DRAFT_NOT_JSON"


def test_provider_validation_failure_mapping():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    # Missing required 'summary' and 'requirements' keys
    response = StubResponse(text="{}")

    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["request_attempted"]
    assert summary["request_count"] == 1
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_DRAFT_VALIDATION_FAILED"


def test_safe_summary_does_not_leak_secrets_or_payloads():
    fake_environ = {
        "GEMINI_API_KEY": "super_secret_key_12345",
        "GEMINI_MODEL_NAME": "extremely_secret_model_name"
    }

    response = StubResponse(text="{}")

    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)

    # Format the summary elements as a string representation
    serialized_summary = str(summary)

    assert "super_secret_key_12345" not in serialized_summary
    assert "extremely_secret_model_name" not in serialized_summary
    assert "The system shall display a system status indicator." not in serialized_summary


def test_pre_request_prompt_failure_does_not_attempt_request(monkeypatch):
    fake_environ = {
        "GEMINI_API_KEY": "secret-api-key-value",
        "GEMINI_MODEL_NAME": "secret-model-name-value"
    }

    import app.requirement_agent_prompt as prompt_module
    def fake_build_prompt(sanitized_input_env):
        raise ValueError("Simulated prompt building failure")

    monkeypatch.setattr(prompt_module, "build_requirement_agent_prompt", fake_build_prompt)

    class FakeClient:
        def __init__(self, api_key):
            pass

        request_count = 0
        def generate_content(self, model_name, prompt):
            FakeClient.request_count += 1
            return StubResponse("{}")

    FakeClient.request_count = 0

    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert not summary["request_attempted"]
    assert summary["request_count"] == 0
    assert FakeClient.request_count == 0
    assert summary["stage_status"] == "FAILED"
    assert summary["error_code"] == "AGENT_PROVIDER_FAILED"

    # Ensure no secrets or details are leaked in the summary
    serialized_summary = str(summary)
    assert "secret-api-key-value" not in serialized_summary
    assert "secret-model-name-value" not in serialized_summary
    assert "Simulated prompt building failure" not in serialized_summary
