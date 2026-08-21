from nicegui import ui

from src.viewmodels.view_model import ViewModel
from src.views.view import View


class MainView(View):
    def __init__(self, vm: ViewModel):
        super().__init__(vm)

        with ui.column().classes("w-full h-screen"):
            with ui.splitter(horizontal=True).classes("w-full h-full") as splitter:
                with splitter.before:
                    with ui.row().classes("w-full h-full"):
                        ui.markdown("", extras=["markdown-in-html"]).classes("h-full m-4") \
                            .bind_content_from(vm, "response")
                with splitter.after:
                    with ui.row().classes("w-full h-full"):
                        with ui.column().classes("flex-1 h-full"):
                            # .on("keydown.enter", self._send_prompt) \
                            ui.textarea("") \
                                .classes("w-full h-full pl-4 pr-4") \
                                .props("clearable autofocus hide-bottom-space dense borderless") \
                                .bind_value(vm, "prompt")

                        with ui.column().classes("flex-none h-full"):
                            ui.button("Submit", on_click=self._send_prompt) \
                                .classes("m-4")
                            ui.spinner(size="lg").bind_visibility_from(vm, "busy")

    async def _send_prompt(self):
        await self.vm.call("send_prompt")
