from typing import Any, cast

from haystack.dataclasses import StreamingChunk, ChatMessage, ChatRole
from nicegui import binding
from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel

from services.chat_agent import ChatAgent


@binding.bindable_dataclass
class ChatViewModel(ViewModel):

    def __init__(self):
        super().__init__()

        self.thread = GridList()
        self.prompt: str = ""
        self.stream_text: str = ""
        self.stream_visible: bool = False
        self.chat_agent = ChatAgent()
        self.chat_agent.subscribe("stream_reply", self._on_stream_reply)
        self.chat_agent.subscribe("reply", self._on_final_reply)
        self.enabled: bool = True
        self.busy: bool = False

    async def _on_call(self, msg: str, **kwargs) -> Any:
        match msg:
            case "ask":
                if self.prompt:
                    self.enabled = False
                    self.busy = True
                    self.stream_text = ""
                    self.stream_visible = True
                    self.thread.append(ChatMessage.from_user(self.prompt))
                    await self.chat_agent.ask_async(self.prompt)
        return None

    async def _on_stream_reply(self, **kwargs):
        # print(kwargs)
        if "chunk" in kwargs:
            chunk = cast(StreamingChunk, kwargs["chunk"])
            if chunk:
                self.stream_text += chunk.content
                self.stream_visible = True

    async def _on_final_reply(self, **kwargs):
        if "reply" in kwargs:
            reply = cast(ChatMessage, kwargs["reply"])
            if reply:
                self.thread.append(reply)
        self.prompt = ""
        self.enabled = True
        self.busy = False
        self.stream_text = ""
        self.stream_visible = False
