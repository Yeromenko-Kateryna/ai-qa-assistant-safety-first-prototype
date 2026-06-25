import pytest

from app.domain_models import (
    AcceptanceCriterion,
    Ambiguity,
    Assumption,
    BusinessRule,
    ExtractedSummary,
    MissingInformation,
    OriginEnum,
    Provenance,
    Requirement,
    RequirementAnalysis,
    RequirementCategoryEnum,
    TransformationEnum,
)
from app.validator import validate_requirement_analysis


def make_extracted_prov() -> Provenance:
    return Provenance(
        origin=OriginEnum.EXTRACTED,
        transformation=TransformationEnum.VERBATIM,
        source_segment_ids=["SEG-001"],
        derived_from_ids=[],
        rationale=None,
    )


def make_proposed_prov(derived_from_ids: list[str]) -> Provenance:
    return Provenance(
        origin=OriginEnum.PROPOSED,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=derived_from_ids,
        rationale="Proposed rationale",
    )


def make_inferred_prov(derived_from_ids: list[str]) -> Provenance:
    return Provenance(
        origin=OriginEnum.INFERRED,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=derived_from_ids,
        rationale="Inferred rationale",
    )


def make_missing_prov(derived_from_ids: list[str]) -> Provenance:
    return Provenance(
        origin=OriginEnum.MISSING_INFORMATION,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=derived_from_ids,
        rationale="Missing info rationale",
    )


def make_assumption_prov(derived_from_ids: list[str]) -> Provenance:
    return Provenance(
        origin=OriginEnum.ASSUMPTION,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=derived_from_ids,
        rationale="Assumption rationale",
    )


def make_summary() -> ExtractedSummary:
    return ExtractedSummary(
        text="A valid summary of requirements",
        provenance=make_extracted_prov(),
    )


def test_valid_requirement_analysis_passes() -> None:
    req = Requirement(
        id="REQ-001",
        description="Functional req",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_extracted_prov(),
    )
    ac = AcceptanceCriterion(
        id="AC-001",
        description="Proposed AC",
        provenance=make_proposed_prov(["REQ-001"]),
    )
    br = BusinessRule(
        id="BR-001",
        description="Extracted BR",
        provenance=make_extracted_prov(),
    )
    amb = Ambiguity(
        id="AMB-001",
        description="Inferred ambiguity",
        provenance=make_inferred_prov(["AC-001"]),
    )
    miss = MissingInformation(
        id="MISS-001",
        description="Missing info",
        provenance=make_missing_prov(["BR-001"]),
    )
    asm = Assumption(
        id="ASM-001",
        description="Assumption details",
        provenance=make_assumption_prov(["AMB-001", "MISS-001"]),
    )

    analysis = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        acceptance_criteria=[ac],
        business_rules=[br],
        ambiguities=[amb],
        missing_information=[miss],
        assumptions=[asm],
    )

    # Must pass without raising ValueError
    validate_requirement_analysis(analysis)


def test_type_validation_runs_before_existence_validation() -> None:
    # We verify that an invalid prefix fails type validation first,
    # even when that invalid ID does not exist in the report.
    req = Requirement(
        id="REQ-001",
        description="Req",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_extracted_prov(),
    )
    asm = Assumption(
        id="ASM-001",
        description="Assumption with invalid prefix dependency",
        # RISK is not allowed in Assumption's matrix list (REQ, AC, BR, AMB, MISS)
        # Even though RISK-001 is absent, it must trigger type validation error first.
        provenance=make_assumption_prov(["RISK-001"]),
    )
    analysis = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        assumptions=[asm],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis)
    assert "invalid dependency type" in str(exc_info.value)


def test_missing_referenced_id_with_valid_prefix_rejected() -> None:
    req = Requirement(
        id="REQ-001",
        description="Req",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_extracted_prov(),
    )
    # AC-001 has valid prefix "REQ" but REQ-999 is missing from the report
    ac = AcceptanceCriterion(
        id="AC-001",
        description="AC",
        provenance=make_proposed_prov(["REQ-999"]),
    )
    analysis = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        acceptance_criteria=[ac],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis)
    assert "references missing dependency" in str(exc_info.value)


