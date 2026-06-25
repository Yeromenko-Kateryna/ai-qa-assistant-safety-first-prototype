from app.local_demo import run_local_demo


def test_local_demo_golden_success():
    raw_text = "The checkout page shall allow users to apply a valid discount code."
    markdown = run_local_demo(raw_text)

    # 1. Verification of exact core headers
    headers = [
        "# AI QA Assistant Report",
        "## Stage Status",
        "## Summary",
        "## Requirements",
        "## Acceptance Criteria",
        "## Business Rules",
        "## Ambiguities",
        "## Missing Information",
        "## Assumptions",
    ]

    for h in headers:
        assert h in markdown

    # 2. Verify deterministic header ordering using index positions
    positions = [markdown.index(h) for h in headers]
    assert positions == sorted(positions)

    # 3. Verify status value
    assert "Stage Status: SUCCESS" in markdown

    # 4. Verify requirement rendering
    assert "1. **REQ-001**:" in markdown
    assert raw_text in markdown

    # 5. Verify empty optional sections render "_None._"
    assert "## Acceptance Criteria\n_None._" in markdown
    assert "## Business Rules\n_None._" in markdown
    assert "## Ambiguities\n_None._" in markdown
    assert "## Missing Information\n_None._" in markdown
    assert "## Assumptions\n_None._" in markdown


def test_local_demo_golden_no_leak():
    raw_secret_value = "supersecretpass123"
    raw_secret_expr = "password='supersecretpass123'"
    raw_input = f"Secure login requires: {raw_secret_expr} configuration."

    markdown = run_local_demo(raw_input)

    # Assert status is SUCCESS
    assert "Stage Status: SUCCESS" in markdown

    # Assert secret is redacted and full expression replaced
    assert "[REDACTED_SECRET_001]" in markdown
    assert raw_secret_value not in markdown
    assert raw_secret_expr not in markdown

    # Assert password key label is not present in markdown
    assert "password" not in markdown.lower()


def test_local_demo_golden_deterministic():
    raw_text = "Standard requirement text."
    markdown1 = run_local_demo(raw_text)
    markdown2 = run_local_demo(raw_text)
    assert markdown1 == markdown2
