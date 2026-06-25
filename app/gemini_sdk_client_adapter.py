class GeminiSdkClientAdapter:
    """Adapter wrapping the Google GenAI SDK client to expose a standard text generation contract."""

    def __init__(self, api_key: str = None, client = None):
        self._api_key = api_key
        self._client = client

    def _get_client(self):
        if self._client is None:
            # Lazy import inside method call to maintain import isolation
            from google import genai
            if self._api_key:
                self._client = genai.Client(api_key=self._api_key)
            else:
                self._client = genai.Client()
        return self._client

    def generate_content(self, model_name: str, prompt: str) -> object:
        """Invokes the GenAI SDK client to generate content.

        Propagates client exceptions (TimeoutError, API errors) to the provider.
        """
        client = self._get_client()
        # Direct call to models.generate_content for the client object.
        # Timeout configuration will be verified and added later when SDK API parameters are confirmed.
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response
