# Mock Demo Guide

This document describes how to execute and verify the AI QA Assistant mock demo.

## Overview

The mock demo showcases the system's safe report formatting and demo presentation path using pre-configured synthetic data. It allows verification of the visual markdown formatting, section structures, and safety redactions.

## Running the Mock Demo

Run the CLI script with the explicit `--mock` boolean flag:

```bash
uv run python -m app.local_demo --mock
```

- **Selector Flag**: The `--mock` flag is the only supported selector mode. It does not accept any additional input payloads.
- **Unsupported Inputs**: Command parameters such as `--input`, `--mock-json`, file payloads, or environment variable injections are not supported.
- **No API Call**: This command runs entirely offline. It does not call the Gemini API or require any API keys/environment secrets.
- **Preflight Check**: Running without the `--mock` flag is unsupported and returns a safe notice explaining that real-mode is disabled.

## Demo Output Details

When running in mock mode, the output is formatted as follows:

- **Mock Output Label**: The top of the output is visibly prefixed with:
  ```text
  [DEMO / MOCK OUTPUT]
  ```
- **Frozen MVP Scope Visible Fields**:
  - **Summary**: A sanitized summary of the requirement document.
  - **Requirements**: A bulleted list of requirement descriptions, categorized by category type (e.g., `[FUNCTIONAL]`, `[NON_FUNCTIONAL]`).
  - **Acceptance Criteria**: A list of criteria text associated with the requirements.

- **Intentionally Hidden/Redacted Fields**:
  To protect privacy and prevent internal data leaks, the following fields are strictly omitted from the user-facing report:
  - **Internal Database IDs**: No entity IDs (e.g., requirement identifiers or criteria identifiers) are displayed.
  - **Provenance Maps**: No origin enums, transformation enums, or parent/derived relations are printed.
  - **Source/Derived Segment Lists**: No lists of underlying document segment references are leaked.
  - **System Rationales**: Internal reasoning and rationales for proposed criteria are excluded.
  - **Diagnostics/Payloads**: No raw API payloads, prompts, drafts, stack traces, or exception messages are printed.
