# Minimal Entity Contracts

Status: approved for the narrow three-agent MVP. No future or stretch schemas are included.

## Common IDs

Domain IDs match:

`^(SEG|REQ|AC|BR|AMB|MISS|ASM|RISK|TC|AUTO|REV)-[0-9]{3}$`

Safety IDs match `^(RED|SIG)-[0-9]{3}$` and are not domain dependencies.

All ID arrays reject duplicates. Segment order is continuous from `1..N`.

## Provenance

Fields:

- `origin`: `EXTRACTED`, `INFERRED`, `PROPOSED`, `ASSUMPTION`, or `MISSING_INFORMATION`;
- `transformation`: `VERBATIM`, `PARAPHRASE`, `SUMMARY`, or `NONE`;
- `source_segment_ids`;
- `derived_from_ids`;
- `rationale`, null for extracted content and 1–1000 characters otherwise.

Extracted content references sanitized segments. `VERBATIM` is an exact non-empty substring of one sanitized segment. For `origin = EXTRACTED`, `derived_from_ids` must be empty. Entity-specific domain relationships are stored in dedicated relationship fields and do not change provenance origin. Non-extracted content uses `NONE`, has no source segments, and references at least one allowed dependency.

These are canonical provenance rules. Agent draft schemas omit provenance fields whose values are fixed by entity type or computed from validated references; the deterministic enrichment layer adds them before canonical validation.

## RequirementAnalysis

`requirement-analysis/1.0.0` contains:

- one extracted summary;
- 1–8 extracted requirements;
- 0–20 extracted or proposed acceptance criteria;
- 0–12 extracted business rules;
- 0–10 inferred ambiguities;
- 0–12 missing-information items;
- 0–8 assumptions.

An extracted requirement has category `FUNCTIONAL`, `NON_FUNCTIONAL`, `CONSTRAINT`, or `UNKNOWN`. Proposed acceptance criteria remain visibly separate from extracted criteria. Business rules cannot be proposed as facts.

## RiskAnalysis

`risk-analysis/1.0.0` contains 0–10 inferred risks.

Risk fields:

- `id`, title, description, and test focus;
- category: `FUNCTIONAL`, `BOUNDARY`, `NEGATIVE`, `SECURITY`, `DATA_VALIDATION`, or `INTEGRATION`;
- severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`;
- likelihood: `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`;
- inferred provenance referencing allowed requirement-analysis entities.

Security risks concern the described product feature, not the AI pipeline.

## TestDesign Model Output

`test-design/1.0.0` contains 0–12 test-case drafts and optional blocking `MISS` IDs. An empty test list requires at least one blocking missing-information ID.

Each test-case draft returns:

- `id`, title, type, and priority;
- 0–10 preconditions;
- 1–10 continuously ordered actions;
- one expected-result string;
- `oracle_refs`: at least one `REQ`, `AC`, `BR`, or `ASM`;
- optional `risk_refs` containing only `RISK` IDs;
- `traceability_reason`, required only when all oracle references are general `REQ` IDs;
- `rationale` of 1–1000 characters.

Test types are `POSITIVE`, `NEGATIVE`, `BOUNDARY`, `SECURITY`, `VALIDATION`, and `INTEGRATION`. Priorities are `P0` through `P3`.

The model does not return canonical provenance, `derived_from_ids`, `assumption_ids`, `expected_result_status`, or `conditional` for test cases.

## TestDesign Deterministic Enrichment

Trusted code computes:

1. Canonical provenance with `origin = PROPOSED`, `transformation = NONE`, no source segments, the draft rationale, and `derived_from_ids = unique(oracle_refs + risk_refs)`.
2. All reachable assumptions through the acyclic type matrix.
3. Whether any reachable acceptance criterion is proposed.
4. `expected_result_status`:
   - `ASSUMED` when any assumption is reachable;
   - otherwise `PROPOSED` when any proposed AC is reachable;
   - otherwise `CONFIRMED` when the oracle is grounded only in extracted `REQ`, `AC`, or `BR` entities.
5. `conditional = expected_result_status != CONFIRMED`.

The canonical `assumption_ids` must equal the complete reachable assumption set. Recommended behavior must first exist as a proposed AC; it cannot appear as an unreferenced expected result.

## AutomationPlan

`automation-plan/1.0.0` contains:

- requirement type: `UI`, `API`, `HYBRID`, `AMBIGUOUS`, or `INSUFFICIENT_INFORMATION`;
- classification rationale;
- 0–8 automation candidates.

Each candidate returns:

- `AUTO-NNN` ID;
- exactly one existing `test_case_id`;
- optional additional `REQ`, `AC`, and `RISK` references;
- recommendation: `AUTOMATE`, `KEEP_MANUAL`, or `DEFER`;
- priority: `HIGH`, `MEDIUM`, or `LOW`;
- rationale of 1–500 characters.

The model does not return canonical provenance for an automation candidate. Trusted code creates it with `origin = PROPOSED`, `transformation = NONE`, no source segments, the candidate rationale, and `derived_from_ids = unique([test_case_id] + additional_refs)`.

Rules:

- conditional tests must use `DEFER`;
- `AMBIGUOUS` and `INSUFFICIENT_INFORMATION` plans cannot use `AUTOMATE`;
- `KEEP_MANUAL` means deliberate human execution is more suitable;
- `DEFER` means information is insufficient or the test is conditional;
- one test case has at most one automation candidate;
- no automation code or skeleton field exists in the mandatory MVP.

## Combined Risk & Test Design Output

`risk-test-design/1.0.0` atomically contains separate `risk_analysis`, `test_design`, and `automation_plan` sections. Failure of any section rejects the entire second-agent stage.

## QAReview Model Output

`qa-review/1.0.0` contains:

- verdict: `READY_FOR_HUMAN_REVIEW`, `NEEDS_CLARIFICATION`, or `NEEDS_REVISION`;
- confidence: `HIGH`, `MEDIUM`, or `LOW`;
- confidence rationale;
- 0–10 inferred findings.

Finding categories are `GAP`, `CONTRADICTION`, `UNSUPPORTED_CLAIM`, `TRACEABILITY`, `TEST_COVERAGE`, `AUTOMATION_READINESS`, and `SAFETY`. Severity is `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.

Findings may reference only `REQ`, `AC`, `BR`, `AMB`, `MISS`, `ASM`, `RISK`, `TC`, and `AUTO`. They cannot reference `REV`, `SEG`, `RED`, or `SIG`.

`NEEDS_REVISION` represents semantic coverage, grounding, or traceability defects. Invalid structure never reaches QA Review because schema validation stops it earlier.

Trusted code adds `human_review_required = true` to canonical JSON.
