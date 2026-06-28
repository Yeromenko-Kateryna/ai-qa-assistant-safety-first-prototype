import sys


def _generate_mock_output() -> str:
    """Generates the committed synthetic mock output safely."""
    from app.domain_models import (
        RequirementAnalysis,
        StageResult,
        StageStatus,
        ExtractedSummary,
        Requirement,
        RequirementCategoryEnum,
        AcceptanceCriterion,
        OriginEnum,
        Provenance,
        TransformationEnum,
    )
    from app.renderer import render_safe_requirement_analysis_markdown
    from app.output_safety import validate_markdown_output

    # Construct safe committed synthetic mock data
    summary_provenance = Provenance(
        origin=OriginEnum.EXTRACTED,
        transformation=TransformationEnum.SUMMARY,
        source_segment_ids=["SEG-001"],
        derived_from_ids=[],
        rationale=None,
    )
    summary = ExtractedSummary(
        text="This is a safe synthetic demo summary of the system requirements.",
        provenance=summary_provenance,
    )

    req_provenance = Provenance(
        origin=OriginEnum.EXTRACTED,
        transformation=TransformationEnum.VERBATIM,
        source_segment_ids=["SEG-001"],
        derived_from_ids=[],
        rationale=None,
    )
    req1 = Requirement(
        id="REQ-001",
        description="The system shall provide a secure user login interface.",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=req_provenance,
    )
    req2 = Requirement(
        id="REQ-002",
        description="The database transactions shall be audited.",
        category=RequirementCategoryEnum.NON_FUNCTIONAL,
        provenance=req_provenance,
    )

    ac_provenance = Provenance(
        origin=OriginEnum.PROPOSED,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=["REQ-001"],
        rationale="Auditing security requirement requires explicit criteria.",
    )
    ac1 = AcceptanceCriterion(
        id="AC-001",
        description="Verify successful login with valid credentials.",
        provenance=ac_provenance,
    )

    mock_analysis = RequirementAnalysis(
        summary=summary,
        requirements=[req1, req2],
        acceptance_criteria=[ac1],
        business_rules=[],
        ambiguities=[],
        missing_information=[],
        assumptions=[],
    )

    mock_result = StageResult(
        status=StageStatus.SUCCESS,
        committed_output=mock_analysis,
    )

    markdown = render_safe_requirement_analysis_markdown(mock_result)
    labeled_markdown = f"[DEMO / MOCK OUTPUT]\n{markdown}"
    return validate_markdown_output(labeled_markdown)


def run_local_demo(raw_text: str) -> str:
    """Runs local_demo in mock/demo mode if --mock flag is present. Real-mode is unsupported."""
    if "--mock" in sys.argv:
        return _generate_mock_output()
    else:
        return "Real-mode analysis is unsupported in local_demo. Run with --mock flag to execute mock mode."


def main(argv=None) -> None:
    """CLI entrypoint to run local_demo and print output to stdout."""
    args = list(sys.argv[1:] if argv is None else argv)
    if "--mock" in args:
        print(_generate_mock_output())
    else:
        print("Real-mode analysis is unsupported in local_demo. Run with --mock flag to execute mock mode.")


if __name__ == "__main__":
    main()
