# Data Contract Boundaries

Status: trust boundaries, minimal provenance, and narrow-MVP entity contracts approved.

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
- `INFERRED`
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
- `VERBATIM` means an exact non-empty substring of one sanitized segment, never raw input.
- `INFERRED`, `PROPOSED`, `ASSUMPTION`, and `MISSING_INFORMATION` use `NONE`, have no source-segment references, reference at least one allowed dependency, and include a rationale.
- `MISSING_INFORMATION.source_segment_ids` may be empty.
- Proposed and assumed items may reference upstream entities through `derived_from_ids` without becoming extracted facts.
- Unknown, duplicate, self, and type-invalid dependencies are rejected.

Safety references use separate `RED-NNN` and `SIG-NNN` namespaces. They belong to `SanitizedInputEnvelope` and are not dependency-graph nodes.

## Traceability

Traceability is contextual rather than a fixed global hierarchy.

- A test of an acceptance criterion references `ac_id`.
- A test of a business rule references `business_rule_id`.
- A test of a risk may directly reference `risk_id`.
- Multiple relevant references are allowed.
- `requirement_id` is a fallback only when no more specific relevant object exists.
- A fallback requires a non-empty `traceability_reason`.

The deterministic validator requires the reason but does not attempt to judge whether a semantically better AC or business rule exists. That judgment belongs to QA Review.

## Minimal Type Reference Matrix

| Entity | Allowed dependencies |
|---|---|
| Proposed `AC` | `REQ`, `BR` |
| `AMB` | `REQ`, `AC`, `BR` |
| `MISS` | `REQ`, `AC`, `BR` |
| `ASM` | `REQ`, `AC`, `BR`, `AMB`, `MISS` |
| `RISK` | `REQ`, `AC`, `BR`, `AMB`, `MISS`, `ASM` |
| `TC` | `REQ`, `AC`, `BR`, `RISK`, `ASM` |
| `AUTO` | one mandatory `TC`; optional `REQ`, `AC`, `RISK` |
| `REV` | `REQ`, `AC`, `BR`, `AMB`, `MISS`, `ASM`, `RISK`, `TC`, `AUTO` |

The matrix is acyclic by construction. No universal cycle-search algorithm is required for MVP.

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

## Deterministic Enrichment

Gemini returns variable content, source/reference arrays, and rationale. Draft schemas may omit canonical fields whose values are fixed or derivable. Trusted code constructs the complete canonical provenance and computes:

- `TestCase.provenance.derived_from_ids = unique(oracle_refs + risk_refs)`;
- complete direct and indirect `assumption_ids`;
- `expected_result_status` with precedence `ASSUMED > PROPOSED > CONFIRMED`;
- `conditional = expected_result_status != CONFIRMED`;
- `AutomationCandidate.provenance.derived_from_ids = unique([test_case_id] + additional_refs)`;
- `QAReview.human_review_required = true`.

These computed fields appear in canonical JSON but are not requested from the model.
