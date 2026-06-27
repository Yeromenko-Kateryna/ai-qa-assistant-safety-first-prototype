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
    assert summary["acceptance_criteria_count"] == 0
    assert summary["business_rules_count"] == 0
    assert summary["ambiguities_count"] == 0
    assert summary["missing_information_count"] == 0
    assert summary["assumptions_count"] == 0


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


def test_diag_excluded_empty_provider_response():
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
    assert summary["error_code"] == "AGENT_PROVIDER_EMPTY_DRAFT"
    assert not summary.get("diagnostics_included", False)
    # Ensure no other draft diagnostic fields are present
    for key in [
        "diagnostic_status", "failure_phase", "safe_error_code", "root_type",
        "missing_top_level_keys", "invalid_field_paths", "safe_expected_type_names",
        "provenance_rule_failed", "semantic_rule_failed", "payload_values_printed"
    ]:
        assert key not in summary


def test_diag_excluded_timeout_provider_exception():
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
    assert summary["error_code"] == "AGENT_PROVIDER_TIMEOUT"
    assert not summary.get("diagnostics_included", False)
    for key in [
        "diagnostic_status", "failure_phase", "safe_error_code", "root_type",
        "missing_top_level_keys", "invalid_field_paths", "safe_expected_type_names",
        "provenance_rule_failed", "semantic_rule_failed", "payload_values_printed"
    ]:
        assert key not in summary


def test_diag_excluded_missing_model_key_preflight():
    fake_environ = {"GEMINI_API_KEY": "test-key"}
    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import)
    assert summary["error_code"] == "AGENT_PROVIDER_FAILED"
    assert not summary.get("diagnostics_included", False)
    for key in [
        "diagnostic_status", "failure_phase", "safe_error_code", "root_type",
        "missing_top_level_keys", "invalid_field_paths", "safe_expected_type_names",
        "provenance_rule_failed", "semantic_rule_failed", "payload_values_printed"
    ]:
        assert key not in summary


def test_diag_included_malformed_json():
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
    assert summary["error_code"] == "AGENT_DRAFT_NOT_JSON"
    assert summary.get("diagnostics_included") is True
    assert summary.get("failure_phase") == "PARSE"
    assert summary.get("safe_error_code") == "AGENT_DRAFT_NOT_JSON"
    assert summary.get("diagnostic_status") == "FAILED"


def test_diag_included_root_not_object():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }
    response = StubResponse(text="[1, 2, 3]")
    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response
    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["error_code"] == "AGENT_DRAFT_ROOT_NOT_OBJECT"
    assert summary.get("diagnostics_included") is True
    assert summary.get("failure_phase") == "ROOT_TYPE"
    assert summary.get("root_type") == "array"
    assert summary.get("safe_error_code") == "AGENT_DRAFT_ROOT_NOT_OBJECT"


def test_diag_included_missing_top_level_keys():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
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
    assert summary["error_code"] == "AGENT_DRAFT_VALIDATION_FAILED"
    assert summary.get("diagnostics_included") is True
    assert summary.get("failure_phase") == "SCHEMA"
    assert "summary" in summary.get("missing_top_level_keys", [])
    assert "requirements" in summary.get("missing_top_level_keys", [])
    assert summary.get("safe_error_code") == "AGENT_DRAFT_VALIDATION_FAILED"


def test_diag_included_pydantic_schema_failure():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }
    response = StubResponse(text='{"summary": "not an object", "requirements": []}')
    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response
    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["error_code"] == "AGENT_DRAFT_VALIDATION_FAILED"
    assert summary.get("diagnostics_included") is True
    assert summary.get("failure_phase") == "SCHEMA"
    assert "summary" in summary.get("invalid_field_paths", [])
    assert summary.get("safe_error_code") == "AGENT_DRAFT_VALIDATION_FAILED"

    # Ensure Pydantic's raw details do not leak in summary
    serialized = str(summary)
    assert "Input should be" not in serialized
    assert "valid dictionary" not in serialized
    assert "ctx" not in serialized
    assert "url" not in serialized


