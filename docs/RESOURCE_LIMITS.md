# Resource Limits v1.0

Status: provisional until an exact Gemini model is selected and representative usage is measured.

Policy version: `resource-policy/0.1`.

## Principles

- Limits are enforced without silent truncation.
- Aggregation and rendering are deterministic and consume no model calls.
- Actual API usage includes system instructions, JSON schemas, upstream outputs, all attempts, and retries.
- Global graph and output limits override per-entity limits.
- Any `PARTIAL` result may be shown safely but fails release evaluation.

## Input Limits

| Limit | Value |
|---|---:|
| HTTP request body | 32 KiB |
| Normalized requirement text | 12,000 Unicode code points |
| Local pre-model token estimate | 4,000 tokens |
| Sanitized segments | 64 |
| Characters per segment | 2,000 |

The provisional deterministic estimator is:

`estimated_tokens = ceil(UTF-8 byte length / 3)`

It runs locally before any model call and never logs input. Once a model is selected, a versioned local tokenizer may replace this conservative formula if it can run without sending data externally.

## Entity Limits

| Entity | Maximum |
|---|---:|
| Requirements | 8 |
| Acceptance criteria, extracted and proposed combined | 20 |
| Business rules | 12 |
| Ambiguities | 10 |
| Missing-information items | 12 |
| Assumptions | 8 |
| Risks | 30 |
| Test cases | 30 |
| Steps per test case | 10 |
| Automation candidates | 20 |
| QA review findings | 20 |
| Automation skeletons | 1 for unambiguous UI or API input |

## Provisional Model Budgets

| Stage | Maximum output tokens across its successful attempt |
|---|---:|
| Requirement Agent | 5,000 |
| Risk Agent | 4,000 |
| Test Design Agent | 7,000 |
| Automation Agent | 5,000 |
| QA Review Agent | 4,000 |

Successful-stage maximum: 25,000 output tokens.

Pipeline limits:

| Limit | Value |
|---|---:|
| Total actual input tokens across every attempt | 100,000 |
| Total actual output tokens across every attempt | 32,000 |
| Model calls | 6 |
| Retries | One global transient-error retry |

The 32,000-token global output limit covers the 25,000-token successful path plus one full retry of the largest 7,000-token stage. Aggregation does not use the sixth call.

Before each call, the controller estimates the projected request. After each call, it updates cumulative budgets using API usage metadata. If exact metadata is unavailable, the run is marked `ESTIMATED` and uses the versioned conservative local estimator.

No retry is allowed for safety, schema, provenance, language, graph, or resource-limit failures.

## Object Size Limits

| Object | Maximum |
|---|---:|
| Ordinary text field | 4,000 characters |
| Automation code skeleton | 12,000 characters |
| Candidate JSON | 256 KiB |
| Canonical JSON | 256 KiB |
| Rendered Markdown | 256 KiB |
| JSON nesting depth | 16 |

## Timeouts

| Operation | Hard timeout |
|---|---:|
| Pre-ADK Input Safety Gate | 2 seconds |
| Individual model stage | 60 seconds |
| Schema and graph validation | 2 seconds |
| Output Safety Gate | 2 seconds |
| Whole pipeline, including retry | 240 seconds |

## Dependency Graph Limits

| Limit | Value |
|---|---:|
| Nodes | 300 |
| Edges | 900 |
| Maximum depth | 8 |
| `derived_from_ids` per entity | 10 |
| Traceability references per test case | 10 |

Cycles, self-references, unknown IDs, and invalid downstream references are forbidden.

## Limit Priority

1. HTTP and whole-input limits
2. Total model-call and token budgets
3. Candidate, canonical, Markdown, and graph limits
4. Per-stage output limits
5. Per-entity limits

Passing a lower-level limit never overrides a violated higher-level limit.

## Safe Error Codes

- `INPUT_RESOURCE_LIMIT_EXCEEDED`
- `TOO_MANY_SEGMENTS`
- `MODEL_CALL_BUDGET_EXCEEDED`
- `MODEL_TOKEN_BUDGET_EXCEEDED`
- `STAGE_OUTPUT_TOO_LARGE`
- `STAGE_ENTITY_LIMIT_EXCEEDED`
- `STAGE_TIMEOUT`
- `PIPELINE_TIMEOUT`
- `DEPENDENCY_GRAPH_LIMIT_EXCEEDED`

## Calibration Gate

Before implementation limits are declared stable:

1. Select the exact model version.
2. Run representative UI, API, incomplete, and injection scenarios.
3. Record actual prompt, schema, upstream-state, output, retry, latency, and object-size usage.
4. Adjust budgets once using measured headroom.
5. Increment `resource_policy_version` and document the reason.
