from nicegui import ui
from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View

from views.thread_view import ChatThreadView


class ChatView(View):
    # _md_bound: bool = False

    def __init__(self, vm: ViewModel):
        super().__init__(vm)

        with (
            ui.column().classes("w-full h-full"),
            ui.splitter(horizontal=True, value=80).classes("w-full h-full") as splitter,
        ):
            with splitter.before, ui.row().classes("w-full h-full"):
                self.chat_thread = ChatThreadView(vm, "w-full h-full")

            with splitter.after, ui.row().classes("w-full h-full"):
                with ui.column().classes("flex-1 h-full"):
                    ui.textarea("").classes("w-full h-full").on(
                        "keydown.enter", self._send_prompt
                    ).props("clearable autofocus").bind_value(
                        vm, "prompt"
                    ).bind_enabled_from(vm, "enabled")
                # .props("clearable autofocus hide-bottom-space dense borderless") \
                with ui.column().classes("flex-none"):
                    ui.button("Submit", on_click=self._send_prompt).classes("m-4")
                    ui.spinner(size="lg").bind_visibility_from(vm, "busy")

    async def _send_prompt(self):
        await self.vm.call("ask")
