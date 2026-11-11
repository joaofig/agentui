import os
from typing import Callable, Awaitable

from dotenv import load_dotenv
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import StreamingChunk, ChatMessage, ChatRole
from haystack.utils import Secret

from nicemvvm.tools.messenger import Messenger


SYSTEM_PROMPT = """
You are a helpful assistant.
"""


class ChatAgent:
    def __init__(self):
        load_dotenv()
        self.messenger = Messenger()
        self.messages = [ChatMessage.from_system(SYSTEM_PROMPT)]

        chat_generator = OpenAIChatGenerator(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model=os.getenv("AGENT_CHAT_MODEL") or "Qwen/Qwen3.8-27B",
            api_base_url=os.getenv("OPENAI_API_URL"),
            streaming_callback=self._streaming_callback
        )
        self.agent = Agent(chat_generator=chat_generator)
        self.agent.warm_up()

    async def _streaming_callback(self, chunk: StreamingChunk) -> None:
        await self.messenger.broadcast("stream_reply", chunk=chunk)

    def subscribe(
        self, message: str, handler: Callable[..., None | Awaitable[None]]
    ) -> None:
        self.messenger.subscribe(message, handler)

    async def ask_async(self, prompt: str) -> None:
        user_msg = ChatMessage.from_user(prompt)
        self.messages.append(user_msg)

        try:
            result = await self.agent.run_async(messages=self.messages)

            # result["messages"] holds the full turn: user msg, tool calls,
            # tool results and the final reply. Drop the system message, since
            # the Agent re-adds system_prompt on every run.
            self.messages = [m for m in result["messages"] if not m.is_from(ChatRole.SYSTEM)]

            await self.messenger.broadcast("reply", result=self.messages[-1])

        except Exception as exc:  # noqa: BLE001  # keep the REPL alive on API/tool errors
            self.messages.pop()


