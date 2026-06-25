import pytest
from app.output_safety import validate_markdown_output


def test_validate_markdown_output_safe():
    safe_md = "# AI QA Assistant Report\n\nStage Status: SUCCESS\n## Summary\nValid summary text."
    assert validate_markdown_output(safe_md) == safe_md


def test_validate_markdown_output_empty_or_whitespace():
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        validate_markdown_output("")
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        validate_markdown_output("   \n   ")


def test_validate_markdown_output_large():
    # 256 KiB = 262,144 bytes. 262,145 bytes should fail.
    large_md = "A" * 262145
    with pytest.raises(ValueError, match="too large"):
        validate_markdown_output(large_md)


def test_validate_markdown_output_secret_exprs():
    # Valid assignments (>= 6 chars value)
    with pytest.raises(ValueError, match="contains raw secret assignments"):
        validate_markdown_output("api_key='abcdef123456'")
    with pytest.raises(ValueError, match="contains raw secret assignments"):
        validate_markdown_output("password=secret123")
    with pytest.raises(ValueError, match="contains raw secret assignments"):
        validate_markdown_output("secret: abcdef123")
    with pytest.raises(ValueError, match="contains raw secret assignments"):
        validate_markdown_output("token: abcdef123")

    # Short values (< 6 chars) should NOT match
    assert validate_markdown_output("api_key=12345") == "api_key=12345"

    # Bearer tokens (>= 12 chars token)
    with pytest.raises(ValueError, match="contains raw Bearer token pattern"):
        validate_markdown_output("Bearer abc123xyz789TOKEN")

    # Short bearer token or raw word "bearer" should NOT match
    assert validate_markdown_output("bearer short") == "bearer short"
    assert validate_markdown_output("just the word bearer") == "just the word bearer"


def test_validate_markdown_output_tracebacks():
    with pytest.raises(ValueError, match="Traceback"):
        validate_markdown_output("An error occurred:\nTraceback (most recent call last):\n...")
    with pytest.raises(ValueError, match="ValidationError"):
        validate_markdown_output("An error occurred:\nValidationError: ...")
    with pytest.raises(ValueError, match="Exception:"):
        validate_markdown_output("An error occurred:\nException: Something failed")
    with pytest.raises(ValueError, match="Stack trace"):
        validate_markdown_output("Stack trace:\n  File 'app/pipeline.py', line 12")


def test_validate_markdown_output_safety_ids():
    with pytest.raises(ValueError, match="raw safety event IDs"):
        validate_markdown_output("Safety event RED-001 has been triggered.")
    with pytest.raises(ValueError, match="raw safety event IDs"):
        validate_markdown_output("Safety event SIG-102 has been triggered.")

    # Non-matching safety IDs should NOT fail
    allowed_red = "RED-1 is not a valid 3-digit safety ID"
    assert validate_markdown_output(allowed_red) == allowed_red

    allowed_sig = "SIG-1234 is not a valid 3-digit safety ID"
    assert validate_markdown_output(allowed_sig) == allowed_sig


def test_validate_markdown_output_provenance_internals():
    # Key-like structures should be rejected
    with pytest.raises(ValueError, match="source_segment_ids"):
        validate_markdown_output("Internals: SOURCE_SEGMENT_IDS: []")
    with pytest.raises(ValueError, match="derived_from_ids"):
        validate_markdown_output("Internals: Derived_From_Ids: []")
    with pytest.raises(ValueError, match="transformation"):
        validate_markdown_output("Internals: TRANSFORMATION: 'foo'")
    with pytest.raises(ValueError, match="rationale"):
        validate_markdown_output("Details: Rationale: 'none'")

    # Plain business terminology should be ALLOWED
    business_text_1 = "The data transformation rule is documented."
    assert validate_markdown_output(business_text_1) == business_text_1

    business_text_2 = "The rationale is explained in plain business text."
    assert validate_markdown_output(business_text_2) == business_text_2


def test_output_safety_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
