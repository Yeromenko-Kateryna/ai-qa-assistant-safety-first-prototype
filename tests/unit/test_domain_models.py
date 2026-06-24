import pytest
from pydantic import TypeAdapter, ValidationError

from app.domain_models import (
    DomainId,
    OriginEnum,
    Provenance,
    SafetyId,
    SegmentId,
    TransformationEnum,
)


def assert_validation_error(
    error: ValidationError,
    *,
    error_type: str,
    location: tuple[str | int, ...],
) -> None:
    assert any(
        item["type"] == error_type and item["loc"] == location
        for item in error.errors(include_url=False)
    )


def extracted_provenance_data() -> dict[str, object]:
    return {
        "origin": OriginEnum.EXTRACTED,
        "transformation": TransformationEnum.VERBATIM,
        "source_segment_ids": ["SEG-001"],
        "derived_from_ids": [],
        "rationale": None,
    }


def test_domain_id_validation() -> None:
    adapter = TypeAdapter(DomainId)
    valid_prefixes = [
        "SEG",
        "REQ",
        "AC",
        "BR",
        "AMB",
        "MISS",
        "ASM",
        "RISK",
        "TC",
        "AUTO",
        "REV",
    ]

    for prefix in valid_prefixes:
        assert adapter.validate_python(f"{prefix}-001") == f"{prefix}-001"
        assert adapter.validate_python(f"{prefix}-999") == f"{prefix}-999"

    invalid_ids = [
        "RED-001",
        "SIG-100",
        "ABC-123",
        "REQ-12",
        "REQ-1234",
        "req-123",
        "REQ-abc",
        "",
    ]
    for invalid_id in invalid_ids:
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid_id)


def test_safety_id_validation() -> None:
    adapter = TypeAdapter(SafetyId)

    for prefix in ["RED", "SIG"]:
        assert adapter.validate_python(f"{prefix}-001") == f"{prefix}-001"
        assert adapter.validate_python(f"{prefix}-999") == f"{prefix}-999"

    invalid_ids = [
        "REQ-001",
        "SEG-100",
        "ABC-123",
        "RED-12",
        "RED-1234",
        "red-001",
        "RED-abc",
        "",
    ]
    for invalid_id in invalid_ids:
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid_id)


def test_segment_id_validation() -> None:
    adapter = TypeAdapter(SegmentId)

    for segment_id in ["SEG-000", "SEG-123", "SEG-999"]:
        assert adapter.validate_python(segment_id) == segment_id

    for invalid_id in ["REQ-001", "RED-100", "SEG-12", "SEG-1234", "seg-001", ""]:
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid_id)


def test_provenance_requires_all_fields() -> None:
    required_fields = {
        "origin",
        "transformation",
        "source_segment_ids",
        "derived_from_ids",
        "rationale",
    }
    schema = Provenance.model_json_schema()
    assert set(schema["required"]) == required_fields

    for field_name in required_fields:
        data = extracted_provenance_data()
        del data[field_name]
        with pytest.raises(ValidationError) as exc_info:
            Provenance.model_validate(data)
        assert_validation_error(
            exc_info.value,
            error_type="missing",
            location=(field_name,),
        )


def test_rationale_constraints_are_exposed_in_json_schema() -> None:
    schema = Provenance.model_json_schema()
    rationale_options = schema["properties"]["rationale"]["anyOf"]
    string_schema = next(
        option for option in rationale_options if option.get("type") == "string"
    )

    assert string_schema["minLength"] == 1
    assert string_schema["maxLength"] == 1000


def test_provenance_rejects_duplicate_ids() -> None:
    with pytest.raises(ValidationError) as source_error:
        Provenance(
            origin=OriginEnum.EXTRACTED,
            transformation=TransformationEnum.VERBATIM,
            source_segment_ids=["SEG-001", "SEG-001"],
            derived_from_ids=[],
            rationale=None,
        )
    assert_validation_error(
        source_error.value,
        error_type="value_error",
        location=("source_segment_ids",),
    )

    with pytest.raises(ValidationError) as dependency_error:
        Provenance(
            origin=OriginEnum.INFERRED,
            transformation=TransformationEnum.NONE,
            source_segment_ids=[],
            derived_from_ids=["REQ-001", "REQ-001"],
            rationale="Valid rationale",
        )
    assert_validation_error(
        dependency_error.value,
        error_type="value_error",
        location=("derived_from_ids",),
    )


def test_provenance_rejects_extra_fields() -> None:
    data = extracted_provenance_data()
    data["unexpected"] = "value"

    with pytest.raises(ValidationError) as exc_info:
        Provenance.model_validate(data)
    assert_validation_error(
        exc_info.value,
        error_type="extra_forbidden",
        location=("unexpected",),
    )


