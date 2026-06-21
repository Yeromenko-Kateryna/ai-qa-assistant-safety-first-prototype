# Data Contract Boundaries

Status: trust boundaries and provenance model approved; detailed entity schemas remain to be designed.

## Contract Types

| Contract | Trust level | User-visible |
|---|---|---|
| `RawAnalyzeRequest` | Untrusted and ephemeral | No |
| `SanitizedInputEnvelope` | Sanitized and validated | Yes |
| `StageResult<T>` | Valid only after atomic stage validation | Not directly |
| `CandidateReport` | Structurally assembled but untrusted | No |
| `CanonicalReport` | Validated and output-safe | Yes |
| `SafeErrorEnvelope` | Trusted safe failure schema | Yes |
| `RenderedMarkdown` | Deterministic canonical view | Yes |

## Provenance

`origin` identifies where knowledge came from:

- `EXTRACTED`
- `PROPOSED`
- `ASSUMPTION`
- `MISSING_INFORMATION`

`transformation` identifies presentation form:

- `VERBATIM`
- `PARAPHRASE`
- `SUMMARY`
- `NONE`

Rules:

- `EXTRACTED` uses `VERBATIM`, `PARAPHRASE`, or `SUMMARY` and references at least one sanitized source segment.
- `VERBATIM` means exact content from a sanitized segment, never raw input.
- `PROPOSED`, `ASSUMPTION`, and `MISSING_INFORMATION` use `NONE`.
- `MISSING_INFORMATION.source_segment_ids` may be empty.
- Proposed and assumed items may reference upstream entities through `derived_from_ids` without becoming extracted facts.
- Missing, unknown, cyclic, self, and invalid downstream dependencies are rejected.

## Traceability

Traceability is contextual rather than a fixed global hierarchy.

- A test of an acceptance criterion references `ac_id`.
- A test of a business rule references `business_rule_id`.
- A test of a risk may directly reference `risk_id`.
- Multiple relevant references are allowed.
- `requirement_id` is a fallback only when no more specific relevant object exists.
- A fallback requires a non-empty `traceability_reason`.

## Atomic Stage Contract

A stage output is committed only after structural and semantic validation. Invalid output is discarded, the stage becomes `FAILED`, and dependent downstream stages become `SKIPPED`.

The deterministic aggregator combines only committed stage results and never calls a model.

## Output Boundary

```text
Committed Stage Outputs
  -> CandidateReport
  -> Schema and Referential Validation
  -> Output Safety Gate
  -> CanonicalReport or SafeErrorEnvelope
  -> Final Schema Validation
  -> Deterministic Markdown
```

Invalid candidates and raw validator messages never enter logs, traces, safe errors, or rendered output.
