# AI QA Assistant — Safety-First Requirements Analysis Prototype

An R&D prototype exploring how unstructured English product requirements can be turned into a structured QA draft without allowing untrusted input or model-derived content to bypass deterministic controls.

## Project Status

**Current demonstrable version:** an offline, synthetic mock demo of the safe requirement-analysis report format.

The deterministic core is implemented and covered by unit tests. An experimental one-shot Gemini execution path exists for the Requirement Agent boundary, but it is not part of the supported portfolio demo and no reproducible live-run evidence is committed. End-to-end multi-agent orchestration, service deployment, and semantic LLM evaluation remain target work.

## What Is Implemented

- Pydantic domain models for requirements, provenance, stage status, and safe errors.
- Deterministic structural and referential validation.
- Input-safety checks for language, size, secret-like values, URLs, and suspicious instruction patterns.
- A deterministic requirement-analysis stage and safe handling of invalid candidate drafts.
- Output checks and a deterministic Markdown renderer that omits internal IDs, provenance, rationales, raw payloads, and diagnostics.
- Provider and SDK-adapter boundaries with lazy SDK import, plus experimental one-shot Requirement Agent execution code tested with fakes.
- A clearly labelled offline mock CLI using committed synthetic data.

## Why This Matters for QA / AI Quality

The project focuses on testable quality boundaries around an AI-assisted QA workflow: traceability, typed contracts, deterministic validation, controlled failures, safe presentation, and a clear distinction between extracted facts and proposed or inferred content. It is designed to support human QA review, not replace it.

## Tech Stack

Python 3.11–3.13, Pydantic, pytest, Google GenAI SDK boundary, and `uv`.

Google ADK and multi-agent orchestration are documented target technologies; they are not part of the supported local execution path.

## Safety-First Design

- Raw input is processed by the pre-provider safety gate; only sanitized input is intended to enter provider calls, application state, logs, or traces.
- Requirements are treated as untrusted data, not instructions.
- Candidate output is validated before it can become canonical output.
- User-facing Markdown is generated deterministically from validated data.
- The mock demo never silently falls back from live execution and never makes a live API call.

See [Safety Boundaries](docs/safety_boundaries.md) for the precise scope and [Data Contract Boundaries](docs/DATA_CONTRACT_BOUNDARIES.md) for the contract model.

## Current Architecture

Today, the runnable path is:

```text
Committed synthetic requirement data
  -> deterministic validation
  -> safe Markdown renderer
  -> output-safety check
  -> labelled mock CLI output
```

The deterministic domain, validation, input-safety, provider-boundary, and rendering components are implemented independently. There is no supported end-to-end live agent pipeline.

## Target Architecture

The documented target is a trust-aware sequential workflow with input safety, requirement analysis, risk/test design, QA review, deterministic aggregation, validation, output safety, and deterministic rendering. It is **designed architecture**, not an operational live workflow. See [Architecture](docs/ARCHITECTURE.md) and [MVP Scope](docs/MVP_SCOPE.md).

## Testing

The unit suite covers deterministic contracts, IDs, provenance, validation, pipeline-stage behavior, input and output safety, safe rendering, provider failures, adapter behavior, and malformed model drafts.

These tests are deterministic code tests. They are not evidence of semantic LLM quality. The repository contains an [evaluation plan](docs/EVALUATION_PLAN.md); completed semantic LLM evaluation results are not included.

## Controlled Demo

Run the offline mock demo:

```bash
uv run python -m app.local_demo --mock
```

It renders committed synthetic data and prints `[DEMO / MOCK OUTPUT]`. It accepts no custom requirement input and does not call Gemini. See the [demo guide](docs/demo.md).

## Repository Structure

```text
app/        Deterministic domain, validation, safety, provider-boundary, and rendering code
tests/unit/ Deterministic automated tests
docs/       Architecture, contracts, safety, evaluation plan, demo, and status documentation
```

## Technical Documentation

- [Current Release Status](docs/release_status.md)
- [Safety Boundaries](docs/safety_boundaries.md)
- [Target Architecture](docs/ARCHITECTURE.md)
- [Evaluation Plan](docs/EVALUATION_PLAN.md)
- [Demo Guide](docs/demo.md)
- [Entity Contracts](docs/ENTITY_CONTRACTS.md)

## Current Limitations

- No supported live user-facing CLI or committed reproducible live-execution evidence.
- No end-to-end multi-agent orchestration.
- No completed semantic LLM evaluation evidence.
- The mock CLI is presentation-only and does not process arbitrary input.

## Reuse / License Notice

No open-source license is currently selected. The repository is shared for review and demonstration; detailed reuse and Kaggle-related context is in [release status](docs/release_status.md). This notice is informational and not legal advice.
