import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import List

from dotenv import load_dotenv
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage, ChatRole, StreamingChunk
from haystack.utils import Secret
from nicemvvm.tools.messenger import Messenger

from src.services.mojeek_search import create_mojeek_search_tool

SYSTEM_PROMPT = """
You are a deep research assistant.
You create comprehensive research reports to answer the user's questions.
You use the 'web_search' tool to answer any questions about topics you don't know about.
You perform multiple searches until you have the information you need to answer the question.
Make sure you research different aspects of the question.
Use markdown to format your response.
When you use information from the websearch results, cite your sources using markdown links.
It is important that you cite accurately.
"""


class ChatAgent:
    def __init__(self):
        load_dotenv()
        self.messenger = Messenger()
        self.messages = [ChatMessage.from_system(SYSTEM_PROMPT)]
        self.task: asyncio.Task | None = None
        self.partial: List[str] = []

        web_search = create_mojeek_search_tool(
            top_k=5,
            search_params={"lb": "EN", "lbb": 100, "dlen": 300},
            # allowed_domains=[".daimlertruck.com"],   # optional, max 25
            raise_on_failure=False,  # agent gets "No results found." instead of a crash
        )

        chat_generator = OpenAIChatGenerator(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model=os.getenv("AGENT_CHAT_MODEL") or "Qwen/Qwen3.8-27B",
            api_base_url=os.getenv("OPENAI_API_URL"),
            streaming_callback=self._streaming_callback,
        )
        self.agent = Agent(
            chat_generator=chat_generator,
            tools=[web_search],
            # max_agent_steps=10,
        )
        self.agent.warm_up()

    async def _streaming_callback(self, chunk: StreamingChunk) -> None:
        if chunk.content:
            self.partial.append(chunk.content)
        await self.messenger.broadcast("stream_reply", chunk=chunk)

    def subscribe(
        self, message: str, handler: Callable[..., None | Awaitable[None]]
    ) -> None:
        self.messenger.subscribe(message, handler)

    async def ask_async(self, prompt: str) -> None:
        user_msg = ChatMessage.from_user(prompt)
        self.messages.append(user_msg)
        self.partial.clear()
        self.task = asyncio.create_task(self.agent.run_async(messages=self.messages))

        try:
            if self.task:
                result = await self.task

                # result["messages"] holds the full turn: user msg, tool calls,
                # tool results and the final reply. Drop the system message, since
                # the Agent re-adds system_prompt on every run.
                self.messages = [
                    m for m in result["messages"] if not m.is_from(ChatRole.SYSTEM)
                ]

                await self.messenger.broadcast("reply", reply=self.messages[-1])

        except asyncio.CancelledError:
            cancel_message = ChatMessage.from_assistant(text="User interrupted.")
            await self.messenger.broadcast("reply", reply=cancel_message)

        # Keep the REPL alive on API/tool errors
        except Exception:  # noqa: BLE001
            self.messages.pop()

    def stop(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()