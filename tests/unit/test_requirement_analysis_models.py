import pytest
from pydantic import ValidationError

from app.domain_models import (
    RequirementAnalysis,
    ExtractedSummary,
    Requirement,
    AcceptanceCriterion,
    BusinessRule,
    Ambiguity,
    MissingInformation,
    Assumption,
    Provenance,
    OriginEnum,
    TransformationEnum,
    RequirementCategoryEnum,
)


def make_extracted_prov() -> Provenance:
    return Provenance(
        origin=OriginEnum.EXTRACTED,
        transformation=TransformationEnum.VERBATIM,
        source_segment_ids=["SEG-001"],
        derived_from_ids=[],
        rationale=None,
    )


def make_proposed_prov() -> Provenance:
    return Provenance(
        origin=OriginEnum.PROPOSED,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=["REQ-001"],
        rationale="Proposed rationale",
    )


def make_inferred_prov() -> Provenance:
    return Provenance(
        origin=OriginEnum.INFERRED,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=["REQ-001"],
        rationale="Inferred rationale",
    )


def make_missing_prov() -> Provenance:
    return Provenance(
        origin=OriginEnum.MISSING_INFORMATION,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=["REQ-001"],
        rationale="Missing info rationale",
    )


def make_assumption_prov() -> Provenance:
    return Provenance(
        origin=OriginEnum.ASSUMPTION,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=["REQ-001"],
        rationale="Assumption rationale",
    )


def make_summary() -> ExtractedSummary:
    return ExtractedSummary(
        text="A valid summary of requirements",
        provenance=make_extracted_prov(),
    )


def make_requirement(req_id: str = "REQ-001") -> Requirement:
    return Requirement(
        id=req_id,
        description="A valid requirement",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_extracted_prov(),
    )


def test_valid_minimal_requirement_analysis() -> None:
    analysis = RequirementAnalysis(
        summary=make_summary(),
        requirements=[make_requirement()],
    )
    assert analysis.summary.text == "A valid summary of requirements"
    assert len(analysis.requirements) == 1
    assert analysis.acceptance_criteria == []
    assert analysis.business_rules == []
    assert analysis.ambiguities == []
    assert analysis.missing_information == []
    assert analysis.assumptions == []


def test_missing_summary_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            requirements=[make_requirement()],
        )
    assert any(
        err["type"] == "missing" and err["loc"] == ("summary",)
        for err in exc_info.value.errors(include_url=False)
    )


def test_empty_requirements_list_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=make_summary(),
            requirements=[],
        )
    assert any(
        err["type"] == "too_short" and err["loc"] == ("requirements",)
        for err in exc_info.value.errors(include_url=False)
    )


def test_list_max_lengths_are_enforced() -> None:
    summary = make_summary()
    prov_ext = make_extracted_prov()
    prov_prop = make_proposed_prov()
    prov_inf = make_inferred_prov()
    prov_miss = make_missing_prov()
    prov_asm = make_assumption_prov()

    # requirements list > 8 rejected
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=summary,
            requirements=[make_requirement(f"REQ-{i:03d}") for i in range(9)],
        )
    assert any(
        err["type"] == "too_long" and err["loc"] == ("requirements",)
        for err in exc_info.value.errors(include_url=False)
    )

    # acceptance_criteria > 20 rejected
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=summary,
            requirements=[make_requirement()],
            acceptance_criteria=[
                AcceptanceCriterion(
                    id=f"AC-{i:03d}",
                    description="AC desc",
                    provenance=prov_prop,
                )
                for i in range(21)
            ],
        )
    assert any(
        err["type"] == "too_long" and err["loc"] == ("acceptance_criteria",)
        for err in exc_info.value.errors(include_url=False)
    )

    # business_rules > 12 rejected
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=summary,
            requirements=[make_requirement()],
            business_rules=[
                BusinessRule(
                    id=f"BR-{i:03d}",
                    description="BR desc",
                    provenance=prov_ext,
                )
                for i in range(13)
            ],
        )
    assert any(
        err["type"] == "too_long" and err["loc"] == ("business_rules",)
        for err in exc_info.value.errors(include_url=False)
    )

    # ambiguities > 10 rejected
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=summary,
            requirements=[make_requirement()],
            ambiguities=[
                Ambiguity(
                    id=f"AMB-{i:03d}",
                    description="AMB desc",
                    provenance=prov_inf,
                )
                for i in range(11)
            ],
        )
    assert any(
        err["type"] == "too_long" and err["loc"] == ("ambiguities",)
        for err in exc_info.value.errors(include_url=False)
    )

    # missing_information > 12 rejected
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=summary,
            requirements=[make_requirement()],
            missing_information=[
                MissingInformation(
                    id=f"MISS-{i:03d}",
                    description="MISS desc",
                    provenance=prov_miss,
                )
                for i in range(13)
            ],
        )
    assert any(
        err["type"] == "too_long" and err["loc"] == ("missing_information",)
        for err in exc_info.value.errors(include_url=False)
    )

    # assumptions > 8 rejected
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=summary,
            requirements=[make_requirement()],
            assumptions=[
                Assumption(
                    id=f"ASM-{i:03d}",
                    description="ASM desc",
                    provenance=prov_asm,
                )
                for i in range(9)
            ],
        )
    assert any(
        err["type"] == "too_long" and err["loc"] == ("assumptions",)
        for err in exc_info.value.errors(include_url=False)
    )


def test_summary_rejects_non_extracted_provenance() -> None:
    non_extracted_origins = [
        OriginEnum.PROPOSED,
        OriginEnum.INFERRED,
        OriginEnum.ASSUMPTION,
        OriginEnum.MISSING_INFORMATION,
    ]

    for origin in non_extracted_origins:
        prov = Provenance(
            origin=origin,
            transformation=TransformationEnum.NONE,
            source_segment_ids=[],
            derived_from_ids=["REQ-001"],
            rationale="Some rationale",
        )
        with pytest.raises(ValidationError) as exc_info:
            ExtractedSummary(
                text="Summary text",
                provenance=prov,
            )
        assert any(
            err["type"] == "value_error" and err["loc"] == ()
            for err in exc_info.value.errors(include_url=False)
        )


def test_extracted_summary_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ExtractedSummary(
            text="Summary text",
            provenance=make_extracted_prov(),
            extra_field="forbidden",
        )
    assert any(
        err["type"] == "extra_forbidden" and err["loc"] == ("extra_field",)
        for err in exc_info.value.errors(include_url=False)
    )


def test_requirement_analysis_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RequirementAnalysis(
            summary=make_summary(),
            requirements=[make_requirement()],
            extra_field="forbidden",
        )
    assert any(
        err["type"] == "extra_forbidden" and err["loc"] == ("extra_field",)
        for err in exc_info.value.errors(include_url=False)
    )
def test_summary_text_length_limit() -> None:
    prov = make_extracted_prov()

    # 4000 characters is accepted
    summary_4000 = ExtractedSummary(text="A" * 4000, provenance=prov)
    assert len(summary_4000.text) == 4000

    # 4001 characters is rejected
    with pytest.raises(ValidationError) as exc_info:
        ExtractedSummary(text="A" * 4001, provenance=prov)
    assert any(
        err["type"] == "string_too_long" and err["loc"] == ("text",)
        for err in exc_info.value.errors(include_url=False)
    )


def test_import_isolation() -> None:
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
