from enum import Enum
from typing import Annotated

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
