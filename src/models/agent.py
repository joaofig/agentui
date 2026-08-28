import os


class Agent:
    def __init__(self,
                 model: str,
                 api_key: str = "",
                 api_url: str = ""):
        self.model = model
        self.messages = []
        self.api_key = api_key if len(api_key) else os.getenv("OPENAI_API_KEY", "")
        self.api_url = api_url if len(api_url) else os.getenv("OPENAI_API_URL", "")

        if not len(self.api_key):
            raise ValueError("API key is required")
        if not len(self.api_url):
            raise ValueError("API URL is required")
