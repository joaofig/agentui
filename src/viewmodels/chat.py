from typing import Any, cast

from haystack.dataclasses import StreamingChunk, ChatMessage, ChatRole
from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel

from services.chat_agent import ChatAgent


class ChatViewModel(ViewModel):

    def __init__(self):
        super().__init__()

        self.thread = GridList()
        self.prompt: str = ""
        self.chat_agent = ChatAgent()
        self.chat_agent.subscribe("stream_reply", self._on_stream_reply)
        self.chat_agent.subscribe("final_reply", self._on_final_reply)

    async def _on_call(self, msg: str, **kwargs) -> Any:
        match msg:
            case "ask":
                if self.prompt:
                    self.thread.append(ChatMessage.from_user(self.prompt))
                    await self.chat_agent.ask_async(self.prompt)
        return None

    async def _on_stream_reply(self, **kwargs):
        if "chunk" in kwargs:
            chunk = cast(StreamingChunk, kwargs["chunk"])
            if chunk:
                pass

    async def _on_final_reply(self, **kwargs):
        if "reply" in kwargs:
            reply = cast(ChatMessage, kwargs["reply"])
            if reply:
                self.thread.append(reply)
