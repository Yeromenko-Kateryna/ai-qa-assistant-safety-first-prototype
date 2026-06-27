import sys
from app.agent_draft_diagnostics import diagnose_agent_draft

def test_diagnose_import_isolation():
    # Verify that importing the script does not load genai or check keys
    assert "google.genai" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "app.agent" not in sys.modules


def test_unsafe_content_precedence():
    # Secret pattern in input matching the word boundary regex
    fake_unsafe = "api_key = 'AIzaSyFakeKeyValue'"
    summary = diagnose_agent_draft(fake_unsafe)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "UNSAFE"
    assert summary.safe_error_code == "AGENT_DRAFT_UNSAFE_CONTENT"
    # Ensure no structural details or keys are reported
    assert not summary.missing_top_level_keys
    assert not summary.invalid_field_paths
    assert not summary.root_type
    # Ensure secret is not leaked in representation
    serialized = str(summary.__dict__)
    assert "AIzaSyFakeKeyValue" not in serialized


def test_malformed_json_failure():
    fake_malformed = "not valid json {{"
    summary = diagnose_agent_draft(fake_malformed)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "PARSE"
    assert summary.safe_error_code == "AGENT_DRAFT_NOT_JSON"
    assert "not valid json" not in str(summary.__dict__)


def test_non_object_root_failure():
    fake_array_root = "[1, 2, 3]"
    summary = diagnose_agent_draft(fake_array_root)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "ROOT_TYPE"
    assert summary.safe_error_code == "AGENT_DRAFT_ROOT_NOT_OBJECT"
    assert summary.root_type == "array"


def test_missing_summary():
    fake_missing_summary = '{"requirements": []}'
    summary = diagnose_agent_draft(fake_missing_summary)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "SCHEMA"
    assert summary.safe_error_code == "AGENT_DRAFT_VALIDATION_FAILED"
    assert "summary" in summary.missing_top_level_keys
    assert "requirements" not in summary.missing_top_level_keys


def test_missing_requirements():
    fake_missing_reqs = '{"summary": {}}'
    summary = diagnose_agent_draft(fake_missing_reqs)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "SCHEMA"
    assert summary.safe_error_code == "AGENT_DRAFT_VALIDATION_FAILED"
    assert "requirements" in summary.missing_top_level_keys
    assert "summary" not in summary.missing_top_level_keys


def test_wrong_provenance_origin():
    # Valid outer structure but wrong origin type in requirements
    fake_wrong_origin = """{
      "summary": {
        "text": "Valid text summary",
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
          "description": "Valid description",
          "category": "FUNCTIONAL",
          "provenance": {
            "origin": "INVALID_ORIGIN_VALUE",
            "transformation": "VERBATIM",
            "source_segment_ids": ["SEG-001"],
            "derived_from_ids": [],
            "rationale": null
          }
        }
      ]
    }"""
    summary = diagnose_agent_draft(fake_wrong_origin)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "PROVENANCE"
    assert summary.safe_error_code == "AGENT_DRAFT_VALIDATION_FAILED"
    assert "requirements[0].provenance.origin" in summary.invalid_field_paths
    assert summary.provenance_rule_failed == "PROVENANCE_ORIGIN_INVALID"
    # Ensure raw invalid string is not returned in summary dict
    serialized = str(summary.__dict__)
    assert "INVALID_ORIGIN_VALUE" not in serialized


def test_semantic_dependency_failure():
    # Model draft where derived_from_ids references REQ-999 but it is missing.
    # Provenance fields must be valid under Pydantic schemas so that structural check passes.
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
    summary = diagnose_agent_draft(fake_semantic_fail)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "SEMANTIC"
    assert summary.safe_error_code == "AGENT_DRAFT_VALIDATION_FAILED"
    assert summary.semantic_rule_failed == "MISSING_DEPENDENCY_REFERENCE"
    # Ensure no payload leak
    serialized = str(summary.__dict__)
    assert "REQ-999" not in serialized
    assert "Validation check criterion" not in serialized


def test_pydantic_error_sanitization():
    # Generate schema failure by providing a string instead of a list for requirements
    fake_wrong_type = """{
      "summary": {
        "text": "Valid text summary",
        "provenance": {
          "origin": "EXTRACTED",
          "transformation": "SUMMARY",
          "source_segment_ids": ["SEG-001"],
          "derived_from_ids": [],
          "rationale": null
        }
      },
      "requirements": "this should be a list"
    }"""
    summary = diagnose_agent_draft(fake_wrong_type)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "SCHEMA"
    assert "requirements" in summary.invalid_field_paths
    assert "array" in summary.safe_expected_type_names

    # Ensure no Pydantic raw dictionary leak (like ctx, input, url, msg)
    serialized = str(summary.__dict__)
    assert "this should be a list" not in serialized
    assert "ctx" not in serialized
    assert "url" not in serialized
    assert "input" not in serialized
    assert "msg" not in serialized

    # Strengthened sanitization assertions for common Pydantic message texts
    assert "Input should be" not in serialized
    assert "valid list" not in serialized


