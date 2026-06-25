# No module-level imports of google.genai or google.auth are allowed.
# No module-level env var reads or executable statements.

def check_sdk_and_key(environ, import_genai) -> tuple[bool, str]:
    """Helper to verify environment readiness safely without printing credentials."""
    if "GEMINI_API_KEY" not in environ:
        return False, "Error: GEMINI_API_KEY environment variable is not set. Real Gemini execution is blocked."

    try:
        import_genai()
    except ImportError:
        return False, "google.genai SDK is not installed in the environment."

    return True, ""


def main():
    # Executed strictly when running scripts manually, not during automated tests.
    import os

    def lazy_import_genai():
        from google import genai
        return genai

    ready, error_msg = check_sdk_and_key(os.environ, lazy_import_genai)
    if not ready:
        print(error_msg)
        return

    # Real execution checks are deferred to execution gate approval
    print("Smoke test environment check completed successfully.")


if __name__ == "__main__":
    main()
