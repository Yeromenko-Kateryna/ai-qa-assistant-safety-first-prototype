# ADK Reference Pattern Study

Status: Phase 1 reference study completed. No sample code has been copied.

## Purpose

This study records official Google ADK patterns that may inform future live orchestration. It does not change the approved target scope, data contracts, or trust boundaries.

## Sources Reviewed

- [`deep-search/app/agent.py`](https://github.com/google/adk-samples/blob/main/python/agents/deep-search/app/agent.py)
- [`safety-plugins/safety_plugins/main.py`](https://github.com/google/adk-samples/blob/main/python/agents/safety-plugins/safety_plugins/main.py)
- [`safety-plugins/plugins/model_armor.py`](https://github.com/google/adk-samples/blob/main/python/agents/safety-plugins/safety_plugins/plugins/model_armor.py)
- [`safety-plugins/plugins/agent_as_a_judge.py`](https://github.com/google/adk-samples/blob/main/python/agents/safety-plugins/safety_plugins/plugins/agent_as_a_judge.py)

## `deep-search`: Orchestration and Review

### Reuse conceptually

- Use explicit sequential orchestration so stage order is visible and testable.
- Give each model stage a dedicated responsibility and a named state output.
- Use typed structured output for the reviewer instead of parsing free-form prose.
- Keep the QA reviewer separate from the agents that create requirement, risk, and test artifacts.
- Perform aggregation and human-readable rendering in deterministic code rather than another model call.

### Adapt for this MVP

- Validate every stage candidate before exposing it to a downstream stage. ADK state passing does not replace schema, reference, resource, or safety validation.
- Stop the pipeline with the trusted Safe Error Envelope when a stage fails. Do not ask an agent to improvise an error response.
- Run exactly one pass through Requirement Agent, Risk & Test Design Agent, and QA Review Agent for the narrow MVP.

### Do not reuse

- The research/refinement loop and its repeated model calls.
- Web search, source collection, citation processing, agent tools, or agent transfer.
- Model-controlled approval of structurally invalid data.

These features solve a research problem and would increase cost and nondeterminism without helping the approved QA workflow.

## `safety-plugins`: Guardrail Separation

### Reuse conceptually

- Treat safety as a cross-cutting boundary around the agents, not as an instruction buried inside an agent prompt.
- Block unsafe input before the normal agent run continues.
- Replace blocked content with a stable, safe response that does not repeat the unsafe material.
- Apply a separate check to model output before it becomes user-visible.

### Adapt for this MVP

- The Input Safety Gate remains outside and before the ADK Runner so secrets and unsupported input cannot reach Gemini, ADK state, logs, or traces.
- The Output Safety Gate examines a schema-valid Candidate JSON and produces Safe Canonical JSON only after deterministic validation.
- Safety failures use the trusted Safe Error Envelope and stable error codes.
- Agents have no tools, so tool-input and tool-output callbacks are unnecessary in v1.0.

### Do not reuse

- The LLM-as-a-judge plugin as a runtime safety enforcement boundary. It adds a model call and nondeterministic safety decisions. This exclusion does not apply to offline LLM-as-judge quality evaluation governed by the Evaluation Plan.
- Model Armor as an MVP dependency. It requires an external cloud service and does not replace the approved local pre-ADK boundary.
- Logging raw prompts or model responses. The sample logs these values in places; the AI QA Assistant explicitly forbids raw requirements, secrets, invalid candidates, and model responses from logs and traces.
- Returning filter details that could echo sensitive or adversarial content.

## Resulting MVP Pattern

The implementation target remains:

`Input Safety Gate -> Requirement Agent -> validation -> Risk & Test Design Agent -> validation -> QA Review Agent -> validation -> deterministic aggregation -> Output Safety Gate -> Safe Canonical JSON -> deterministic Markdown`

The official samples inform the orchestration and guardrail boundaries, but their research tools, refinement loop, cloud safety dependency, and prompt logging are intentionally excluded.

## Exit Decision

The reference-study exit criterion is satisfied: reusable patterns and explicit exclusions are documented. Any future live-orchestration work requires a separately approved, project-specific implementation and evaluation plan.
