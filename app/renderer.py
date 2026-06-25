from app.domain_models import RequirementAnalysis, StageResult, StageStatus


def render_requirement_analysis_markdown(
    result: StageResult[RequirementAnalysis],
) -> str:
    """Renders a deterministic Markdown report for a StageResult[RequirementAnalysis]."""
    lines = ["# AI QA Assistant Report", ""]

    # 1. Stage Status Section
    lines.extend(["## Stage Status", f"Stage Status: {result.status.value}", ""])

    if result.status == StageStatus.SUCCESS:
        # SUCCESS rendering behavior
        committed = result.committed_output
        if committed is None:
            raise ValueError("SUCCESS status requires committed_output")

        # 2. Summary
        lines.extend(["## Summary", committed.summary.text, ""])

        # 3. Requirements (sorted by ID, rendered as a numbered list)
        lines.append("## Requirements")
        if committed.requirements:
            sorted_reqs = sorted(committed.requirements, key=lambda r: r.id)
            for idx, req in enumerate(sorted_reqs, 1):
                lines.append(f"{idx}. **{req.id}**: {req.description}")
        else:
            lines.append("_None._")
        lines.append("")

        # Helper to render other entity lists
        def render_entity_section(heading: str, entities: list) -> None:
            lines.append(f"## {heading}")
            if entities:
                sorted_entities = sorted(entities, key=lambda e: e.id)
                for ent in sorted_entities:
                    lines.append(f"- **{ent.id}**: {ent.description}")
            else:
                lines.append("_None._")
            lines.append("")

        # 4. Acceptance Criteria
        render_entity_section("Acceptance Criteria", committed.acceptance_criteria)

        # 5. Business Rules
        render_entity_section("Business Rules", committed.business_rules)

        # 6. Ambiguities
        render_entity_section("Ambiguities", committed.ambiguities)

        # 7. Missing Information
        render_entity_section("Missing Information", committed.missing_information)

        # 8. Assumptions
        render_entity_section("Assumptions", committed.assumptions)

    elif result.status == StageStatus.FAILED:
        # FAILED rendering behavior
        lines.append("## Error")
        if result.error_code:
            lines.append(f"Error Code: {result.error_code}")
        if result.safe_message:
            lines.append(f"Message: {result.safe_message}")
        lines.append("")

    elif result.status == StageStatus.SKIPPED:
        # SKIPPED note rendering is allowed if a safe_message exists (upstream skipped routing deferred)
        if result.safe_message:
            lines.extend(["## Note", result.safe_message, ""])

    return "\n".join(lines)
