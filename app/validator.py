from app.domain_models import OriginEnum, RequirementAnalysis


def validate_requirement_analysis(analysis: RequirementAnalysis) -> None:
    """Validates unique IDs and reference contracts for RequirementAnalysis."""
    # 1. Duplicate IDs check
    req_ids = [r.id for r in analysis.requirements]
    if len(req_ids) != len(set(req_ids)):
        raise ValueError("Duplicate ID found in requirements")

    ac_ids = [ac.id for ac in analysis.acceptance_criteria]
    if len(ac_ids) != len(set(ac_ids)):
        raise ValueError("Duplicate ID found in acceptance_criteria")

    br_ids = [br.id for br in analysis.business_rules]
    if len(br_ids) != len(set(br_ids)):
        raise ValueError("Duplicate ID found in business_rules")

    amb_ids = [amb.id for amb in analysis.ambiguities]
    if len(amb_ids) != len(set(amb_ids)):
        raise ValueError("Duplicate ID found in ambiguities")

    miss_ids = [miss.id for miss in analysis.missing_information]
    if len(miss_ids) != len(set(miss_ids)):
        raise ValueError("Duplicate ID found in missing_information")

    asm_ids = [asm.id for asm in analysis.assumptions]
    if len(asm_ids) != len(set(asm_ids)):
        raise ValueError("Duplicate ID found in assumptions")

    # 2. Referential integrity and Dependency Matrix check
    valid_ids = set()
    valid_ids.update(req_ids)
    valid_ids.update(ac_ids)
    valid_ids.update(br_ids)
    valid_ids.update(amb_ids)
    valid_ids.update(miss_ids)
    valid_ids.update(asm_ids)

    # Validate proposed acceptance criteria
    for ac in analysis.acceptance_criteria:
        if ac.provenance.origin == OriginEnum.PROPOSED:
            for dep_id in ac.provenance.derived_from_ids:
                prefix = dep_id.split("-", 1)[0]
                if prefix not in {"REQ", "BR"}:
                    raise ValueError(
                        f"Proposed AC {ac.id} has invalid dependency type {dep_id}"
                    )
                if dep_id not in valid_ids:
                    raise ValueError(
                        f"Proposed AC {ac.id} references missing dependency {dep_id}"
                    )

    # Validate ambiguities
    for amb in analysis.ambiguities:
        for dep_id in amb.provenance.derived_from_ids:
            prefix = dep_id.split("-", 1)[0]
            if prefix not in {"REQ", "AC", "BR"}:
                raise ValueError(
                    f"Ambiguity {amb.id} has invalid dependency type {dep_id}"
                )
            if dep_id not in valid_ids:
                raise ValueError(
                    f"Ambiguity {amb.id} references missing dependency {dep_id}"
                )

    # Validate missing information
    for miss in analysis.missing_information:
        for dep_id in miss.provenance.derived_from_ids:
            prefix = dep_id.split("-", 1)[0]
            if prefix not in {"REQ", "AC", "BR"}:
                raise ValueError(
                    f"MissingInformation {miss.id} has invalid dependency type {dep_id}"
                )
            if dep_id not in valid_ids:
                raise ValueError(
                    f"MissingInformation {miss.id} references missing dependency {dep_id}"
                )

    # Validate assumptions
    for asm in analysis.assumptions:
        for dep_id in asm.provenance.derived_from_ids:
            prefix = dep_id.split("-", 1)[0]
            if prefix not in {"REQ", "AC", "BR", "AMB", "MISS"}:
                raise ValueError(
                    f"Assumption {asm.id} has invalid dependency type {dep_id}"
                )
            if dep_id not in valid_ids:
                raise ValueError(
                    f"Assumption {asm.id} references missing dependency {dep_id}"
                )
