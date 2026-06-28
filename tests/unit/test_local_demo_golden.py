import sys
from app.local_demo import run_local_demo


def test_local_demo_golden_success(monkeypatch):
    # Mock sys.argv to contain --mock flag
    monkeypatch.setattr(sys, "argv", ["app/local_demo.py", "--mock"])

    markdown = run_local_demo("Ignored text")

    # 1. Verification of exact safe headings
    headers = [
        "# AI QA Assistant Report",
        "## Stage Status",
        "## Summary",
        "## Requirements",
        "## Acceptance Criteria",
    ]

    for h in headers:
        assert h in markdown

    # 2. Verify deterministic header ordering using index positions
    positions = [markdown.index(h) for h in headers]
    assert positions == sorted(positions)

    # 3. Verify status value and mock label
    assert "Stage Status: SUCCESS" in markdown
    assert "[DEMO / MOCK OUTPUT]" in markdown

    # 4. Verify no internal IDs or optional sections appear
    assert "REQ-001" not in markdown
    assert "AC-001" not in markdown
    assert "Business Rules" not in markdown
    assert "Ambiguities" not in markdown
    assert "Missing Information" not in markdown
    assert "Assumptions" not in markdown


def test_local_demo_golden_no_leak(monkeypatch):
    # In mock mode, raw input is ignored and static mock data is returned
    monkeypatch.setattr(sys, "argv", ["app/local_demo.py", "--mock"])
    raw_secret_value = "supersecretpass123"
    raw_secret_expr = "password='supersecretpass123'"
    raw_input = f"Secure login requires: {raw_secret_expr} configuration."

    markdown = run_local_demo(raw_input)

    # Assert status is SUCCESS and no secrets/passwords exist in the static output
    assert "Stage Status: SUCCESS" in markdown
    assert raw_secret_value not in markdown
    assert raw_secret_expr not in markdown
    assert "password" not in markdown.lower()


def test_local_demo_golden_deterministic(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["app/local_demo.py", "--mock"])
    markdown1 = run_local_demo("Ignored text 1")
    markdown2 = run_local_demo("Ignored text 2")
    assert markdown1 == markdown2
