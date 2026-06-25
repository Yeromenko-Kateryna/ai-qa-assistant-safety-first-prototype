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
from app.renderer import render_requirement_analysis_markdown


def make_provenance(
    origin=OriginEnum.EXTRACTED,
    trans=TransformationEnum.VERBATIM,
    segments=None,
    derived=None,
):
    return Provenance(
        origin=origin,
        transformation=trans,
        source_segment_ids=segments or ["SEG-001"],
        derived_from_ids=derived or [],
        rationale=None,
    )


def test_renderer_success_full():
    summary = ExtractedSummary(
        text="A brief summary.",
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
        description="Acceptance criterion description",
        provenance=make_provenance(),
    )

    analysis = RequirementAnalysis(
        summary=summary,
        requirements=[req2, req1],  # Unordered to check sorting
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

    markdown = render_requirement_analysis_markdown(result)

    # Headers in correct order
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

    # Assert all headings exist
    for h in headers:
        assert h in markdown

    # Assert headings are in correct order using index positions
    positions = [markdown.index(h) for h in headers]
    assert positions == sorted(positions)

    # Check status and summary
    assert "Stage Status: SUCCESS" in markdown
    assert "A brief summary." in markdown

    # Check requirement sorted order and format
    assert "1. **REQ-001**: Functional description 1" in markdown
    assert "2. **REQ-002**: Functional description 2" in markdown
    req1_idx = markdown.find("REQ-001")
    req2_idx = markdown.find("REQ-002")
    assert req1_idx < req2_idx

    # Check AC format
    assert "- **AC-001**: Acceptance criterion description" in markdown

    # Check empty list format
    assert "## Business Rules\n_None._" in markdown
    assert "## Ambiguities\n_None._" in markdown

    # Verify no internal provenance details leaked (e.g. OriginEnum, TransformationEnum, source_segment_ids)
    assert "EXTRACTED" not in markdown
    assert "VERBATIM" not in markdown
    assert "SEG-001" not in markdown


def test_renderer_success_stable():
    # Verify exact determinism across calls
    summary = ExtractedSummary(text="Summary text", provenance=make_provenance())
    req = Requirement(
        id="REQ-001",
        description="Desc",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_provenance(),
    )
    analysis = RequirementAnalysis(summary=summary, requirements=[req])
    result = StageResult(status=StageStatus.SUCCESS, committed_output=analysis)

    markdown1 = render_requirement_analysis_markdown(result)
    markdown2 = render_requirement_analysis_markdown(result)
    assert markdown1 == markdown2


def test_renderer_failed():
    # Setup raw-looking inputs to ensure safety leaks checks are strict
    raw_secret = "supersecretpass123"
    raw_candidate_text = "password='supersecretpass123'"

    result = StageResult(
        status=StageStatus.FAILED,
        error_code="STRUCTURAL_VALIDATION_FAILED",
        safe_message="Unsafe candidate data rejected.",
    )

    markdown = render_requirement_analysis_markdown(result)

    assert "# AI QA Assistant Report" in markdown
    assert "## Stage Status" in markdown
    assert "Stage Status: FAILED" in markdown
    assert "## Error" in markdown
    assert "Error Code: STRUCTURAL_VALIDATION_FAILED" in markdown
    assert "Message: Unsafe candidate data rejected." in markdown

    # Assert committed_output, raw exception/secret/label fragments are omitted
    assert "committed_output" not in markdown
    assert "## Summary" not in markdown

    # Assert domain headings are completely omitted in failed reports
    assert "## Requirements" not in markdown
    assert "## Acceptance Criteria" not in markdown
    assert "## Business Rules" not in markdown
    assert "## Ambiguities" not in markdown
    assert "## Missing Information" not in markdown
    assert "## Assumptions" not in markdown

    # Strict safety leak checks
    assert raw_secret not in markdown
    assert raw_candidate_text not in markdown
    assert "password" not in markdown.lower()


def test_renderer_not_started_or_skipped():
    # NOT_STARTED StageResult created without safe_message (as per Pydantic invariants)
    result_ns = StageResult(
        status=StageStatus.NOT_STARTED,
    )
    markdown_ns = render_requirement_analysis_markdown(result_ns)
    assert "Stage Status: NOT_STARTED" in markdown_ns
    assert "## Note" not in markdown_ns

    # SKIPPED StageResult with safe_message (allowed by invariants in Slice 4/5/6)
    result_skip = StageResult(
        status=StageStatus.SKIPPED,
        safe_message="Deferred note message.",
    )
    markdown_skip = render_requirement_analysis_markdown(result_skip)
    assert "Stage Status: SKIPPED" in markdown_skip
    assert "## Note" in markdown_skip
    assert "Deferred note message." in markdown_skip


def test_renderer_success_empty_sections_all_render_none():
    summary = ExtractedSummary(
        text="A brief summary.",
        provenance=make_provenance(trans=TransformationEnum.SUMMARY),
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
    markdown = render_requirement_analysis_markdown(result)

    assert "## Acceptance Criteria\n_None._" in markdown
    assert "## Business Rules\n_None._" in markdown
    assert "## Ambiguities\n_None._" in markdown
    assert "## Missing Information\n_None._" in markdown
    assert "## Assumptions\n_None._" in markdown


def test_renderer_import_isolation():
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
