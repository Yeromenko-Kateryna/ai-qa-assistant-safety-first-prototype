from app.domain_models import RequirementAnalysis, StageResult, StageStatus, SanitizedInputEnvelope
from app.requirement_agent_adapter import parse_requirement_agent_draft

# Error Codes for Provider Layer
AGENT_PROVIDER_FAILED = "AGENT_PROVIDER_FAILED"
AGENT_PROVIDER_TIMEOUT = "AGENT_PROVIDER_TIMEOUT"
AGENT_PROVIDER_EMPTY_DRAFT = "AGENT_PROVIDER_EMPTY_DRAFT"


class RequirementAgentProvider:
    """Interface/base class for generating candidate requirement drafts from sanitized inputs."""

    def generate_draft(self, sanitized_input: SanitizedInputEnvelope) -> str:
        """Generates raw candidate JSON draft text from the sanitized segment inputs.

        Subclasses will implement this to run LLM reasoning (or fakes in testing).
        """
        raise NotImplementedError("Subclasses must implement generate_draft")


def run_requirement_agent_with_provider(
    sanitized_input: SanitizedInputEnvelope,
    provider: RequirementAgentProvider,
) -> StageResult[RequirementAnalysis]:
    """Runs the requirement agent generation and validates the output through the adapter.

    Catches provider failures, timeouts, and empty drafts to ensure raw exceptions
    never leak downstream.
    """
    try:
        # 1. Generate candidate draft string from provider
        draft_text = provider.generate_draft(sanitized_input)
    except TimeoutError:
        return StageResult(
            status=StageStatus.FAILED,
            committed_output=None,
            error_code=AGENT_PROVIDER_TIMEOUT,
            safe_message="The requirement agent request timed out."
        )
    except Exception:
        # Prevent leaking raw exception messages or stack traces
        return StageResult(
            status=StageStatus.FAILED,
            committed_output=None,
            error_code=AGENT_PROVIDER_FAILED,
            safe_message="The requirement agent provider encountered an error."
        )

    # 2. Check that the returned draft is a string
    if not isinstance(draft_text, str):
        return StageResult(
            status=StageStatus.FAILED,
            committed_output=None,
            error_code=AGENT_PROVIDER_FAILED,
            safe_message="The requirement agent provider encountered an error."
        )

    # 3. Check for empty or whitespace draft at the provider boundary layer
    if not draft_text or not draft_text.strip():
        return StageResult(
            status=StageStatus.FAILED,
            committed_output=None,
            error_code=AGENT_PROVIDER_EMPTY_DRAFT,
            safe_message="The requirement agent provider returned an empty draft."
        )

    # 4. Pipe the draft through the adapter boundary (structural, semantic, and safety validator)
    adapter_result = parse_requirement_agent_draft(draft_text)

    return adapter_result
