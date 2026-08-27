# Target MVP Scope v1.0

> **Status: designed scope, not current release status.** This document defines the intended narrow MVP and its Definition of Done. The current release is a deterministic-core and mock-demo prototype; see [release_status.md](release_status.md).

## Product Goal

Transform unstructured English product requirements into a structured QA draft that helps a QA engineer begin analysis systematically without replacing human judgment.

## Target User Flow

1. A QA engineer submits pasted requirement text.
2. A deterministic pre-ADK gate validates language, size, secrets, URLs, and suspicious instruction patterns.
3. Only sanitized input enters the ADK workflow.
4. Requirement, Risk & Test Design, and QA Review agents run sequentially.
5. A deterministic aggregator builds a candidate report without a model call.
6. The candidate passes schema and referential validation.
7. Output Safety Gate produces safe canonical JSON or a trusted safe error.
8. A deterministic renderer produces Markdown.

## Included

- Requirement summary and extracted facts
- Extracted and proposed acceptance criteria kept separate
- Business rules
- Ambiguities, assumptions, and missing information
- Functional, boundary, validation, integration, and security risks
- Prioritized and traceable test cases
- Requirement classification as UI, API, HYBRID, AMBIGUOUS, or INSUFFICIENT_INFORMATION
- Automation recommendations linked to generated test cases
- No generated automation code in the mandatory MVP
- QA completeness and consistency review
- Input and output safety results

## Excluded

- File uploads
- Jira, GitHub Issues, and Confluence integrations
- External browsing and URL access
- Real Playwright or API execution
- Playwright or API code generation in the mandatory MVP
- Shell and code execution
- Repository writes and pull requests
- Database persistence
- User accounts and production authentication
- MCP tools
- Mandatory Cloud Run deployment

## Definition of Done

- Local multi-agent workflow works end to end.
- Canonical JSON and deterministic Markdown are produced safely.
- Safety gates and resource limits are enforced.
- The three narrow-MVP release scenarios pass alongside deterministic contract and safety tests.
- README, architecture diagram, GitHub repository, and video demonstration exist.
- Used course technologies and intentionally excluded technologies are explained.