def test_no_payload_leaks_regression():
    # Test draft with custom payloads, Rationales, Segment Texts, Enums, missing dependencies and fake API keys
    fake_payload = """{
      "summary": {
        "text": "ExtremelyUniqueModelSummaryTextToShowLeakInSummaryString",
        "provenance": {
          "origin": "EXTRACTED",
          "transformation": "SUMMARY",
          "source_segment_ids": ["SEG-888UniqueSegmentNameToShowLeak"],
          "derived_from_ids": [],
          "rationale": null
        }
      },
      "requirements": [
        {
          "id": "REQ-001",
          "description": "ExtremelyUniqueModelRequirementDescriptionTextToShowLeak",
          "category": "FUNCTIONAL",
          "provenance": {
            "origin": "EXTRACTED",
            "transformation": "VERBATIM",
            "source_segment_ids": ["SEG-888UniqueSegmentNameToShowLeak"],
            "derived_from_ids": [],
            "rationale": null
          }
        }
      ],
      "acceptance_criteria": [
        {
          "id": "AC-001",
          "description": "UniqueAcceptanceCriteriaDescriptionText",
          "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-777MissingDependencyIDLeakCheck"],
            "rationale": "UniqueProposedRationaleTextToShowLeak"
          }
        }
      ],
      "business_rules": [],
      "ambiguities": [],
      "missing_information": [],
      "assumptions": []
    }"""

    summary = diagnose_agent_draft(fake_payload)
    serialized = str(summary.__dict__)

    # Assert diagnostic summary never includes payload values
    assert "ExtremelyUniqueModelSummaryTextToShowLeakInSummaryString" not in serialized
    assert "SEG-888UniqueSegmentNameToShowLeak" not in serialized
    assert "ExtremelyUniqueModelRequirementDescriptionTextToShowLeak" not in serialized
    assert "UniqueAcceptanceCriteriaDescriptionText" not in serialized
    assert "REQ-777MissingDependencyIDLeakCheck" not in serialized
    assert "UniqueProposedRationaleTextToShowLeak" not in serialized
    assert "api_key" not in serialized
    assert "secret" not in serialized
    assert summary.payload_values_printed is False


def test_unsafe_json_key_precedence_regression():
    # Test JSON-style secret keys detection
    fake_json_unsafe = '{"api_key": "SyntheticSecretValue123456"}'
    summary = diagnose_agent_draft(fake_json_unsafe)

    assert summary.diagnostic_status == "FAILED"
    assert summary.failure_phase == "UNSAFE"
    assert summary.safe_error_code == "AGENT_DRAFT_UNSAFE_CONTENT"

    # Ensure no structural details or keys are reported
    assert not summary.missing_top_level_keys
    assert not summary.invalid_field_paths
    assert not summary.root_type

    # Ensure secret is not leaked in serialized summary representation
    serialized = str(summary.__dict__)
    assert "api_key" not in serialized
    assert "SyntheticSecretValue123456" not in serialized
    assert "secret" not in serialized