def test_invalid_dependency_types_rejected() -> None:
    req = Requirement(
        id="REQ-001",
        description="Req",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=make_extracted_prov(),
    )
    amb = Ambiguity(
        id="AMB-001",
        description="Ambiguity",
        provenance=make_inferred_prov(["REQ-001"]),
    )
    miss = MissingInformation(
        id="MISS-001",
        description="Missing information",
        provenance=make_missing_prov(["REQ-001"]),
    )
    asm = Assumption(
        id="ASM-001",
        description="Assumption",
        provenance=make_assumption_prov(["REQ-001"]),
    )

    # 1. Proposed AC referencing existing AMB-001 (invalid prefix)
    ac_invalid_amb = AcceptanceCriterion(
        id="AC-001",
        description="AC",
        provenance=make_proposed_prov(["AMB-001"]),
    )
    analysis_ac_amb = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        acceptance_criteria=[ac_invalid_amb],
        ambiguities=[amb],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_ac_amb)
    assert "invalid dependency type" in str(exc_info.value)

    # 2. Proposed AC referencing existing MISS-001 (invalid prefix)
    ac_invalid_miss = AcceptanceCriterion(
        id="AC-001",
        description="AC",
        provenance=make_proposed_prov(["MISS-001"]),
    )
    analysis_ac_miss = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        acceptance_criteria=[ac_invalid_miss],
        missing_information=[miss],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_ac_miss)
    assert "invalid dependency type" in str(exc_info.value)

    # 3. Ambiguity referencing existing MISS-001 (invalid prefix)
    amb_invalid_miss = Ambiguity(
        id="AMB-002",
        description="Amb",
        provenance=make_inferred_prov(["MISS-001"]),
    )
    analysis_amb_miss = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        ambiguities=[amb, amb_invalid_miss],
        missing_information=[miss],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_amb_miss)
    assert "invalid dependency type" in str(exc_info.value)

    # 4. Ambiguity referencing existing ASM-001 (invalid prefix)
    amb_invalid_asm = Ambiguity(
        id="AMB-002",
        description="Amb",
        provenance=make_inferred_prov(["ASM-001"]),
    )
    analysis_amb_asm = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        ambiguities=[amb, amb_invalid_asm],
        assumptions=[asm],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_amb_asm)
    assert "invalid dependency type" in str(exc_info.value)

    # 5. MissingInformation referencing existing AMB-001 (invalid prefix)
    miss_invalid_amb = MissingInformation(
        id="MISS-002",
        description="Miss",
        provenance=make_missing_prov(["AMB-001"]),
    )
    analysis_miss_amb = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        ambiguities=[amb],
        missing_information=[miss, miss_invalid_amb],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_miss_amb)
    assert "invalid dependency type" in str(exc_info.value)

    # 6. MissingInformation referencing existing ASM-001 (invalid prefix)
    miss_invalid_asm = MissingInformation(
        id="MISS-002",
        description="Miss",
        provenance=make_missing_prov(["ASM-001"]),
    )
    analysis_miss_asm = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        missing_information=[miss, miss_invalid_asm],
        assumptions=[asm],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_miss_asm)
    assert "invalid dependency type" in str(exc_info.value)


def test_duplicate_ids_rejected() -> None:
    prov_ext = make_extracted_prov()
    prov_prop = make_proposed_prov(["REQ-001"])
    prov_inf = make_inferred_prov(["REQ-001"])
    prov_miss = make_missing_prov(["REQ-001"])
    prov_asm = make_assumption_prov(["REQ-001"])

    # 1. Duplicate requirements
    req = Requirement(
        id="REQ-001",
        description="desc",
        category=RequirementCategoryEnum.FUNCTIONAL,
        provenance=prov_ext,
    )
    analysis_req = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req, req],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_req)
    assert "Duplicate ID found in requirements" in str(exc_info.value)

    # 2. Duplicate acceptance_criteria
    ac = AcceptanceCriterion(
        id="AC-001",
        description="desc",
        provenance=prov_prop,
    )
    analysis_ac = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        acceptance_criteria=[ac, ac],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_ac)
    assert "Duplicate ID found in acceptance_criteria" in str(exc_info.value)

    # 3. Duplicate business_rules
    br = BusinessRule(
        id="BR-001",
        description="desc",
        provenance=prov_ext,
    )
    analysis_br = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        business_rules=[br, br],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_br)
    assert "Duplicate ID found in business_rules" in str(exc_info.value)

    # 4. Duplicate ambiguities
    amb = Ambiguity(
        id="AMB-001",
        description="desc",
        provenance=prov_inf,
    )
    analysis_amb = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        ambiguities=[amb, amb],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_amb)
    assert "Duplicate ID found in ambiguities" in str(exc_info.value)

    # 5. Duplicate missing_information
    miss = MissingInformation(
        id="MISS-001",
        description="desc",
        provenance=prov_miss,
    )
    analysis_miss = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        missing_information=[miss, miss],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_miss)
    assert "Duplicate ID found in missing_information" in str(exc_info.value)

    # 6. Duplicate assumptions
    asm = Assumption(
        id="ASM-001",
        description="desc",
        provenance=prov_asm,
    )
    analysis_asm = RequirementAnalysis(
        summary=make_summary(),
        requirements=[req],
        assumptions=[asm, asm],
    )
    with pytest.raises(ValueError) as exc_info:
        validate_requirement_analysis(analysis_asm)
    assert "Duplicate ID found in assumptions" in str(exc_info.value)



def test_import_isolation() -> None:
    import sys
    assert "app.agent" not in sys.modules
    assert "google.auth" not in sys.modules
    assert "google.adk" not in sys.modules
    assert "google.genai" not in sys.modules
