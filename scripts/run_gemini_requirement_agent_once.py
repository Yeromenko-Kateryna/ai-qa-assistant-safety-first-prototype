# No module-level imports of google.genai, google.auth, google.adk, or app.agent are allowed.
# No module-level env var reads or executable statements.

def is_git_status_clean(status_stdout: str) -> bool:
    """Classifies if git status is clean.

    Returns True if the output consists only of the branch header line (or is empty),
    and contains no modified, deleted, staged, or untracked file entries.
    """
    lines = [line.strip() for line in status_stdout.splitlines() if line.strip()]
    if not lines:
        return True
    for line in lines:
        if not line.startswith("##"):
            return False
    return True


def check_env_vars(environ) -> tuple[bool, str]:
    """Verify that GEMINI_API_KEY and GEMINI_MODEL_NAME are present."""
    if "GEMINI_API_KEY" not in environ:
        return False, "Error: GEMINI_API_KEY environment variable is not set."
    if "GEMINI_MODEL_NAME" not in environ:
        return False, "Error: GEMINI_MODEL_NAME environment variable is not set."
    return True, ""


class CountingClientWrapper:
    """Wraps a Gemini client adapter to count the number of generate_content calls."""

    def __init__(self, target_client):
        self.target_client = target_client
        self.count = 0

    def generate_content(self, model_name: str, prompt: str) -> object:
        self.count += 1
        return self.target_client.generate_content(model_name, prompt)


def execute_request(environ, import_genai, client_adapter_class=None) -> dict:
    """Executes the single synthetic Gemini API request using dependency injection.

    Returns a dict summary containing safety metadata without secrets/payload text.
    """
    summary = {
        "api_key_present": False,
        "model_name_present": False,
        "model_configured": False,
        "sdk_readiness": False,
        "request_attempted": False,
        "request_count": 0,
        "stage_status": "FAILED",
        "error_code": "AGENT_PROVIDER_FAILED",
        "committed_output_exists": False,
        "requirement_count": 0,
    }

    # 1. Check environment variables
    summary["api_key_present"] = "GEMINI_API_KEY" in environ
    summary["model_name_present"] = "GEMINI_MODEL_NAME" in environ

    env_ok, _ = check_env_vars(environ)
    if not env_ok:
        summary["error_code"] = "AGENT_PROVIDER_FAILED"
        return summary

    # 2. Check SDK readiness via lazy import
    try:
        import_genai()
        summary["sdk_readiness"] = True
    except ImportError:
        summary["error_code"] = "AGENT_PROVIDER_FAILED"
        return summary

    summary["model_configured"] = True

    # 3. Import and run validation/safety
    from app.input_safety import sanitize_requirement_text
    from app.gemini_requirement_agent_provider import GeminiRequirementAgentProvider
    from app.requirement_agent_provider import run_requirement_agent_with_provider, RequirementAgentProvider
    import app.requirement_agent_prompt as requirement_agent_prompt
    from app.domain_models import StageStatus

    synthetic_input = "The system shall display a system status indicator."
    try:
        sanitized_input = sanitize_requirement_text(synthetic_input)
    except Exception:
        summary["error_code"] = "AGENT_PROVIDER_FAILED"
        return summary

    # Local adapter class to bridge Gemini provider to requirement pipeline
    class PromptProviderAdapter(RequirementAgentProvider):
        def __init__(self, prompt_provider):
            self.prompt_provider = prompt_provider

        def generate_draft(self, sanitized_input_env) -> str:
            prompt = requirement_agent_prompt.build_requirement_agent_prompt(sanitized_input_env)
            return self.prompt_provider.generate_draft_from_prompt(prompt)

    counting_client = None
    try:
        api_key = environ["GEMINI_API_KEY"]
        model_name = environ["GEMINI_MODEL_NAME"]

        if client_adapter_class:
            client = client_adapter_class(api_key=api_key)
        else:
            from app.gemini_sdk_client_adapter import GeminiSdkClientAdapter
            client = GeminiSdkClientAdapter(api_key=api_key)

        counting_client = CountingClientWrapper(client)
        provider = GeminiRequirementAgentProvider(client=counting_client, model_name=model_name)
        wrapper = PromptProviderAdapter(provider)

        result = run_requirement_agent_with_provider(sanitized_input, wrapper)

        summary["stage_status"] = result.status.name if hasattr(result.status, "name") else str(result.status)
        summary["error_code"] = result.error_code

        if result.status == StageStatus.SUCCESS:
            summary["committed_output_exists"] = result.committed_output is not None
            if result.committed_output and hasattr(result.committed_output, "requirements"):
                summary["requirement_count"] = len(result.committed_output.requirements)
        else:
            summary["committed_output_exists"] = False

    except Exception:
        summary["stage_status"] = "FAILED"
        summary["error_code"] = "AGENT_PROVIDER_FAILED"

    # Update actual generate_content calls using the wrapper
    if counting_client is not None:
        summary["request_count"] = counting_client.count
        summary["request_attempted"] = counting_client.count > 0

    return summary


def main():
    import os
    import sys
    import subprocess

    # Verify git status
    try:
        git_res = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            check=True
        )
        clean = is_git_status_clean(git_res.stdout)
        if clean:
            print("Initial git status: clean")
        else:
            print("Initial git status: dirty")
            print("Error: Git working tree is dirty. Execution aborted.")
            sys.exit(1)
    except Exception:
        print("Error: unable to check git status. Execution aborted.")
        sys.exit(1)

    def lazy_import_genai():
        from google import genai
        return genai

    print("Running first real request execution path...")
    summary = execute_request(os.environ, lazy_import_genai)

    print("\n--- Execution Summary ---")
    print(f"GEMINI_API_KEY present: {summary['api_key_present']}")
    print(f"GEMINI_MODEL_NAME present: {summary['model_name_present']}")
    print(f"Model configured: {summary['model_configured']}")
    print(f"SDK readiness via guarded path: {summary['sdk_readiness']}")
    print(f"Request attempted: {summary['request_attempted']}")
    print(f"Request count: {summary['request_count']}")
    print(f"StageResult.status: {summary['stage_status']}")
    print(f"StageResult.error_code: {summary['error_code']}")
    print(f"committed_output exists: {summary['committed_output_exists']}")
    print(f"Requirement count: {summary['requirement_count']}")
    print("-------------------------")

    try:
        git_res_final = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            check=True
        )
        final_clean = is_git_status_clean(git_res_final.stdout)
        if final_clean:
            print("\nFinal git status: clean")
        else:
            print("\nFinal git status: dirty")
    except Exception:
        print("\nError: unable to check git status.")


if __name__ == "__main__":
    main()
