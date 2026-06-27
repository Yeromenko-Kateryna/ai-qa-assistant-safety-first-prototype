import sys
from app.domain_models import (
    AcceptanceCriterion,
    ExtractedSummary,
    OriginEnum,
    Provenance,
    Requirement,
    RequirementAnalysis,
    RequirementCategoryEnum,
    StageResult,
    StageStatus,
    TransformationEnum,
)
from app.renderer import render_safe_requirement_analysis_markdown


def make_provenance(
    origin=OriginEnum.EXTRACTED,
    trans=TransformationEnum.VERBATIM,
    segments=None,
    derived=None,
    rationale=None,
):
    return Provenance(
        origin=origin,
        transformation=trans,
        source_segment_ids=segments if segments is not None else ["SEG-001"],
        derived_from_ids=derived or [],
        rationale=rationale,
    )


def test_renderer_success_full():
    summary = ExtractedSummary(
        text="A brief <summary> summary text.",
        provenance=make_provenance(trans=TransformationEnum.SUMMARY),
    )
    req1 = Requirement(
        id="REQ-001",
        description="Functional description 1",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_provenance(),
    )
    req2 = Requirement(
        id="REQ-002",
        description="Functional description 2",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_provenance(),
    )
    ac = AcceptanceCriterion(
        id="AC-001",
        description="Acceptance criterion description text",
        provenance=make_provenance(
            origin=OriginEnum.PROPOSED,
            trans=TransformationEnum.NONE,
            segments=[],
            derived=["REQ-001"],
            rationale="internal rationale context text",
        ),
    )

    analysis = RequirementAnalysis(
        summary=summary,
        requirements=[req2, req1],
        acceptance_criteria=[ac],
        business_rules=[],
        ambiguities=[],
        missing_information=[],
        assumptions=[],
    )

    result = StageResult(
        status=StageStatus.SUCCESS,
        committed_output=analysis,
    )

    markdown = render_safe_requirement_analysis_markdown(result)

    # 1. SUCCESS output includes safe content
    assert "A brief  summary text." in markdown  # sanitized summary text (stripped tag <summary>)
    assert "Functional description 1" in markdown
    assert "Functional description 2" in markdown
    assert "FUNCTIONAL" in markdown
    assert "Acceptance criterion description text" in markdown

    # 2. SUCCESS output excludes internal IDs, provenance, secrets, and raw objects
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
    assert "internal rationale context text" not in markdown
    assert "committed_output" not in markdown
    assert "StageResult" not in markdown
    assert "{" not in markdown
    assert "}" not in markdown
    assert "[" not in markdown.replace("-[FUNCTIONAL]", "").replace("[FUNCTIONAL]", "")

    # Exclude internal optional arrays headings
    assert "Business Rules" not in markdown
    assert "Ambiguities" not in markdown
    assert "Missing Information" not in markdown
    assert "Assumptions" not in markdown


def test_renderer_failed():
    # Setup raw inputs that must never leak
    secret_text = "privatekey_12345"
    pydantic_error_trace = "ValidationError: 1 validation error for RequirementAnalysis"

    result = StageResult(
        status=StageStatus.FAILED,
        error_code="STRUCTURAL_VALIDATION_FAILED",
        safe_message="Unsafe candidate data rejected.",
    )

    markdown = render_safe_requirement_analysis_markdown(result)

    # FAILED output contains safe failure message and code
    assert "Requirement analysis failed: structural or semantic validation error." in markdown
    assert "Error Code: STRUCTURAL_VALIDATION_FAILED" in markdown

    # FAILED output excludes sensitive diagnostics and model texts
    assert secret_text not in markdown
    assert pydantic_error_trace not in markdown
    assert "Message:" not in markdown
    assert "Unsafe candidate data rejected." not in markdown
    assert "committed_output" not in markdown
    assert "Summary" not in markdown
    assert "Requirements" not in markdown
    assert "Acceptance Criteria" not in markdown


def test_renderer_success_empty_acceptance_criteria():
    summary = ExtractedSummary(
        text="A brief summary.",
        provenance=make_provenance(),
    )
    req = Requirement(
        id="REQ-001",
        description="Functional description 1",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_provenance(),
    )
    analysis = RequirementAnalysis(
        summary=summary,
        requirements=[req],
        acceptance_criteria=[],
        business_rules=[],
        ambiguities=[],
        missing_information=[],
        assumptions=[],
    )
    result = StageResult(
        status=StageStatus.SUCCESS,
        committed_output=analysis,
    )
    markdown = render_safe_requirement_analysis_markdown(result)

    assert "No acceptance criteria available." in markdown
    assert "Business Rules" not in markdown
    assert "Ambiguities" not in markdown


def test_renderer_import_isolation():
    import subprocess
    import sys
    cmd = [
        sys.executable,
        "-I",
        "-c",
        "import sys; import app.renderer; "
        "assert 'app.agent' not in sys.modules; "
        "assert 'google.auth' not in sys.modules; "
        "assert 'google.adk' not in sys.modules; "
        "assert 'google.genai' not in sys.modules; "
        "assert 'app.gemini_requirement_agent_provider' not in sys.modules; "
        "assert 'app.gemini_sdk_client_adapter' not in sys.modules;"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Import isolation check failed: {res.stderr}"
