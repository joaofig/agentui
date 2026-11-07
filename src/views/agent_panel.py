from nicegui import ui

from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View
from src.views.agent_view import AgentView


class AgentPanel(View):
    def __init__(self, vm: ViewModel):
        super().__init__(vm)

        with ui.row().classes("w-full h-full"):
            with ui.column().classes("flex-none"):
                with ui.button("New", icon="add") \
                        .classes("text-xs") \
                        .props("no-caps"):
                    ui.tooltip("New Session")

            with ui.column().classes("h-full flex-1"):
                AgentView(vm)