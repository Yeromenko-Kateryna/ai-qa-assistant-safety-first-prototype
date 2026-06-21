# Product and Architecture Decisions

## Approved Decisions

### 001 — Problem

AI QA Assistant addresses slow and inconsistent manual analysis of incomplete or ambiguous product requirements.

### 002 — Audience

The primary audience is junior and middle QA engineers in small Agile teams.

### 003 — MVP Input

MVP accepts pasted plain text only.

### 004 — MVP Output

MVP produces a structured QA draft: requirement analysis, risk analysis, traceable test design, automation plan or skeleton, and QA review.

### 005 — Safety Boundary

MVP performs no code execution, browser access, external API calls, repository access, issue creation, or external side effects.

### 006 — Architecture

The system uses pre-model and post-generation deterministic safety boundaries around a sequential multi-agent workflow.

### 007 — Technology Stack

Must-have: ADK, Gemini, multi-agent orchestration, structured output, safety guardrails, evaluation, GitHub documentation, architecture diagram, and video.

Should-have: local FastAPI endpoint.

Optional: local web page and Cloud Run.

Excluded from v1.0: MCP, external integrations, persistence, authentication, and real test execution.

### 008 — Language Scope

MVP supports English requirements. Unsupported and substantial mixed-language input returns a safe pre-model error.

### 009 — Canonical Output

Canonical output is versioned JSON. Markdown is produced deterministically from JSON without another LLM call.

## Working Environment Decision

- Maintain one ordinary Git repository.
- Use Antigravity only as an interface over that repository.
- Do not create a separate Antigravity copy.
- Complete and approve architecture and data contracts before `agents-cli` scaffolding.
- Do not create agent code manually before scaffolding.
