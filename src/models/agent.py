import os
from typing import Callable, Awaitable

from dotenv import load_dotenv
from litellm import acompletion


class Agent:
    def __init__(self,
                 model: str,
                 callback: Callable[[str], Awaitable[None]],
                 api_key: str = "",
                 api_url: str = "",
                 system_prompt: str = ""):
        load_dotenv()
        self.model = model

        self.api_key = api_key if len(api_key) else os.getenv("OPENAI_API_KEY", "")
        self.api_url = api_url if len(api_url) else os.getenv("OPENAI_API_URL", "")
        self.callback = callback
        self.system_prompt = system_prompt
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        if not len(self.api_key):
            raise ValueError("API key is required")
        if not len(self.api_url):
            raise ValueError("API URL is required")

    async def send_prompt(self, prompt: str) -> None:
        self.messages.append({'role': 'user', 'content': prompt})

        response = await acompletion(
            model=self.model,
            messages=self.messages,
            base_url=self.api_url,
            api_key=self.api_key,
            stream=True
        )

        content = ""
        try:
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    delta = str(chunk.choices[0].delta.content)
                    content += delta
                    await self.callback(delta)

        finally:
            aclose = getattr(response, "aclose", None)
            if aclose is not None:
                await aclose()

        self.messages.append({"role": "assistant", "content": content})

        # content = response.choices[0].message.content
        # if content:
        #     self.messages.append({"role": "assistant", "content": content})
        #     result = self.callback(content=content)
        #     if inspect.isawaitable(result):
        #         await result
