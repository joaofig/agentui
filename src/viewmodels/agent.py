import os
from dataclasses import field
from typing import Any

from dotenv import load_dotenv
from litellm import acompletion
from nicegui import binding

from src.viewmodels.view_model import ViewModel


@binding.bindable_dataclass
class AgentViewModel(ViewModel):
    prompt: str = ""
    response: str = "### Answer Panel \r\n \r\n"
    busy: bool = False
    enabled: bool = True
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        super().__init__()

        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "your_default_api_key_here")
        self.api_url = os.getenv("OPENAI_API_URL", "https://hostyourai.com/api/v1")

    async def _send_prompt(self) -> None:
        self.busy = True
        self.enabled = False

        prompt = self.prompt
        self.prompt = ""
        self.messages.append({'role': 'user', 'content': prompt})

        assistant_message = \
            '<div style="border:1px solid #ccc; padding:4px; border-radius:6px; font-weight: bold;' + \
            'background-color: antiquewhite">' + \
            prompt + \
            "</div><br/>"
        self.response += assistant_message

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
        response = await acompletion(
            model="openai/Qwen/Qwen3.5-397B-A17B",
            messages=new_messages,
            base_url=self.api_url,
            api_key=self.api_key
        )
        content = response.choices[0].message.content
        if content:
            assistant_message += content
            self.response += content

            assistant_message += " \r\n \r\n ---  \r\n \r\n"
            self.messages.append({'role': 'assistant', 'content': assistant_message})

        self.enabled = True
        self.busy = False

    # async def _add_content(self, content: str) -> None:
    #     self.response += content

    async def _on_call(self, msg: str, **kwargs) -> Any:
        if msg == "send_prompt":
            return await self._send_prompt()
        return None