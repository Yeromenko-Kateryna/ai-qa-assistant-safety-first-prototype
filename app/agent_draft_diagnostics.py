import re
import json
from pydantic import ValidationError
from app.domain_models import RequirementAnalysis

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)['\"]?\b(api[_-]?key|password|secret|token)\b['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{6,}['\"]?"
)
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_.-]{12,}\b")


class AgentDraftDiagnosticSummary:
    """Safe diagnostic metadata representing LLM draft validation failures.

    Contains NO prompt, response, or raw payload text.
    """

    def __init__(self):
        self.diagnostic_status: str = "FAILED"
        self.failure_phase: str = ""
        self.safe_error_code: str = ""
        self.root_type: str = ""
        self.missing_top_level_keys: list[str] = []
        self.invalid_field_paths: list[str] = []
        self.safe_expected_type_names: list[str] = []
        self.schema_error_types: list[str] = []
        self.schema_error_type_counts: dict[str, int] = {}
        self.provenance_rule_failed: str | None = None
        self.semantic_rule_failed: str | None = None
        self.payload_values_printed: bool = False


def format_loc(loc) -> str:
    """Formats a Pydantic loc tuple as a safe field path."""
    path = ""
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            if path:
                path += f".{part}"
            else:
                path = str(part)
    return path


def diagnose_agent_draft(draft_text: str) -> AgentDraftDiagnosticSummary:
    """Analyzes a model draft validation failure safely without leaking raw values.

    Returns whitelisted structural metadata only.
    """
    summary = AgentDraftDiagnosticSummary()

    # 1. Unsafe content check (Precedence)
    if SECRET_ASSIGNMENT_PATTERN.search(draft_text) or BEARER_PATTERN.search(draft_text):
        summary.diagnostic_status = "FAILED"
        summary.failure_phase = "UNSAFE"
        summary.safe_error_code = "AGENT_DRAFT_UNSAFE_CONTENT"
        return summary

    # 2. JSON Parse Check
    try:
        data = json.loads(draft_text)
    except json.JSONDecodeError:
        summary.diagnostic_status = "FAILED"
        summary.failure_phase = "PARSE"
        summary.safe_error_code = "AGENT_DRAFT_NOT_JSON"
        return summary

    # 3. Root Node Type Check
    if not isinstance(data, dict):
        summary.diagnostic_status = "FAILED"
        summary.failure_phase = "ROOT_TYPE"
        summary.safe_error_code = "AGENT_DRAFT_ROOT_NOT_OBJECT"
        if isinstance(data, list):
            summary.root_type = "array"
        elif isinstance(data, str):
            summary.root_type = "string"
        elif isinstance(data, bool):
            summary.root_type = "boolean"
        elif isinstance(data, (int, float)):
            summary.root_type = "number"
        elif data is None:
            summary.root_type = "null"
        else:
            summary.root_type = "unknown"
        return summary

    summary.root_type = "object"

    # 4. Missing required top-level keys check
    required_top_level = ["summary", "requirements"]
    missing_keys = [key for key in required_top_level if key not in data]
    if missing_keys:
        summary.diagnostic_status = "FAILED"
        summary.failure_phase = "SCHEMA"
        summary.safe_error_code = "AGENT_DRAFT_VALIDATION_FAILED"
        summary.missing_top_level_keys = missing_keys
        return summary

    # 5. Pydantic validation (Structural/Provenance) Check
    try:
        analysis = RequirementAnalysis.model_validate(data)
    except ValidationError as e:
        summary.diagnostic_status = "FAILED"
        summary.safe_error_code = "AGENT_DRAFT_VALIDATION_FAILED"

        is_provenance = False
        categories = []
        counts = {}
        for err in e.errors():
            loc = err.get("loc", ())
            path_str = format_loc(loc)
            if path_str:
                summary.invalid_field_paths.append(path_str)

            # Map standard Pydantic error type to safe type names
            err_type = err.get("type", "")
            if "int" in err_type:
                summary.safe_expected_type_names.append("integer")
            elif "str" in err_type:
                summary.safe_expected_type_names.append("string")
            elif "bool" in err_type:
                summary.safe_expected_type_names.append("boolean")
            elif "list" in err_type or "array" in err_type:
                summary.safe_expected_type_names.append("array")
            elif "dict" in err_type:
                summary.safe_expected_type_names.append("object")

            # Map Pydantic err.get("type") to safe categories
            # Safe categories: missing, extra_forbidden, model_type, list_type, string_type, enum, value_error, unknown_schema_error
            if err_type == "missing":
                category = "missing"
            elif err_type == "extra_forbidden":
                category = "extra_forbidden"
            elif err_type == "model_type":
                category = "model_type"
            elif err_type == "list_type":
                category = "list_type"
            elif err_type == "string_type":
                category = "string_type"
            elif err_type in ("enum", "literal_error"):
                category = "enum"
            elif err_type == "value_error":
                category = "value_error"
            else:
                category = "unknown_schema_error"

            categories.append(category)
            counts[category] = counts.get(category, 0) + 1

            if "provenance" in loc:
                is_provenance = True
                if "origin" in loc:
                    summary.provenance_rule_failed = "PROVENANCE_ORIGIN_INVALID"
                elif "transformation" in loc:
                    summary.provenance_rule_failed = "PROVENANCE_TRANSFORMATION_INVALID"
                else:
                    summary.provenance_rule_failed = "PROVENANCE_INVARIANT_VIOLATED"

        summary.schema_error_types = sorted(list(set(categories)))
        summary.schema_error_type_counts = {cat: counts[cat] for cat in sorted(counts.keys())}

        if is_provenance:
            summary.failure_phase = "PROVENANCE"
        else:
            summary.failure_phase = "SCHEMA"
        return summary

    # 6. Semantic Validation Check
    try:
        from app.validator import validate_requirement_analysis
        validate_requirement_analysis(analysis)
        summary.diagnostic_status = "SUCCESS"
        summary.safe_error_code = ""
    except ValueError as val_err:
        summary.diagnostic_status = "FAILED"
        summary.failure_phase = "SEMANTIC"
        summary.safe_error_code = "AGENT_DRAFT_VALIDATION_FAILED"
        err_msg = str(val_err)
        if "Duplicate ID" in err_msg:
            summary.semantic_rule_failed = "DUPLICATE_ID"
        elif "references missing dependency" in err_msg:
            summary.semantic_rule_failed = "MISSING_DEPENDENCY_REFERENCE"
        elif "invalid dependency type" in err_msg:
            summary.semantic_rule_failed = "INVALID_DEPENDENCY_TYPE"
        else:
            summary.semantic_rule_failed = "SEMANTIC_INVARIANT_VIOLATED"

    return summary
