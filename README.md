# AI QA Assistant — Safety-First Requirements Analysis Prototype

This repository contains a safety-first AI-assisted QA prototype for transforming unstructured English product requirements into structured requirement-analysis drafts.

The project demonstrates practical QA + AI Quality skills: deterministic validation, typed data contracts, provenance-aware requirement modelling, input and output safety controls, safe failure handling, provider/SDK boundaries, experimental one-shot Gemini integration, automated testing, and evidence-bounded technical documentation.

---

## Tech Stack

- Python 3.11–3.13
- Pydantic
- pytest
- Google GenAI SDK
- `uv`
- Deterministic validation and rendering
- Safety-focused QA design
- Mock/offline CLI demonstration

Google ADK and sequential multi-agent orchestration are documented target technologies; they are not part of the supported local demo path.

---

## Project Architecture

The currently supported portfolio path is intentionally deterministic and offline:

```text
Committed synthetic requirement data
  -> deterministic validation
  -> safe Markdown renderer
  -> output-safety check
  -> labelled mock CLI output
```

The repository also contains independently implemented domain, input-safety, provider-boundary, validation, and rendering components.

An experimental one-shot Gemini execution path exists for the Requirement Agent boundary, but it is outside the supported portfolio demo and no reproducible live-run evidence is committed.

The documented target architecture extends this into a trust-aware sequential workflow with requirement analysis, risk/test design, QA review, deterministic aggregation, validation, output safety, and rendering.

See [Target Architecture](docs/ARCHITECTURE.md) and [MVP Scope](docs/MVP_SCOPE.md).

---

## Features

- Converts requirement-analysis data into typed Pydantic domain models
- Distinguishes extracted, inferred, proposed, assumed, and missing information through explicit data contracts
- Performs deterministic structural and referential validation
- Applies input-safety checks for language, size, secret-like values, URLs, and suspicious instruction patterns
- Treats requirement text as untrusted data rather than executable instructions
- Rejects malformed or unsafe candidate drafts before canonical output is produced
- Applies output-safety checks before presentation
- Uses a deterministic Markdown renderer that hides internal IDs, provenance mappings, rationales, raw payloads, and diagnostics
- Uses lazy SDK imports to preserve import isolation
- Implements provider and SDK-adapter boundaries for Gemini interaction
- Includes experimental one-shot Requirement Agent execution code tested with fakes
- Provides an explicit offline mock CLI using committed synthetic data
- Separates deterministic code verification from future semantic LLM evaluation

---

## QA / AI Quality Coverage

The project focuses on quality controls around an AI-assisted QA workflow rather than treating model output as trusted application state.

### Data and Contract Validation

- Required model fields and schema structure
- Stable IDs and referential consistency
- Provenance-aware requirement contracts
- Stage-result success/failure handling
- Invalid and malformed candidate drafts
- Missing and unsupported data handling

### Safety Boundaries

- Input sanitization before provider-facing processing
- Suspicious instruction and prompt-injection-like pattern handling
- Secret-like value detection
- URL and unsupported-language checks
- Safe handling of provider and adapter failures
- Prevention of unvalidated model-derived content from becoming canonical output
- Deterministic user-facing rendering
- Output filtering for internal implementation details

### Provider and Adapter Behaviour

- Gemini provider boundary behaviour
- SDK adapter behaviour using injected/fake clients
- Lazy SDK import isolation
- Empty, missing, malformed, and non-string model responses
- Provider exceptions and safe error propagation

Detailed safety rationale is available in [Safety Boundaries](docs/safety_boundaries.md) and [Data Contract Boundaries](docs/DATA_CONTRACT_BOUNDARIES.md).

---

## Automated Test Coverage

The current deterministic unit suite covers domain contracts, IDs, provenance, validation, pipeline-stage behaviour, input and output safety, safe rendering, provider failures, adapter behaviour, diagnostics, and malformed model drafts.

### Coverage Summary

```text
174 automated tests
174 passed
0 failed
```

The final local run completed successfully with one `PytestCacheWarning` caused by a local Windows permission issue for `.pytest_cache`; it did not affect test execution.

These tests verify deterministic code behaviour. They are **not** evidence of semantic LLM quality or completed live Gemini evaluation.

The planned nondeterministic evaluation strategy is documented in [Evaluation Plan](docs/EVALUATION_PLAN.md).

---

## Safety Strategy

The project uses explicit trust boundaries around both input and generated content.

- Raw input is processed at the pre-provider safety boundary.
- Only sanitized input is intended to enter provider calls, application state, logs, or traces.
- Requirements are handled as data, not as trusted instructions.
- Model candidate output must satisfy deterministic contracts before it can become committed output.
- User-facing Markdown is generated from validated data rather than directly from raw model output.
- Internal IDs, provenance mappings, rationales, raw JSON, and diagnostics are excluded from the rendered report.
- The mock demo never silently falls back to live execution.

---

## Experimental Gemini Boundary

