# Safety Boundaries and Invariants

This document details the architectural safety design and data leak-prevention rules of the AI QA Assistant.

## Core Design Principles

1. **Strict Output Redaction**:
   The system implements a zero-trust presentation layer. Under no circumstances should internal metadata or diagnostic telemetry be exposed to the user.
2. **Safe Renderer Boundary**:
   User-facing reports are rendered exclusively through the safe renderer. It receives a validated internal data model and generates sanitized markdown text.
3. **No Silent Fallbacks**:
   To prevent deceptive UX behavior, the system must never silently switch from a failing live execution path to mock data. If a future real-mode execution path is implemented and fails or lacks authorization, the process must terminate immediately with a clean, generic failure notice.

## Architectural Boundaries

- **Input Safety Gate**: Processes raw input at the pre-provider boundary. Only sanitized input may enter provider calls, application state, logs, or traces in the target workflow.
- **Output Safety Gate**: Screens final rendered markdown to ensure no secrets, passwords, or raw object strings are present.
- **Import Isolation**: Modules like `app/local_demo.py` and `app/renderer.py` do not load Gemini SDK modules, cloud trace adapters, or live provider classes at module import time, preserving offline environment safety.

## Blocked Scopes and Deferred Features

- **Gemini Live CLI**: Real-mode Gemini invocation remains disabled.
- **Live Orchestration**: Multi-agent orchestration is a target capability and is not integrated into the supported local execution path.
- **Optional Arrays**: Support for Business Rules, Ambiguities, Missing Information, and Assumptions is deferred; the current mock demo and safe rendering path do not surface these arrays.
- **Payload Telemetry**: Prompt text, draft responses, raw model payloads, and raw exception logs are completely excluded from user-facing buffers.
