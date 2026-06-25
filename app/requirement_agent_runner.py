from app.domain_models import RequirementAnalysis, StageResult, SanitizedInputEnvelope
import app.requirement_agent_prompt as requirement_agent_prompt
from app.requirement_agent_provider import (
    RequirementAgentProvider,
    run_requirement_agent_with_provider,
)


class FakePromptAwareProvider:
    """A fake, local-only provider that receives a prompt string and returns a configured draft JSON."""

    def __init__(self, response_text: str = "", raises_exc: Exception = None):
        self.response_text = response_text
        self.raises_exc = raises_exc
        self.seen_prompt = None

    def generate_draft_from_prompt(self, prompt: str) -> str:
        self.seen_prompt = prompt
        if self.raises_exc:
            raise self.raises_exc
        return self.response_text


class PromptBuilderRequirementAgentProvider(RequirementAgentProvider):
    """Adapter bridging the SanitizedInputEnvelope-oriented RequirementAgentProvider
    with a prompt-aware logic/callable.
    """

    def __init__(self, fake_provider: FakePromptAwareProvider):
        self.fake_provider = fake_provider

    def generate_draft(self, sanitized_input: SanitizedInputEnvelope) -> str:
        # Prompt builder ValueError is caught by run_requirement_agent_with_provider's generic except
        prompt = requirement_agent_prompt.build_requirement_agent_prompt(sanitized_input)
        return self.fake_provider.generate_draft_from_prompt(prompt)


def run_requirement_agent_pipeline_with_fake_provider(
    sanitized_input: SanitizedInputEnvelope,
    fake_provider: FakePromptAwareProvider,
) -> StageResult[RequirementAnalysis]:
    """Connects prompt building, the provider boundary, and output validation."""
    provider_adapter = PromptBuilderRequirementAgentProvider(fake_provider)
    return run_requirement_agent_with_provider(sanitized_input, provider_adapter)
