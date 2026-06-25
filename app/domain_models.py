from enum import Enum
from typing import Annotated, Generic, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

DomainId = Annotated[
    str,
    StringConstraints(
        pattern=r"^(SEG|REQ|AC|BR|AMB|MISS|ASM|RISK|TC|AUTO|REV)-[0-9]{3}$"
    ),
]
SafetyId = Annotated[
    str,
    StringConstraints(pattern=r"^(RED|SIG)-[0-9]{3}$"),
]
SegmentId = Annotated[str, StringConstraints(pattern=r"^SEG-[0-9]{3}$")]
Rationale = Annotated[str, StringConstraints(min_length=1, max_length=1000)]


class OriginEnum(str, Enum):
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    PROPOSED = "PROPOSED"
    ASSUMPTION = "ASSUMPTION"
    MISSING_INFORMATION = "MISSING_INFORMATION"


class TransformationEnum(str, Enum):
    VERBATIM = "VERBATIM"
    PARAPHRASE = "PARAPHRASE"
    SUMMARY = "SUMMARY"
    NONE = "NONE"


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: OriginEnum
    transformation: TransformationEnum
    source_segment_ids: list[SegmentId] = Field(max_length=64)
    derived_from_ids: list[DomainId] = Field(max_length=10)
    rationale: Rationale | None

    @field_validator("source_segment_ids", "derived_from_ids")
    @classmethod
    def reject_duplicate_ids(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate IDs are not allowed")
        return value

    @model_validator(mode="after")
    def validate_provenance_invariants(self) -> "Provenance":
        if self.origin == OriginEnum.EXTRACTED:
            if self.transformation not in (
                TransformationEnum.VERBATIM,
                TransformationEnum.PARAPHRASE,
                TransformationEnum.SUMMARY,
            ):
                raise ValueError(
                    "EXTRACTED origin requires VERBATIM, PARAPHRASE, or "
                    "SUMMARY transformation"
                )
            if not self.source_segment_ids:
                raise ValueError(
                    "EXTRACTED origin requires non-empty source_segment_ids"
                )
            if self.derived_from_ids:
                raise ValueError(
                    "EXTRACTED origin requires derived_from_ids to be empty"
                )
            if self.rationale is not None:
                raise ValueError("EXTRACTED origin must not have a rationale")
        else:
            if self.transformation != TransformationEnum.NONE:
                raise ValueError(
                    f"{self.origin.value} origin requires NONE transformation"
                )
            if self.source_segment_ids:
                raise ValueError(
                    f"{self.origin.value} origin requires empty source_segment_ids"
                )
            if not self.derived_from_ids:
                raise ValueError(
                    f"{self.origin.value} origin requires non-empty derived_from_ids"
                )
            if self.rationale is None:
                raise ValueError(
                    f"{self.origin.value} origin requires a non-null rationale"
                )

        return self


# Specialized ID Types
RequirementId = Annotated[str, StringConstraints(pattern=r"^REQ-[0-9]{3}$")]
ACId = Annotated[str, StringConstraints(pattern=r"^AC-[0-9]{3}$")]
BRId = Annotated[str, StringConstraints(pattern=r"^BR-[0-9]{3}$")]
AMBId = Annotated[str, StringConstraints(pattern=r"^AMB-[0-9]{3}$")]
MISSId = Annotated[str, StringConstraints(pattern=r"^MISS-[0-9]{3}$")]
ASMId = Annotated[str, StringConstraints(pattern=r"^ASM-[0-9]{3}$")]


class RequirementCategoryEnum(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    CONSTRAINT = "CONSTRAINT"
    UNKNOWN = "UNKNOWN"


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: RequirementId
    description: Annotated[str, StringConstraints(max_length=4000)]
    category: RequirementCategoryEnum
    provenance: Provenance

    @model_validator(mode="after")
    def validate_requirement_origin(self) -> "Requirement":
        if self.provenance.origin != OriginEnum.EXTRACTED:
            raise ValueError("Requirement provenance origin must be EXTRACTED")
        return self


class AcceptanceCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: ACId
    description: Annotated[str, StringConstraints(max_length=4000)]
    provenance: Provenance

    @model_validator(mode="after")
    def validate_ac_origin(self) -> "AcceptanceCriterion":
        if self.provenance.origin not in (OriginEnum.EXTRACTED, OriginEnum.PROPOSED):
            raise ValueError(
                "AcceptanceCriterion provenance origin must be EXTRACTED or "
                "PROPOSED"
            )
        return self


class BusinessRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: BRId
    description: Annotated[str, StringConstraints(max_length=4000)]
    provenance: Provenance

    @model_validator(mode="after")
    def validate_br_origin(self) -> "BusinessRule":
        if self.provenance.origin != OriginEnum.EXTRACTED:
            raise ValueError("BusinessRule provenance origin must be EXTRACTED")
        return self


class Ambiguity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: AMBId
    description: Annotated[str, StringConstraints(max_length=4000)]
    provenance: Provenance

    @model_validator(mode="after")
    def validate_amb_origin(self) -> "Ambiguity":
        if self.provenance.origin != OriginEnum.INFERRED:
            raise ValueError("Ambiguity provenance origin must be INFERRED")
        return self


class MissingInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: MISSId
    description: Annotated[str, StringConstraints(max_length=4000)]
    provenance: Provenance

    @model_validator(mode="after")
    def validate_miss_origin(self) -> "MissingInformation":
        if self.provenance.origin != OriginEnum.MISSING_INFORMATION:
            raise ValueError(
                "MissingInformation provenance origin must be "
                "MISSING_INFORMATION"
            )
        return self


class Assumption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: ASMId
    description: Annotated[str, StringConstraints(max_length=4000)]
    provenance: Provenance

    @model_validator(mode="after")
    def validate_asm_origin(self) -> "Assumption":
        if self.provenance.origin != OriginEnum.ASSUMPTION:
            raise ValueError(
                "Assumption provenance origin must be ASSUMPTION"
            )
        return self


class ExtractedSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: Annotated[str, StringConstraints(max_length=4000)]
    provenance: Provenance

    @model_validator(mode="after")
    def validate_summary_origin(self) -> "ExtractedSummary":
        if self.provenance.origin != OriginEnum.EXTRACTED:
            raise ValueError(
                "ExtractedSummary provenance origin must be EXTRACTED"
            )
        return self


class RequirementAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ExtractedSummary
    requirements: list[Requirement] = Field(min_length=1, max_length=8)
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        default_factory=list, max_length=20
    )
    business_rules: list[BusinessRule] = Field(
        default_factory=list, max_length=12
    )
    ambiguities: list[Ambiguity] = Field(
        default_factory=list, max_length=10
    )
    missing_information: list[MissingInformation] = Field(
        default_factory=list, max_length=12
    )
    assumptions: list[Assumption] = Field(
        default_factory=list, max_length=8
    )


T = TypeVar("T")


class StageStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class StageResult(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    status: StageStatus
    committed_output: T | None = None
    error_code: str | None = None
    safe_message: str | None = None

    @model_validator(mode="after")
    def validate_state_invariants(self) -> "StageResult[T]":
        if self.status == StageStatus.SUCCESS:
            if self.committed_output is None:
                raise ValueError("SUCCESS status requires committed_output")
            if self.error_code is not None:
                raise ValueError("SUCCESS status must not have error_code")
            if self.safe_message is not None:
                raise ValueError("SUCCESS status must not have safe_message")
        elif self.status == StageStatus.FAILED:
            if self.committed_output is not None:
                raise ValueError("FAILED status must not have committed_output")
            if self.error_code is None:
                raise ValueError("FAILED status requires error_code")
            if self.safe_message is None:
                raise ValueError("FAILED status requires safe_message")
        elif self.status == StageStatus.NOT_STARTED:
            if self.committed_output is not None:
                raise ValueError("NOT_STARTED status must not have committed_output")
            if self.error_code is not None:
                raise ValueError("NOT_STARTED status must not have error_code")
            if self.safe_message is not None:
                raise ValueError("NOT_STARTED status must not have safe_message")
        elif self.status == StageStatus.SKIPPED:
            if self.committed_output is not None:
                raise ValueError("SKIPPED status must not have committed_output")
        return self


class SafetyFlag(str, Enum):
    SECRET_REDACTED = "SECRET_REDACTED"
    URL_DETECTED = "URL_DETECTED"
    INJECTION_SUSPECTED = "INJECTION_SUSPECTED"
    UNSAFE_ACTION_REQUEST = "UNSAFE_ACTION_REQUEST"


class SafetyEventKind(str, Enum):
    REDACTION = "REDACTION"
    SIGNAL = "SIGNAL"


class SafetyEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: SafetyId
    kind: SafetyEventKind
    safe_label: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    segment_id: SegmentId | None = None

    @model_validator(mode="after")
    def validate_safety_id_kind_alignment(self) -> "SafetyEvent":
        if self.kind == SafetyEventKind.REDACTION and not self.id.startswith("RED-"):
            raise ValueError("REDACTION safety event must use RED-NNN ID format")
        if self.kind == SafetyEventKind.SIGNAL and not self.id.startswith("SIG-"):
            raise ValueError("SIGNAL safety event must use SIG-NNN ID format")
        return self


class SanitizedSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: SegmentId
    order: Annotated[int, Field(ge=1)]
    text: Annotated[str, StringConstraints(max_length=2000)]
    safety_flags: list[SafetyFlag] = Field(default_factory=list)
    safety_event_ids: list[SafetyId] = Field(default_factory=list)

    @field_validator("safety_flags", "safety_event_ids")
    @classmethod
    def reject_duplicates(cls, values: list) -> list:
        if len(values) != len(set(values)):
            raise ValueError("Duplicate values are not allowed")
        return values


class SanitizedInputEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segments: list[SanitizedSegment] = Field(min_length=1, max_length=64)
    safety_events: list[SafetyEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_envelope_invariants(self) -> "SanitizedInputEnvelope":
        # 1. Segment order continuity: must start at 1 and be contiguous
        sorted_segments = sorted(self.segments, key=lambda s: s.order)
        for idx, segment in enumerate(sorted_segments):
            expected_order = idx + 1
            if segment.order != expected_order:
                raise ValueError(
                    f"Segment order must be contiguous 1..N. "
                    f"Expected order {expected_order}, got {segment.order}."
                )

        # 2. Unique Segment IDs
        segment_ids = [s.id for s in self.segments]
        if len(segment_ids) != len(set(segment_ids)):
            raise ValueError("Segment IDs must be unique")

        # 3. Unique Safety Event IDs
        event_ids = [e.id for e in self.safety_events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("Safety Event IDs must be unique")

        # 4. Referential Integrity: safety_event_ids on segments must point to defined events
        event_map = {e.id: e for e in self.safety_events}
        for segment in self.segments:
            for ev_id in segment.safety_event_ids:
                if ev_id not in event_map:
                    raise ValueError(
                        f"Referenced safety event ID {ev_id} not found in safety_events"
                    )
                # Check segment ID mapping matches
                event = event_map[ev_id]
                if event.segment_id != segment.id:
                    raise ValueError(
                        f"Safety event {ev_id} references segment {event.segment_id}, "
                        f"but is attached to segment {segment.id}"
                    )

        # 5. Safety event bidirectional mapping validation
        segment_map = {s.id: s for s in self.segments}
        for event in self.safety_events:
            if event.segment_id is None:
                raise ValueError(f"Safety event {event.id} must have segment_id")
            if event.segment_id not in segment_map:
                raise ValueError(
                    f"Safety event {event.id} references non-existent segment {event.segment_id}"
                )
            segment = segment_map[event.segment_id]
            if event.id not in segment.safety_event_ids:
                raise ValueError(
                    f"Safety event {event.id} is not listed in segment {segment.id}'s safety_event_ids"
                )

        return self