def test_diag_included_semantic_dependency_failure():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }
    fake_semantic_fail = """{
      "summary": {
        "text": "Indicator system.",
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
      "acceptance_criteria": [
        {
          "id": "AC-001",
          "description": "Validation check criterion.",
          "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-999"],
            "rationale": "Valid proposed rationale"
          }
        }
      ],
      "business_rules": [],
      "ambiguities": [],
      "missing_information": [],
      "assumptions": []
    }"""
    response = StubResponse(text=fake_semantic_fail)
    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response
    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["error_code"] == "AGENT_DRAFT_VALIDATION_FAILED"
    assert summary.get("diagnostics_included") is True
    assert summary.get("failure_phase") == "SEMANTIC"
    assert summary.get("semantic_rule_failed") == "MISSING_DEPENDENCY_REFERENCE"

    # Ensure no payload leaks (e.g. REQ-999 or description text)
    serialized = str(summary)
    assert "REQ-999" not in serialized
    assert "Validation check criterion" not in serialized


def test_diag_included_unsafe_key_precedence():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }
    response = StubResponse(text='{"api_key": "SyntheticSecretValue123456"}')
    class FakeClient:
        def __init__(self, api_key):
            pass
        def generate_content(self, model_name, prompt):
            return response
    def fake_import():
        return object()

    summary = runner.execute_request(fake_environ, fake_import, FakeClient)
    assert summary["error_code"] == "AGENT_DRAFT_VALIDATION_FAILED"
    assert summary.get("diagnostics_included") is True
    assert summary.get("failure_phase") == "UNSAFE"
    assert summary.get("safe_error_code") == "AGENT_DRAFT_UNSAFE_CONTENT"
    assert summary.get("payload_values_printed") is False

    # Ensure other diagnostic metadata are omitted
    for key in [
        "diagnostic_status", "root_type", "missing_top_level_keys",
        "invalid_field_paths", "safe_expected_type_names",
        "provenance_rule_failed", "semantic_rule_failed"
    ]:
        assert key not in summary

    # Ensure the secret values are not leaked
    serialized = str(summary)
    assert "SyntheticSecretValue123456" not in serialized
    assert "api_key_present" in serialized  # Whitelisted key
    assert "api_key" not in serialized.replace("api_key_present", "")


def test_diag_safe_summary_formatting():
    summary = {
        "api_key_present": True,
        "model_name_present": True,
        "model_configured": True,
        "sdk_readiness": True,
        "request_attempted": True,
        "request_count": 1,
        "stage_status": "FAILED",
        "error_code": "AGENT_DRAFT_VALIDATION_FAILED",
        "committed_output_exists": False,
        "requirement_count": 0,
        "acceptance_criteria_count": 0,
        "business_rules_count": 0,
        "ambiguities_count": 0,
        "missing_information_count": 0,
        "assumptions_count": 0,
        "diagnostics_included": True,
        "diagnostic_status": "FAILED",
        "failure_phase": "SCHEMA",
        "safe_error_code": "AGENT_DRAFT_VALIDATION_FAILED",
        "root_type": "object",
        "missing_top_level_keys": ["summary"],
        "invalid_field_paths": ["requirements[0].id"],
        "safe_expected_type_names": ["string"],
        "schema_error_types": ["missing", "extra_forbidden"],
        "schema_error_type_counts": {"missing": 1, "extra_forbidden": 2},
        "provenance_rule_failed": None,
        "semantic_rule_failed": None,
        "payload_values_printed": False,
        "leaked_key": "some_leak_value",  # Not in whitelist
        "draft_text": "leak_draft_value",  # Prohibited key
        "raw_response": "leak_raw_response_value",  # Prohibited key
        "prompt": "leak_prompt_value",  # Prohibited key
        "msg": "leak_pydantic_msg",  # Prohibited key
        "input": "leak_pydantic_input",  # Prohibited key
        "ctx": {"leak": "pydantic_ctx"},  # Prohibited key
        "url": "leak_pydantic_url",  # Prohibited key
    }

    # Call production helper
    lines = runner.format_safe_diagnostic_lines(summary)
    output = "\n".join(lines)

    # Allowed diagnostic fields must appear
    assert "Diagnostic status: FAILED" in output
    assert "Failure phase: SCHEMA" in output
    assert "Safe error code: AGENT_DRAFT_VALIDATION_FAILED" in output
    assert "Root type: object" in output
    assert "Missing top level keys: ['summary']" in output
    assert "Invalid field paths: ['requirements[0].id']" in output
    assert "Safe expected type names: ['string']" in output
    assert "Schema error types: ['missing', 'extra_forbidden']" in output
    assert "Schema error type counts: {'missing': 1, 'extra_forbidden': 2}" in output
    assert "Payload values printed: False" in output

    # Unknown/prohibited fields must not appear
    assert "leaked_key" not in output
    assert "some_leak_value" not in output
    assert "draft_text" not in output
    assert "leak_draft_value" not in output
    assert "raw_response" not in output
    assert "leak_raw_response_value" not in output
    assert "prompt" not in output
    assert "leak_prompt_value" not in output
    assert "msg" not in output
    assert "leak_pydantic_msg" not in output
    assert "input" not in output
    assert "leak_pydantic_input" not in output
    assert "ctx" not in output
    assert "pydantic_ctx" not in output
    assert "url" not in output
    assert "leak_pydantic_url" not in output


