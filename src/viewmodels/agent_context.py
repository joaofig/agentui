import os
from dataclasses import field
from typing import Any

from asyncer import asyncify
from dotenv import load_dotenv
from litellm import acompletion
from nicegui import binding

from models.agent import Agent
from models.agent_context import AgentContextModel
from src.viewmodels.view_model import ViewModel


@binding.bindable_dataclass
class AgentContextViewModel(ViewModel):
    prompt: str = ""
    response: str = "### Answer Panel \r\n \r\n"
    busy: bool = False
    enabled: bool = True
    messages: list[dict[str, str]] = field(default_factory=list)
    context = AgentContextModel()

    def __post_init__(self):
        super().__init__()

        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "your_default_api_key_here")
        self.api_url = os.getenv("OPENAI_API_URL", "https://hostyourai.com/api/v1")
        self.agent = Agent(
            model="openai/moonshotai/Kimi-K3",
            callback=self._add_content,
            api_key=self.api_key,
            api_url=self.api_url,
            system_prompt="""
                You are a helpful assistant that provides accurate and concise answers to user questions.
                You are precise and concise. Stay on topic.
            """
        )

    def _add_prompt_to_response(self, prompt: str) -> None:
        self.response += \
            '<div style="border:1px solid #ccc; padding:4px; border-radius:6px; font-weight: bold;' + \
            'background-color: antiquewhite">' + \
            prompt + \
            "</div><br/>"

    async def _send_prompt(self) -> None:
        self.busy = True
        self.enabled = False

        self._add_prompt_to_response(self.prompt)

        await self.agent.send_prompt(self.prompt)

        self.response += " \r\n \r\n ---  \r\n \r\n"

        self.prompt = ""
        self.enabled = True
        self.busy = False

    def _append_content(self, content: str) -> None:
        self.response += content

    async def _add_content(self, content: str) -> None:
        await asyncify(self._append_content)(content)

    async def _on_call(self, msg: str, **kwargs) -> Any:
        if msg == "send_prompt":
            return await self._send_prompt()
        return None