class GeminiRequirementAgentProvider:
    """Boundary wrapper that invokes an injected SDK-free Gemini client using prompt texts."""

    def __init__(self, client, model_name: str = "gemini-1.5-flash"):
        self.client = client
        self.model_name = model_name

    def generate_draft_from_prompt(self, prompt: str) -> str:
        """Invokes the injected client to generate candidate draft JSON.

        Preserves raw text exactly as the model/client produced it.
        """
        if self.client is None:
            raise ValueError("Injected Gemini client is missing.")

        # Call the injected client contract: client.generate_content(model_name, prompt)
        response = self.client.generate_content(self.model_name, prompt)

        if response is None:
            raise ValueError("Response object is None.")

        # 1. Validate response object has text attribute
        if not hasattr(response, "text"):
            raise ValueError("Response object is missing the required 'text' attribute.")

        text_content = response.text

        # 2. Return empty string for None/empty/whitespace responses
        if text_content is None or (isinstance(text_content, str) and not text_content.strip()):
            return ""

        # 3. Raise ValueError for non-string responses
        if not isinstance(text_content, str):
            raise ValueError(f"Expected response 'text' to be string, got {type(text_content).__name__}")

        # 4. Return raw text exactly (no markdown stripping, no JSON extraction)
        return text_content
