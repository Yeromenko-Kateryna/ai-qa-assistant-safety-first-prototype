import pytest
import json
from app.domain_models import StageStatus
from app.requirement_agent_adapter import (
    parse_requirement_agent_draft,
    AGENT_DRAFT_EMPTY,
    AGENT_DRAFT_NOT_JSON,
    AGENT_DRAFT_ROOT_NOT_OBJECT,
    AGENT_DRAFT_UNSAFE_CONTENT,
    AGENT_DRAFT_VALIDATION_FAILED,
)

# Helpers for testing (using required schema & EXTRACTED provenance rules)
VALID_ANALYSIS_DICT = {
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
}


def test_valid_draft_json_success():
    valid_json = json.dumps(VALID_ANALYSIS_DICT)
    result = parse_requirement_agent_draft(valid_json)

    assert result.status == StageStatus.SUCCESS
    assert result.committed_output is not None
    assert result.committed_output.requirements[0].id == "REQ-001"
    assert result.error_code is None
    assert result.safe_message is None


def test_empty_or_whitespace_draft():
    for empty_input in ["", "    ", "\n   \n"]:
        result = parse_requirement_agent_draft(empty_input)
        assert result.status == StageStatus.FAILED
        assert result.error_code == AGENT_DRAFT_EMPTY
        assert result.safe_message is not None


def test_markdown_draft_fails():
    markdown_draft = "# Summary\n- Bullet points"
    result = parse_requirement_agent_draft(markdown_draft)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_NOT_JSON
    assert result.safe_message is not None


def test_malformed_json_fails():
    malformed_json = '{"summary": {"text": "incomplete"'
    result = parse_requirement_agent_draft(malformed_json)

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_NOT_JSON
    assert result.safe_message is not None


def test_json_non_object_roots_fail():
    # List root
    result_list = parse_requirement_agent_draft(json.dumps([VALID_ANALYSIS_DICT]))
    assert result_list.status == StageStatus.FAILED
    assert result_list.error_code == AGENT_DRAFT_ROOT_NOT_OBJECT
    assert result_list.safe_message is not None

    # String root
    result_str = parse_requirement_agent_draft(json.dumps("plain string"))
    assert result_str.status == StageStatus.FAILED
    assert result_str.error_code == AGENT_DRAFT_ROOT_NOT_OBJECT
    assert result_str.safe_message is not None

    # Number root (negative number -1 should be successfully parsed but fail root check)
    result_num = parse_requirement_agent_draft(json.dumps(-1))
    assert result_num.status == StageStatus.FAILED
    assert result_num.error_code == AGENT_DRAFT_ROOT_NOT_OBJECT
    assert result_num.safe_message is not None

    # Null root
    result_null = parse_requirement_agent_draft(json.dumps(None))
    assert result_null.status == StageStatus.FAILED
    assert result_null.error_code == AGENT_DRAFT_ROOT_NOT_OBJECT
    assert result_null.safe_message is not None


def test_schema_invalid_json_fails():
    # Missing 'summary' key (causes structural failure)
    invalid_dict = VALID_ANALYSIS_DICT.copy()
    invalid_dict.pop("summary")

    result = parse_requirement_agent_draft(json.dumps(invalid_dict))

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_VALIDATION_FAILED
    assert result.safe_message is not None


def test_semantic_invalid_json_fails():
    # Adding a PROPOSED AC depending on non-existent REQ-999 to cause semantic failure
    invalid_dict = json.loads(json.dumps(VALID_ANALYSIS_DICT))
    invalid_dict["acceptance_criteria"] = [
        {
            "id": "AC-001",
            "description": "User can log in.",
            "provenance": {
                "origin": "PROPOSED",
                "transformation": "NONE",
                "source_segment_ids": [],
                "derived_from_ids": ["REQ-999"],
                "rationale": "Proposed from requirement."
            }
        }
    ]

    result = parse_requirement_agent_draft(json.dumps(invalid_dict))

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_VALIDATION_FAILED
    assert result.safe_message is not None


def test_secret_like_draft_fails():
    # Contains api_key assignment
    unsafe_dict = json.loads(json.dumps(VALID_ANALYSIS_DICT))
    unsafe_dict["summary"]["text"] = "Setup config with api_key='supersecretpassword'"

    result = parse_requirement_agent_draft(json.dumps(unsafe_dict))

    assert result.status == StageStatus.FAILED
    assert result.error_code == AGENT_DRAFT_UNSAFE_CONTENT
    assert result.committed_output is None
    assert result.safe_message is not None


def test_failed_results_do_not_leak_details_in_serialization():
    unsafe_dict = json.loads(json.dumps(VALID_ANALYSIS_DICT))
    unsafe_text = "Setup config with api_key='supersecretpassword'"
    unsafe_dict["summary"]["text"] = unsafe_text

    result = parse_requirement_agent_draft(json.dumps(unsafe_dict))

    serialized = result.model_dump_json()
    assert unsafe_text not in serialized
    assert "supersecretpassword" not in serialized
    assert "api_key" not in serialized


def test_adapter_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
