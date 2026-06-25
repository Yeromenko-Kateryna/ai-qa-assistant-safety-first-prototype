import pytest
from app.local_demo import run_local_demo


def test_run_local_demo_success():
    raw_text = "The authentication page shall process email login requests."
    markdown = run_local_demo(raw_text)

    # Verifications
    assert "# AI QA Assistant Report" in markdown
    assert "Stage Status: SUCCESS" in markdown
    assert "## Summary" in markdown
    assert "## Requirements" in markdown
    assert raw_text in markdown
    assert "REQ-001" in markdown


def test_run_local_demo_redacted_secrets():
    raw_secret_value = "supersecretpass123"
    raw_secret_expr = f"password='{raw_secret_value}'"
    raw_input = f"Configure database connection: {raw_secret_expr} in properties."

    markdown = run_local_demo(raw_input)

    # Assert secret and secret expression are redacted from output markdown
    assert raw_secret_value not in markdown
    assert raw_secret_expr not in markdown
    assert "[REDACTED_SECRET_" in markdown

    # Assert password key label is not present in markdown
    assert "password" not in markdown.lower()


def test_run_local_demo_empty_input_raises_value_error():
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        run_local_demo("")
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        run_local_demo("   \n   ")


def test_run_local_demo_long_input_raises_value_error():
    long_text = "A" * 2001
    with pytest.raises(
        ValueError, match="exceeds single segment limit of 2,000 characters"
    ):
        run_local_demo(long_text)


def test_local_demo_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules


def test_run_local_demo_uses_output_safety(monkeypatch):
    called_with = None

    def mock_validate(markdown):
        nonlocal called_with
        called_with = markdown
        return "MOCKED_SAFE_OUTPUT"

    monkeypatch.setattr(
        "app.local_demo.validate_markdown_output", mock_validate
    )
    result = run_local_demo("Valid raw text.")
    assert called_with is not None
    assert "Stage Status: SUCCESS" in called_with
    assert "Valid raw text." in called_with
    assert result == "MOCKED_SAFE_OUTPUT"