def test_runner_second_synthetic_fixture():
    # Verify that runner uses the second built-in synthetic fixture by default
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    captured_prompts = []

    class MockAdapter:
        def __init__(self, api_key):
            self.api_key = api_key

        def generate_content(self, model_name, prompt):
            captured_prompts.append(prompt)
            dummy_json = (
                '{"summary": {"text": "dummy summary", "provenance": {"origin": "EXTRACTED", '
                '"transformation": "SUMMARY", "source_segment_ids": ["SEG-001"], "derived_from_ids": [], '
                '"rationale": null}}, "requirements": [{"id": "REQ-001", "description": "dummy req", '
                '"category": "FUNCTIONAL", "provenance": {"origin": "EXTRACTED", "transformation": "VERBATIM", '
                '"source_segment_ids": ["SEG-001"], "derived_from_ids": [], "rationale": null}}], '
                '"acceptance_criteria": [], "business_rules": [], "ambiguities": [], "missing_information": [], '
                '"assumptions": []}'
            )
            return StubResponse(text=dummy_json)

    def fake_import():
        pass

    summary = runner.execute_request(fake_environ, fake_import, client_adapter_class=MockAdapter)

    # 1. Verify runner execution succeeded with dummy response
    assert summary["stage_status"] == "SUCCESS"
    assert summary["committed_output_exists"] is True
    assert summary["requirement_count"] == 1
    assert summary["acceptance_criteria_count"] == 0
    assert summary["business_rules_count"] == 0
    assert summary["ambiguities_count"] == 0
    assert summary["missing_information_count"] == 0
    assert summary["assumptions_count"] == 0

    # 2. Verify prompt was captured exactly once
    assert len(captured_prompts) == 1
    prompt_text = captured_prompts[0]

    # 3. Verify the runner uses the second built-in synthetic fixture by default
    expected_fixture = (
        "The system shall store transaction records in a secure database. "
        "The system must allow authorized users to retrieve stored transaction records."
    )
    assert expected_fixture in prompt_text

    # 4. Verify the old first fixture is not the active default for the next gate
    old_fixture = "The system shall display a system status indicator."
    assert old_fixture not in prompt_text

    # 5. Verify no production/customer/confidential text appears
    assert "confidential" not in prompt_text.lower()
    assert "private" not in prompt_text.lower()

    # 6. Verify output expectations for Gate J/K in prompt
    assert '"acceptance_criteria": [' in prompt_text
    assert '"id": "AC-001"' in prompt_text
    assert '"business_rules": []' in prompt_text
    assert '"ambiguities": []' in prompt_text
    assert '"missing_information": []' in prompt_text
    assert '"assumptions": []' in prompt_text

    # 7. Verify no fixture/domain-specific phrases appear in prompt
    assert "transaction storage" not in prompt_text.lower()
    assert "database safety criteria" not in prompt_text.lower()
    assert "database compliance" not in prompt_text.lower()


