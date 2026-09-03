import os
from dataclasses import field
from typing import Any

import openai
from asyncer import asyncify
from dotenv import load_dotenv
from nicegui import binding
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage, StreamingChunk
from src.viewmodels.view_model import ViewModel


@binding.bindable_dataclass
class AgentContextViewModel(ViewModel):
    prompt: str = ""
    response: str = "### Answer Panel \r\n \r\n"
    busy: bool = False
    enabled: bool = True
    messages: list[ChatMessage] = field(default_factory=list)

    def __post_init__(self):
        super().__init__()

        load_dotenv()
        self.api_url = os.getenv("OPENAI_API_URL", "https://hostyourai.com/api/v1")
        self.chat_generator = OpenAIChatGenerator(
            model="moonshotai/Kimi-K3",
            api_base_url=self.api_url,
        )
        system_prompt = """
            You are a helpful assistant that provides accurate and concise answers to user questions.
            You are precise and concise. Stay on topic.
        """
        self.agent = Agent(
            chat_generator=self.chat_generator,
            system_prompt=system_prompt,
            streaming_callback=self._add_content
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
        self.messages.append(ChatMessage.from_user(self.prompt))

        try:
            result = await self.agent.run_async(self.messages)
            self.messages.extend(result["messages"])
        except openai.APIError as e:
            self.response += f"<div style='color: red;'>{e}</div>"
        finally:
            self.response += "<br /><br />"

        self.prompt = ""
        self.enabled = True
        self.busy = False

    def _append_content(self, content: StreamingChunk) -> None:
        self.response += content.content

    async def _add_content(self, content: StreamingChunk) -> None:
        await asyncify(self._append_content)(content)

    async def _on_call(self, msg: str, **kwargs) -> Any:
        if msg == "send_prompt":
            return await self._send_prompt()
        return None