The repository includes an experimental one-shot execution path for the Requirement Agent boundary.

The path:

- checks `GEMINI_API_KEY` and `GEMINI_MODEL_NAME`;
- lazily creates the Google GenAI SDK client;
- calls the Gemini provider boundary;
- passes the generated draft through deterministic validation and safety handling;
- exposes only safe aggregate execution metadata.

This code demonstrates the integration boundary, but it is **not** presented as the supported portfolio demo and no reproducible live-run result is committed.

The following remain outside the demonstrated release scope:

- live user-facing CLI execution;
- end-to-end multi-agent orchestration;
- service/runtime deployment;
- production or customer-data testing;
- completed semantic LLM evaluation.

---

## Controlled Demo

Run the supported offline mock demo:

```bash
uv run python -m app.local_demo --mock
```

The demo:

- uses committed synthetic requirement-analysis data;
- accepts no arbitrary requirement input;
- requires no Gemini API key;
- makes no Gemini API call;
- renders the same safe Markdown format used by the deterministic presentation layer;
- clearly labels the result as `[DEMO / MOCK OUTPUT]`.

See [Demo Guide](docs/demo.md) and [Demo Checklist](docs/demo_checklist.md).

---

## Run Tests Locally

Install the project dependencies using `uv`, then run the deterministic test suite:

```bash
uv run pytest -q
```

Collect the available tests without executing them:

```bash
uv run pytest --collect-only -q
```

Run the supported mock demonstration:

```bash
uv run python -m app.local_demo --mock
```

---

## Repository Structure

```text
app/        Domain models, validation, safety, provider boundaries, diagnostics, and rendering
scripts/    Experimental one-shot and smoke execution helpers
tests/unit/ Deterministic automated tests
docs/       Architecture, contracts, safety, evaluation, demo, and release documentation
```

---

## QA Documentation

### [Target Architecture](docs/ARCHITECTURE.md)

Designed trust-aware multi-stage workflow and separation between the current deterministic corridor and future orchestration.

### [Safety Boundaries](docs/safety_boundaries.md)

Input, provider, validation, output, logging, and trust-boundary constraints.

### [Evaluation Plan](docs/EVALUATION_PLAN.md)

Planned separation between deterministic verification and nondeterministic semantic LLM evaluation.

### [Data Contract Boundaries](docs/DATA_CONTRACT_BOUNDARIES.md)

Rules for extracted, inferred, proposed, assumed, and missing information.

### [Entity Contracts](docs/ENTITY_CONTRACTS.md)

Typed entity structures, validation expectations, and QA findings taxonomy.

### [Demo Guide](docs/demo.md)

Supported offline demonstration path and visible output behaviour.

### [Release Status](docs/release_status.md)

Current demonstrated capabilities, evidence status, and unproven/deferred areas.

---

## Quality Practices Demonstrated

- Deterministic validation around model-derived data
- Explicit trust-boundary design
- Typed domain and provenance contracts
- Safe failure handling instead of silent fallback
- Separation of deterministic testing from semantic LLM evaluation
- Prompt-injection-aware input handling
- Provider and SDK isolation through dependency injection
- Fake-client testing for AI integration boundaries
- Deterministic rendering of validated output
- Evidence-bounded documentation and release claims
- Clear separation between implemented, supported, target, and unproven capabilities
- Removal of unrelated generated scaffold artifacts from the public portfolio

---

## What I Learned

- How to design deterministic QA controls around nondeterministic AI output
- How to model provenance and distinguish extracted facts from inferred or proposed information
- How to prevent raw model output from becoming trusted application state without validation
- How to build provider and SDK boundaries that can be tested without live API calls
- How to test malformed, unsafe, empty, and structurally invalid model responses
- How to design a safe renderer that exposes only approved user-facing fields
- How to separate unit-test evidence from semantic LLM evaluation claims
- How to document experimental AI integration without presenting it as production-ready functionality
- How to distinguish current implementation from target architecture in technical documentation

---

## Project Status

Portfolio-ready R&D prototype.

The current repository includes:

- 174 deterministic automated tests
- 174 passing tests in the final local run
- deterministic requirement-analysis contracts and validation
- input and output safety boundaries
- safe Markdown rendering
- provider and Google GenAI SDK adapter boundaries
- experimental one-shot Requirement Agent execution code
- supported offline synthetic mock demo
- documented target multi-agent architecture
- documented deterministic and semantic evaluation strategy

Current limitations:

- no supported live user-facing CLI;
- no committed reproducible live-execution evidence;
- no end-to-end multi-agent orchestration;
- no completed semantic LLM evaluation results;
- no production or customer-data validation.

---

## Reuse / License Notice

No open-source license is currently selected. The repository is shared for review and demonstration purposes. Detailed reuse and Kaggle-related context is available in [Release Status](docs/release_status.md).

This notice is informational and not legal advice.

---

## Author

Kateryna Yeromenko

GitHub: [Yeromenko-Kateryna](https://github.com/Yeromenko-Kateryna)
