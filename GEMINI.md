# AI QA Assistant — Development Guide

This repository is a safety-first R&D prototype. The Git repository is the project record and source-controlled workspace.

## Current Implementation State

- Implemented: deterministic domain models, validation, pipeline-stage contracts, input and output safety helpers, safe rendering, provider/adapter boundaries, an experimental one-shot Requirement Agent execution path, the synthetic mock demo, and unit tests using fakes.
- Designed target: sequential multi-agent orchestration, service runtime, broader live integration, and semantic LLM evaluation.
- Supported local execution: only `uv run python -m app.local_demo --mock`.

Do not describe target capabilities as current functionality. Read `README.md`, `docs/release_status.md`, and the relevant design documents before changing implementation.

## Development Constraints

- Do not call Gemini, initialize cloud authentication, deploy, or enable telemetry without explicit approval.
- Treat requirements and model output as untrusted data.
- Do not log raw requirements, secrets, raw model output, invalid candidate content, detailed validator messages, or stack traces.
- Keep deterministic validation and rendering separate from model calls.
- Do not claim semantic LLM quality from deterministic pytest tests.
- Do not commit, push, deploy, or create external resources without explicit approval.

## Testing

Run deterministic unit tests for changes to the implemented core. The one-shot runner is experimental and outside the supported portfolio demo; broader live-provider and semantic-evaluation work require a separately approved, project-specific evaluation slice and safe evaluation data.