def test_provenance_rejects_invalid_enums() -> None:
    invalid_origin = extracted_provenance_data()
    invalid_origin["origin"] = "INVALID_ORIGIN"
    with pytest.raises(ValidationError) as origin_error:
        Provenance.model_validate(invalid_origin)
    assert_validation_error(
        origin_error.value,
        error_type="enum",
        location=("origin",),
    )

    invalid_transformation = extracted_provenance_data()
    invalid_transformation["transformation"] = "INVALID_TRANSFORMATION"
    with pytest.raises(ValidationError) as transformation_error:
        Provenance.model_validate(invalid_transformation)
    assert_validation_error(
        transformation_error.value,
        error_type="enum",
        location=("transformation",),
    )


def test_extracted_provenance_combinations() -> None:
    for transformation in [
        TransformationEnum.VERBATIM,
        TransformationEnum.PARAPHRASE,
        TransformationEnum.SUMMARY,
    ]:
        provenance = Provenance(
            origin=OriginEnum.EXTRACTED,
            transformation=transformation,
            source_segment_ids=["SEG-001", "SEG-002"],
            derived_from_ids=[],
            rationale=None,
        )
        assert provenance.transformation == transformation

    invalid_cases = [
        {
            **extracted_provenance_data(),
            "transformation": TransformationEnum.NONE,
        },
        {**extracted_provenance_data(), "source_segment_ids": []},
        {**extracted_provenance_data(), "derived_from_ids": ["REQ-001"]},
        {**extracted_provenance_data(), "rationale": "Not extracted"},
    ]
    for invalid_case in invalid_cases:
        with pytest.raises(ValidationError) as exc_info:
            Provenance.model_validate(invalid_case)
        assert_validation_error(
            exc_info.value,
            error_type="value_error",
            location=(),
        )


def test_non_extracted_provenance_combinations() -> None:
    origins = [
        OriginEnum.INFERRED,
        OriginEnum.PROPOSED,
        OriginEnum.ASSUMPTION,
        OriginEnum.MISSING_INFORMATION,
    ]

    for origin in origins:
        valid_data = {
            "origin": origin,
            "transformation": TransformationEnum.NONE,
            "source_segment_ids": [],
            "derived_from_ids": ["REQ-001"],
            "rationale": "Meaningful rationale",
        }
        assert Provenance.model_validate(valid_data).origin == origin

        invalid_cases = [
            {**valid_data, "transformation": TransformationEnum.VERBATIM},
            {**valid_data, "source_segment_ids": ["SEG-001"]},
            {**valid_data, "derived_from_ids": []},
            {**valid_data, "rationale": None},
        ]
        for invalid_case in invalid_cases:
            with pytest.raises(ValidationError) as exc_info:
                Provenance.model_validate(invalid_case)
            assert_validation_error(
                exc_info.value,
                error_type="value_error",
                location=(),
            )


def test_provenance_array_limits() -> None:
    Provenance(
        origin=OriginEnum.EXTRACTED,
        transformation=TransformationEnum.VERBATIM,
        source_segment_ids=[f"SEG-{index:03d}" for index in range(64)],
        derived_from_ids=[],
        rationale=None,
    )
    Provenance(
        origin=OriginEnum.INFERRED,
        transformation=TransformationEnum.NONE,
        source_segment_ids=[],
        derived_from_ids=[f"REQ-{index:03d}" for index in range(10)],
        rationale="Valid rationale",
    )

    with pytest.raises(ValidationError) as source_error:
        Provenance(
            origin=OriginEnum.EXTRACTED,
            transformation=TransformationEnum.VERBATIM,
            source_segment_ids=[f"SEG-{index:03d}" for index in range(65)],
            derived_from_ids=[],
            rationale=None,
        )
    assert_validation_error(
        source_error.value,
        error_type="too_long",
        location=("source_segment_ids",),
    )

    with pytest.raises(ValidationError) as dependency_error:
        Provenance(
            origin=OriginEnum.INFERRED,
            transformation=TransformationEnum.NONE,
            source_segment_ids=[],
            derived_from_ids=[f"REQ-{index:03d}" for index in range(11)],
            rationale="Valid rationale",
        )
    assert_validation_error(
        dependency_error.value,
        error_type="too_long",
        location=("derived_from_ids",),
    )


def test_rationale_boundary_constraints() -> None:
    for rationale in ["A", "A" * 1000]:
        provenance = Provenance(
            origin=OriginEnum.INFERRED,
            transformation=TransformationEnum.NONE,
            source_segment_ids=[],
            derived_from_ids=["REQ-001"],
            rationale=rationale,
        )
        assert provenance.rationale == rationale

    for rationale, error_type in [
        ("", "string_too_short"),
        ("A" * 1001, "string_too_long"),
    ]:
        with pytest.raises(ValidationError) as exc_info:
            Provenance(
                origin=OriginEnum.INFERRED,
                transformation=TransformationEnum.NONE,
                source_segment_ids=[],
                derived_from_ids=["REQ-001"],
                rationale=rationale,
            )
        assert_validation_error(
            exc_info.value,
            error_type=error_type,
            location=("rationale",),
        )
