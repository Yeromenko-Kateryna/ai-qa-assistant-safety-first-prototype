# Controlled Mock Demo Checklist

This document is a human-facing checklist and presentation guide for the AI QA Assistant mock-only MVP demo.

> [!IMPORTANT]
> **Checklist Parameters and Status**:
> - This is a **human-facing checklist**.
> - This is for the **mock-only MVP demo**.
> - This is **not** an automation script.
> - This is **not** a real Gemini execution guide.
> - This is **not** production-readiness or customer-data readiness documentation.

---

## 1. Pre-Demo Caveats

The presenter must explicitly state the following caveats to the audience before running the demo or displaying the output report:
- This is a mock-only demo using committed, synthetic data.
- The demo does not call the Gemini API.
- The demo does not process arbitrary or custom user requirements.
- The demo does not require API keys or GCP credentials.
- The demo is not production-ready or customer-data ready.
- The demo is intended solely to demonstrate safe output formatting, layout structure, and safety redaction boundaries.

---

## 2. Allowed Execution Command

Run only this command to execute the mock demo:

```bash
uv run python -m app.local_demo --mock
```

### Constraints:
- This command is for controlled mock demo use only.
- The `--mock` flag is a boolean mode selector only. It must not be used as a payload input channel.
- Parameters such as `--input`, `--mock-json`, file payloads, env variable injections, or custom requirement texts are strictly unsupported.
- Live Gemini API calls and the experimental one-shot runner are outside the supported mock-demo path.

---

## 3. Presenter Script Guidelines

### What the Presenter MAY Say:
- "This demonstrates the mock UX shell for the requirements analysis stage."
- "This shows the safe renderer output format, presenting the Summary, Requirements, and Acceptance Criteria sections."
- "All internal IDs, provenance mappings, source segment lists, derived relations, rationales, raw JSON, and diagnostics are hidden by the renderer."
- "This is an R&D prototype with a controlled mock demo."
- "The repository contains deterministic source code and unit tests for the implemented core; no reproducible historical live-gate artifacts are included."

### What the Presenter MUST NOT Say:
- Do not say this is live Gemini output or real-time generation.
- Do not say this processes arbitrary user input.
- Do not say the tool is production-ready or customer-data ready.
- Do not present historical gate outcomes as independently verified evidence.
- Do not say the semantic quality of generated requirements or criteria is proven.
- Do not say that live multi-agent orchestration is integrated or active.
- Do not say real-mode `local_demo` execution is implemented.
- Do not say support for optional arrays (business rules, assumptions, ambiguities) is complete.
- Do not say API keys or model authentication check policies were verified during execution.

---

## 4. Expected Output Observations

Verify the following output structure manually after running the demo:
- **Visibly Present**:
  - The `[DEMO / MOCK OUTPUT]` header at the top of the output.
  - The `Summary` section containing safe, pre-written text.
  - The `Requirements` section listing category-tagged bulleted items (e.g. `[FUNCTIONAL]`, `[NON_FUNCTIONAL]`).
  - The `Acceptance Criteria` section listing criteria bullet points.
- **Strictly Absent**:
  - No database/internal IDs (e.g., requirement keys or criteria keys).
  - No provenance records (e.g. origin, transformation, source segment ids, derived from ids).
  - No rationales or internal reasoning texts.
  - No business rules, ambiguities, missing information, or assumptions headings.
  - No raw JSON objects, exception traces, secrets, or API key parameters.

*(Note: Actual output transcripts, screenshots, and raw model dumps are omitted from this guide.)*

---

## 5. Post-Demo Summary

State the following post-demo status summary:
- The mock demo successfully displayed the expected safe layout sections.
- The output was labeled as mock/demo.
- The demo did not call the Gemini API or process arbitrary user requirements.
- Real-mode integration remains blocked.
- Live multi-agent orchestration remains deferred.
- Production and customer data testing remain blocked.

---

## 6. Unsupported / Unproven for the Portfolio Demo

The following are not part of the supported portfolio demo or current release evidence:
- Live Gemini execution during the demo.
- Execution of the experimental one-shot runner.
- Real-mode `local_demo` integration.
- Live multi-agent orchestration.
- Production, customer, or confidential data testing.
- Completed semantic LLM evaluation.
- Raw response and intermediate draft logs inspection.
- Committed output file on-disk validation.
- Relaxation of parser/validator schemas.
- Automation wrappers or execution scripts.
- Checking in screenshots, transcripts, or raw model dumps.

---

## 7. Documentation References

For more details on the safety design, demo overview, and project history, refer to:
- [docs/demo.md](demo.md)
- [docs/safety_boundaries.md](safety_boundaries.md)
- [docs/release_status.md](release_status.md)
