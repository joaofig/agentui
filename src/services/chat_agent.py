import os

from dotenv import load_dotenv
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import StreamingChunk
from haystack.utils import Secret

from nicemvvm.tools.messenger import Messenger


class ChatAgent:
    def __init__(self):
        load_dotenv()
        self.messenger = Messenger()

        chat_generator = OpenAIChatGenerator(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model=os.getenv("AGENT_CHAT_MODEL") or "Qwen/Qwen3.8-27B",
            api_base_url=os.getenv("OPENAI_API_URL"),
            streaming_callback=self._streaming_callback
        )
        self.agent = Agent(chat_generator=chat_generator)
        self.agent.warm_up()

    def _streaming_callback(self, chunk: StreamingChunk) -> None:
        pass