def test_pydantic_error_categories():
    import json

    # Helper to construct a base draft dict
    def get_base_dict():
        return {
            "summary": {
                "text": "Valid summary text",
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
                    "description": "System health status indicator.",
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

    # 1. ambiguity item as string
    d = get_base_dict()
    d["ambiguities"] = ["Ambiguity string"]
    sum1 = diagnose_agent_draft(json.dumps(d))
    assert sum1.failure_phase == "SCHEMA"
    assert "model_type" in sum1.schema_error_types
    assert sum1.schema_error_type_counts["model_type"] == 1
    assert "ambiguities[0]" in sum1.invalid_field_paths

    # 2. missing required id
    d = get_base_dict()
    d["ambiguities"] = [{
        "description": "Refresh rate not defined.",
        "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-001"],
            "rationale": "Identifying refresh rate ambiguity."
        }
    }]
    sum2 = diagnose_agent_draft(json.dumps(d))
    assert sum2.failure_phase == "SCHEMA"
    assert "missing" in sum2.schema_error_types
    assert sum2.schema_error_type_counts["missing"] == 1
    assert "ambiguities[0].id" in sum2.invalid_field_paths

    # 3. text instead of description
    d = get_base_dict()
    d["ambiguities"] = [{
        "id": "AMB-001",
        "text": "Refresh rate not defined.",
        "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-001"],
            "rationale": "Identifying refresh rate ambiguity."
        }
    }]
    sum3 = diagnose_agent_draft(json.dumps(d))
    assert sum3.failure_phase == "SCHEMA"
    assert "missing" in sum3.schema_error_types  # missing description
    assert "extra_forbidden" in sum3.schema_error_types  # extra key 'text'
    assert sum3.schema_error_type_counts["missing"] == 1
    assert sum3.schema_error_type_counts["extra_forbidden"] == 1
    assert "ambiguities[0].description" in sum3.invalid_field_paths
    assert "ambiguities[0].text" in sum3.invalid_field_paths

    # 4. extra arbitrary key
    d = get_base_dict()
    d["ambiguities"] = [{
        "id": "AMB-001",
        "description": "Refresh rate not defined.",
        "extra_arbitrary_key": "some_value",
        "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-001"],
            "rationale": "Identifying refresh rate ambiguity."
        }
    }]
    sum4 = diagnose_agent_draft(json.dumps(d))
    assert sum4.failure_phase == "SCHEMA"
    assert "extra_forbidden" in sum4.schema_error_types
    assert sum4.schema_error_type_counts["extra_forbidden"] == 1
    assert "ambiguities[0].extra_arbitrary_key" in sum4.invalid_field_paths

    # 5. id as integer
    d = get_base_dict()
    d["ambiguities"] = [{
        "id": 123,
        "description": "Refresh rate not defined.",
        "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-001"],
            "rationale": "Identifying refresh rate ambiguity."
        }
    }]
    sum5 = diagnose_agent_draft(json.dumps(d))
    assert sum5.failure_phase == "SCHEMA"
    assert "string_type" in sum5.schema_error_types
    assert sum5.schema_error_type_counts["string_type"] == 1
    assert "ambiguities[0].id" in sum5.invalid_field_paths

    # 6. ambiguities object instead of list
    d = get_base_dict()
    d["ambiguities"] = {"not": "a list"}
    sum6 = diagnose_agent_draft(json.dumps(d))
    assert sum6.failure_phase == "SCHEMA"
    assert "list_type" in sum6.schema_error_types
    assert sum6.schema_error_type_counts["list_type"] == 1
    assert "ambiguities" in sum6.invalid_field_paths

    # 7. invalid requirement category
    d = get_base_dict()
    d["requirements"][0]["category"] = "INVALID_CATEGORY_VALUE"
    sum7 = diagnose_agent_draft(json.dumps(d))
    assert sum7.failure_phase == "SCHEMA"
    assert "enum" in sum7.schema_error_types
    assert sum7.schema_error_type_counts["enum"] == 1
    assert "requirements[0].category" in sum7.invalid_field_paths

    # 8. unsafe api_key-like draft -> UNSAFE precedence
    # Verify no schema_error_types, schema_error_type_counts, invalid_field_paths
    fake_unsafe = '{"api_key": "SyntheticSecretValue123456", "requirements": "invalid_type"}'
    sum8 = diagnose_agent_draft(fake_unsafe)
    assert sum8.failure_phase == "UNSAFE"
    assert not sum8.schema_error_types
    assert not sum8.schema_error_type_counts
    assert not sum8.invalid_field_paths
    assert not sum8.safe_expected_type_names

    # 9. no leaks of raw msg/input/ctx/url, payload values, etc.
    d = get_base_dict()
    d["ambiguities"] = [{
        "id": "AMB-001",
        "description": "UniqueAmbiguityDescriptionLeakCheckValue",
        "extra_forbidden_key_leak_check": "ExtraForbiddenKeyLeakCheckValue",
        "provenance": {
            "origin": "PROPOSED",
            "transformation": "NONE",
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-001"],
            "rationale": "UniqueAmbiguityRationaleLeakCheckValue"
        }
    }]
    sum9 = diagnose_agent_draft(json.dumps(d))
    serialized = str(sum9.__dict__)
    assert "UniqueAmbiguityDescriptionLeakCheckValue" not in serialized
    assert "ExtraForbiddenKeyLeakCheckValue" not in serialized
    assert "UniqueAmbiguityRationaleLeakCheckValue" not in serialized
    assert "msg" not in serialized
    assert "input" not in serialized
    assert "ctx" not in serialized
    assert "url" not in serialized
    assert "repr" not in serialized
    assert "e.errors" not in serialized
