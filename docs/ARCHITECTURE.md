# Target Architecture v1.0

> **Status: designed target architecture.** The complete live multi-agent workflow below is not implemented end to end. The currently runnable path is the offline synthetic mock demo described in [demo.md](demo.md); deterministic domain, validation, input-safety, provider-boundary, output-safety, and rendering components are implemented independently.

## Current Implemented Corridor

```text
Committed synthetic requirement data
  -> deterministic validation
  -> safe Markdown renderer
  -> output-safety check
  -> labelled mock CLI output
```

The input-safety and candidate-draft validation modules are unit-tested deterministic components. They are not connected to a supported live provider workflow.

## Target Trust-Aware Flow

```text
Raw HTTP Input
    |
    v
Pre-ADK Input Safety Gate
    |
    v
SanitizedInputEnvelope
    |
    v
Requirement Agent
    |
    v
Risk & Test Design Agent
    |  returns separate risk_analysis,
    |  test_design, and automation_plan
    |
    v
QA Review Agent
    |
    v
Deterministic Candidate Aggregator
    |
    v
Candidate JSON
    |
    v
Schema + Referential Validation
    |
    v
Output Safety Gate
    |
    +---- unsafe/invalid ----> SafeErrorEnvelope
    |
    v
Safe Canonical JSON
    |
    v
Final Schema Validation
    |
    v
Deterministic Markdown Renderer
```

## Key Properties

- Raw input never enters the ADK Runner or session state.
- Agents have no action-capable tools.
- Each stage output is atomic and validated before state commit.
- The aggregator is deterministic and consumes no model call.
- Expected-result status, conditional flags, full assumption references, and the constant human-review flag are deterministic enrichments rather than model-generated fields.
- Invalid candidate content and validator details are not logged or traced.
- Candidate, canonical, and safe-error documents have separate schemas.
- Final Markdown cannot add facts because it is a deterministic view of canonical JSON.

## Stage Failure Semantics

Stage states are `NOT_STARTED`, `SUCCESS`, `FAILED`, or `SKIPPED`.

An individual stage is atomic. Pipeline status may be `SUCCESS`, `PARTIAL`, or `FAILED`. A partial report includes only completed validated upstream results, is marked `INCOMPLETE`, and always fails release evaluation.

## ADK State Boundary

Only sanitized, invocation-scoped data may be stored under temporary state keys:

- `temp:sanitized_input`
- `temp:requirement_analysis`
- `temp:risk_test_design`
- `temp:qa_review`
- `temp:candidate_report`

The actual persistence and tracing semantics of the selected ADK version must be verified before implementation. The design does not assume that a prefix alone guarantees confidentiality.

## Safe Logging

Allowed metadata:

- correlation ID;
- stage name;
- safe error code;
- status;
- timing;
- token counts;
- schema and policy versions.

Forbidden content:

- raw request body;
- detected secret value;
- invalid model candidate;
- raw validator message;
- stack trace in user-facing output.
