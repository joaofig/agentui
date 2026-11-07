from nicegui import ui, app

from nicemvvm.tools.user import logout
from src.views.agent_panel import AgentPanel
from src.viewmodels.agent_context import AgentContextViewModel
from src.views.admin.admin_panel import AdminPanel


class MainView:
    def __init__(self):
        user_role = app.storage.user.get("user_role", "User")

        with ui.column().classes("w-full h-screen"):
            with ui.tabs().props("dense no-caps") as tabs:
                agent = ui.tab("Agent").classes("text-sky-800")
                admin = ui.tab("Admin").classes("text-sky-800")

                # Only visible to Admin users
                admin.set_visibility(user_role == "Admin")

            with ui.row().classes("w-full flex-1 justify-end"):
                with ui.button(text="Logout", on_click=logout)\
                        .classes("text-xs mr-4 mt-2") \
                        .props("padding=xs"):
                    ui.tooltip("Log Out")

            with ui.tab_panels(tabs, value=agent, animated=False) \
                    .classes("h-full w-full"):

                with ui.tab_panel(agent).classes("pl-4 pt-0 pb-0 pr-4"):
                    agent_vm = AgentContextViewModel()
                    AgentPanel(agent_vm)

                with ui.tab_panel(admin).classes("pl-4 pt-0 pb-0 pr-4"):
                    if user_role == "Admin":
                        AdminPanel()
