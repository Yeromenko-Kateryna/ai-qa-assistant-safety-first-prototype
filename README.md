# AI QA Assistant

> [!IMPORTANT]
> **Project Status**: R&D mock MVP demo candidate.
> This project is currently **not production-ready**, does **not** support live Gemini CLI integration, and does **not** connect to `app/agent.py`.

This repository contains the AI QA Assistant prototype, focusing on a safe and isolated requirements extraction corridor.

## Safe Demo Path

The current release candidate provides an explicit mock/demo command-line execution path. It uses pre-configured, synthetic, schema-valid requirements data formatted through the safe renderer to demonstrate the target user experience.

### Running the Mock Demo

Execute the mock demo using the explicit `--mock` flag:

```bash
uv run python -m app.local_demo --mock
```

- **Explicit Mode Selector**: The `--mock` flag must be explicitly passed.
- **No API Keys**: No Gemini API keys or environment setup are required for mock mode.
- **No Live Calls**: The mock demo does not contact the live Gemini API.
- **No Custom Inputs**: Raw input text or external file payloads are not processed by the mock integration path.

## Documentation Index

For detailed guidelines, safety rules, and project milestones, please refer to the following documents:

1. **[docs/demo.md](docs/demo.md)**: Details on mock demo outputs, visible fields, and hidden properties.
2. **[docs/safety_boundaries.md](docs/safety_boundaries.md)**: Architectural invariants, data-leak constraints, and blocked scopes.
3. **[docs/release_status.md](docs/release_status.md)**: Status roadmap, unproven areas, and safe gate validation history.

## License / Reuse and Kaggle Competition Terms

No open-source license is currently selected for this repository. All rights are reserved by the project owner.

This repository may be shared publicly for review and demonstration purposes only. Public availability of this repository does not mean the project is open source.

Under the current repository reuse status, no permission is granted to copy, modify, redistribute, sublicense, sell, or use this repository code commercially without explicit written permission from the project owner.

This repository reuse notice does not override any rights, licenses, publication terms, reproduction requirements, or winner obligations that may apply to Kaggle-hosted writeups, Kaggle submission materials, winning Submissions, or source code used to generate a winning Submission under the applicable competition rules.

If the project is selected as a winner or otherwise becomes subject to additional competition licensing requirements, the project owner will need to review and satisfy those requirements separately before making any further licensing, distribution, or reuse claims.

This statement is informational and is not legal advice.