def test_runner_safe_aggregate_counts_populated():
    fake_environ = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL_NAME": "test-model"
    }

    class MockAdapter:
        def __init__(self, api_key):
            self.api_key = api_key

        def generate_content(self, model_name, prompt):
            dummy_json = (
                '{"summary": {"text": "dummy summary", "provenance": {"origin": "EXTRACTED", '
                '"transformation": "SUMMARY", "source_segment_ids": ["SEG-001"], "derived_from_ids": [], '
                '"rationale": null}}, '
                '"requirements": ['
                '  {"id": "REQ-001", "description": "req 1", "category": "FUNCTIONAL", "provenance": {"origin": "EXTRACTED", "transformation": "VERBATIM", "source_segment_ids": ["SEG-001"], "derived_from_ids": [], "rationale": null}},'
                '  {"id": "REQ-002", "description": "req 2", "category": "FUNCTIONAL", "provenance": {"origin": "EXTRACTED", "transformation": "VERBATIM", "source_segment_ids": ["SEG-001"], "derived_from_ids": [], "rationale": null}}'
                '], '
                '"acceptance_criteria": ['
                '  {"id": "AC-001", "description": "ac 1", "provenance": {"origin": "PROPOSED", "transformation": "NONE", "source_segment_ids": [], "derived_from_ids": ["REQ-001"], "rationale": "reason"}}'
                '], '
                '"business_rules": ['
                '  {"id": "BR-001", "description": "br 1", "provenance": {"origin": "EXTRACTED", "transformation": "VERBATIM", "source_segment_ids": ["SEG-001"], "derived_from_ids": [], "rationale": null}},'
                '  {"id": "BR-002", "description": "br 2", "provenance": {"origin": "EXTRACTED", "transformation": "VERBATIM", "source_segment_ids": ["SEG-001"], "derived_from_ids": [], "rationale": null}}'
                '], '
                '"ambiguities": ['
                '  {"id": "AMB-001", "description": "amb 1", "provenance": {"origin": "INFERRED", "transformation": "NONE", "source_segment_ids": [], "derived_from_ids": ["REQ-001"], "rationale": "reason"}}'
                '], '
                '"missing_information": ['
                '  {"id": "MISS-001", "description": "miss 1", "provenance": {"origin": "MISSING_INFORMATION", "transformation": "NONE", "source_segment_ids": [], "derived_from_ids": ["REQ-001"], "rationale": "reason"}},'
                '  {"id": "MISS-002", "description": "miss 2", "provenance": {"origin": "MISSING_INFORMATION", "transformation": "NONE", "source_segment_ids": [], "derived_from_ids": ["REQ-001"], "rationale": "reason"}}'
                '], '
                '"assumptions": ['
                '  {"id": "ASM-001", "description": "asm 1", "provenance": {"origin": "ASSUMPTION", "transformation": "NONE", "source_segment_ids": [], "derived_from_ids": ["REQ-001"], "rationale": "reason"}}'
                ']}'
            )
            return StubResponse(text=dummy_json)

    def fake_import():
        pass

    summary = runner.execute_request(fake_environ, fake_import, client_adapter_class=MockAdapter)

    assert summary["stage_status"] == "SUCCESS"
    assert summary["committed_output_exists"] is True
    assert summary["requirement_count"] == 2
    assert summary["acceptance_criteria_count"] == 1
    assert summary["business_rules_count"] == 2
    assert summary["ambiguities_count"] == 1
    assert summary["missing_information_count"] == 2
    assert summary["assumptions_count"] == 1

    import json
    summary_serialized = json.dumps(summary, sort_keys=True)
    forbidden_payload_values = [
        "REQ-001",
        "REQ-002",
        "AC-001",
        "BR-001",
        "AMB-001",
        "MISS-001",
        "ASM-001",
        "req 1",
        "req 2",
        "ac 1",
        "br 1",
        "amb 1",
        "miss 1",
        "asm 1",
        "SEG-001",
        "reason",
        "source_segment_ids",
        "derived_from_ids",
        "provenance"
    ]
    for val in forbidden_payload_values:
        assert val not in summary_serialized
