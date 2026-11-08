from nicegui import ui
from asyncer import asyncify

from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View


class AgentView(View):
    _md_bound: bool = False

    def __init__(self, vm: ViewModel):
        super().__init__(vm)

        with ui.column().classes("w-full h-full"):
            with ui.splitter(horizontal=True, value=70).classes("w-full h-full") as splitter:
                with splitter.before, ui.row().classes("w-full h-full"):
                    self.chat_thread = ui.column().classes("w-full h-full")
                    # extras = [
                    #     "markdown-in-html",
                    #     "tables",
                    #     "latex",
                    #     "fenced-code-blocks",
                    #     "task-lists",
                    #     "code-friendly",
                    #     "footnotes"]
                    # self.md = ui.markdown("", extras=extras).classes("h-full m-4") \
                    #     .bind_content_from(self.vm, "response",
                    #                        backward=lambda text: self._update_md(text))

                with splitter.after:
                    with ui.row().classes("w-full h-full"):
                        with ui.column().classes("flex-1 h-full"):
                            ui.textarea("") \
                                .on("keydown.enter", self._send_prompt) \
                                .classes("w-full h-full pl-4 pr-4") \
                                .props("clearable autofocus hide-bottom-space dense borderless") \
                                .bind_value(vm, "prompt") \
                                .bind_enabled_from(vm, "enabled")

                        with ui.column().classes("flex-none"):
                            ui.button("Submit", on_click=self._send_prompt) \
                                .classes("m-4")
                            ui.spinner(size="lg").bind_visibility_from(vm, "busy")

    async def _send_prompt(self):
        if not self._md_bound:
            self._md_bound = True
        await self.vm.call("send_prompt")

    async def _scroll_md(self):
        md = self.md
        await ui.run_javascript(f'getHtmlElement({md.id}).scrollTop=getHtmlElement({md.id}).scrollHeight')

    def _update_md(self, text: str) -> str:
        if self._md_bound:
            asyncify(self._scroll_md)
        return text
