import os

from dataclasses import field
from typing import Any

from dotenv import load_dotenv
from nicegui import binding
from openai import AsyncOpenAI

from src.viewmodels.view_model import ViewModel


@binding.bindable_dataclass
class AgentViewModel(ViewModel):
    prompt: str = ""
    response: str = "### Answer Panel \r\n \r\n"
    busy: bool = False
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        super().__init__()

        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "your_default_api_key_here")
        self.api_url = os.getenv("OPENAI_API_URL", "https://hostyourai.com/api/v1")

    async def _send_prompt(self) -> None:
        self.busy = True

        self.messages.append({'role': 'user', 'content': self.prompt})

        async with AsyncOpenAI(base_url=self.api_url, api_key=self.api_key) as client:
            new_messages = [
                {
                    "role": "system",
                    "content": """
                        You are a helpful assistant that provides accurate and concise answers to user questions.
                        You are precise and concise. Stay on topic.
                    """
                },
                *self.messages
            ]
            stream = await client.chat.completions.create(
                model="qwen3-235b-a22b-instruct-2507",
                messages=new_messages,
                stream=True
            )
            assistant_message = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = str(chunk.choices[0].delta.content)
                    assistant_message += content
                    self.response += content
            assistant_message += " \r\n \r\n ---  \r\n \r\n"
            self.messages.append({'role': 'assistant', 'content': assistant_message})
            await stream.response.aclose()
        self.busy = False

    # async def _add_content(self, content: str) -> None:
    #     self.response += content

    async def _on_call(self, msg: str, **kwargs) -> Any:
        if msg == "send_prompt":
            return await self._send_prompt()
        return None