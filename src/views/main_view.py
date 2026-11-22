from nicegui import app, ui
from nicemvvm.tools.user import logout

from src.viewmodels.chat import ChatViewModel
from src.viewmodels.rag_document_list import RagDocumentListViewModel
from src.views.admin.admin_panel import AdminPanel
from src.views.chat_panel import ChatPanel
from src.views.rag_doc_panel import RagDocumentPanel


class MainView:
    """Build the main application tabs and their views."""

    def __init__(self) -> None:
        """Create the main screen for the current user's role."""
        user_role = app.storage.user.get("user_role", "User")

        with ui.column().classes("w-full h-screen"):
            with ui.row().classes("w-full flex-1"):
                with ui.tabs().props("dense no-caps") as tabs:
                    agent = ui.tab("Agent").classes("text-sky-800")
                    documents = ui.tab("Documents").classes("text-sky-800")
                    admin = ui.tab("Admin").classes("text-sky-800")

                    # Only visible to Admin users
                    admin.set_visibility(user_role == "Admin")

                with (
                    ui.row().classes("w-full flex-1 justify-end"),
                    (
                        ui.button(text="Logout", on_click=logout)
                        .classes("text-xs mr-4 mt-2")
                        .props("padding=xs")
                    ),
                ):
                    ui.tooltip("Log Out")

            with ui.tab_panels(tabs, value=agent, animated=False).classes(
                "h-full w-full"
            ):
                with ui.tab_panel(agent).classes("pl-4 pt-0 pb-0 pr-4"):
                    chat_vm = ChatViewModel()
                    ChatPanel(chat_vm)

                with ui.tab_panel(documents).classes("pl-4 pt-0 pb-0 pr-4"):
                    rag_doc_list_vm = RagDocumentListViewModel()
                    RagDocumentPanel(rag_doc_list_vm)

                with ui.tab_panel(admin).classes("pl-4 pt-0 pb-0 pr-4"):
                    if user_role == "Admin":
                        AdminPanel()
