import sys
import pytest
from app.local_demo import run_local_demo


def test_run_local_demo_mock_mode(monkeypatch):
    # Mock sys.argv to contain --mock flag
    monkeypatch.setattr(sys, "argv", ["app/local_demo.py", "--mock"])

    markdown = run_local_demo("Some ignored text")

    # Verify mock/demo label is present
    assert "[DEMO / MOCK OUTPUT]" in markdown

    # Verify headers and safe content
    assert "# AI QA Assistant Report" in markdown
    assert "Stage Status: SUCCESS" in markdown
    assert "## Summary" in markdown
    assert "This is a safe synthetic demo summary" in markdown
    assert "## Requirements" in markdown
    assert "The system shall provide a secure user login interface." in markdown
    assert "The database transactions shall be audited." in markdown
    assert "## Acceptance Criteria" in markdown
    assert "Verify successful login with valid credentials." in markdown

    # Verify complete exclusion of internal IDs, provenance, rationales, and raw dumps
    assert "REQ-001" not in markdown
    assert "REQ-002" not in markdown
    assert "AC-001" not in markdown
    assert "SEG-001" not in markdown
    assert "EXTRACTED" not in markdown
    assert "PROPOSED" not in markdown
    assert "VERBATIM" not in markdown
    assert "source_segment_ids" not in markdown
    assert "derived_from_ids" not in markdown
    assert "provenance" not in markdown
    assert "rationale" not in markdown
    assert "Auditing security requirement" not in markdown
    assert "committed_output" not in markdown
    assert "{" not in markdown
    assert "}" not in markdown


def test_run_local_demo_non_mock_mode(monkeypatch):
    # Mock sys.argv to NOT contain --mock flag
    monkeypatch.setattr(sys, "argv", ["app/local_demo.py"])

    output = run_local_demo("Some raw requirements text")

    # Non-mock mode returns safe unsupported message
    assert "Real-mode analysis is unsupported in local_demo" in output
    assert "[DEMO / MOCK OUTPUT]" not in output
    assert "Stage Status: SUCCESS" not in output
    assert "## Summary" not in output


def test_local_demo_import_isolation():
    # Verify that importing app.local_demo does not trigger active GenAI modules
    import subprocess
    import sys
    cmd = [
        sys.executable,
        "-I",
        "-c",
        "import sys; import app.local_demo; "
        "assert 'app.agent' not in sys.modules; "
        "assert 'google.auth' not in sys.modules; "
        "assert 'google.adk' not in sys.modules; "
        "assert 'google.genai' not in sys.modules; "
        "assert 'app.gemini_requirement_agent_provider' not in sys.modules; "
        "assert 'app.gemini_sdk_client_adapter' not in sys.modules;"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Import isolation check failed: {res.stderr}"
