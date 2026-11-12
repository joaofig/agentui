from typing import cast, Any

from haystack.dataclasses import ChatMessage, ChatRole
from nicegui import ui
from nicegui.events import ScrollEventArguments, ObservableChangeEventArguments
from nicegui.observables import ObservableList
from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View


MD_EXTRAS = [
    "markdown-in-html",
    "tables",
    "latex",
    "fenced-code-blocks",
    "task-lists",
    "code-friendly",
    "footnotes",
    "mermaid",
]


class ChatThreadView(View):
    def __init__(self, vm: ViewModel, classes: str = ""):
        super().__init__(vm)

        self.thread_list = self.vm.get("thread")
        if isinstance(self.thread_list, ObservableList):
            self.thread_list.on_change(self._update_thread_list)

        self.thread = ui.scroll_area(on_scroll=self._on_thread_scroll).classes(classes)

    def _on_thread_scroll(self, e: ScrollEventArguments) -> None:
        pass

    def _update_thread_list(self, e: ObservableChangeEventArguments) -> None:
        # sender = e.sender
        self.thread.clear()

        with self.thread:
            for message in self.thread_list:
                chat_msg = cast(ChatMessage, message)
                match chat_msg.role:

                    case ChatRole.USER:
                        with ui.card():
                            ui.markdown(chat_msg.text or "", extras=MD_EXTRAS)

                    case ChatRole.ASSISTANT:
                        ui.markdown(chat_msg.text or "", extras=MD_EXTRAS)

            # This markdown is used to display the stream text, hidden when not used
            ui.markdown("", extras=MD_EXTRAS) \
                .bind_content_from(self.vm, "stream_text", backward=self._update_scroll) \
                .bind_visibility_from(self.vm, "stream_visible")
        self.thread.scroll_to(percent=1.0)

    def _update_scroll(self, a: Any) -> Any:
        if len(a) > 0:
            self.thread.scroll_to(percent=1.0)
        return a
