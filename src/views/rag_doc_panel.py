from nicegui import app, ui
from nicemvvm.tools.excel import export_to_excel
from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View

from src.viewmodels.rag_document import RagDocumentViewModel
from src.views.dialogs.delete_warning_dialog import DeleteWarningDialog
from src.views.dialogs.rag_document_dialog import RagDocumentDialog
from src.views.rag_doc_grid import RagDocumentGrid


class RagDocumentPanel(View):
    def __init__(self, vm: ViewModel) -> None:
        """Build the document panel and its organization-scoped controls.

        Args:
            vm: List view model for the document grid and actions.
        """
        super().__init__(vm)

        with ui.row().classes("w-full h-full"):
            with ui.column().classes("h-full flex-none"):
                with (
                    ui.button(icon="add", on_click=self._add_document)
                    .classes("text-xs")
                    .props("padding=xs")
                ):
                    ui.tooltip("Add Document")

                with (
                    ui.button(icon="delete", on_click=self._on_delete_document)
                    .bind_enabled(vm, "delete_enabled")
                    .classes("text-xs")
                    .props("padding=xs color=red")
                ):
                    ui.tooltip("Delete Document")

                with (
                    ui.button(icon="table_view", on_click=self._on_export_to_excel)
                    .classes("text-xs")
                    .props("padding=xs")
                ):
                    ui.tooltip("Export to Excel")

                with (
                    ui.button(icon="refresh", on_click=self._on_load_documents)
                    .classes("text-xs")
                    .props("padding=xs")
                ):
                    ui.tooltip("Refresh")

            with ui.column().classes("h-full flex-1"):
                self.grid = RagDocumentGrid(vm)

    async def _on_delete_document(self):
        rag_doc_id = self.vm.get("selected_id")
        org_id = self.vm.get("org_id", 0)
        if not rag_doc_id or not org_id:
            ui.notify("Select a document to delete.", type="negative")
            return

        dialog = DeleteWarningDialog("Are you sure you want to delete this document?")
        result = await dialog.show()
        if result == "delete":
            dialog.close()
            await self.vm.call("delete", rag_doc_id=rag_doc_id, org_id=org_id)

    async def _add_document(self):
        vm = RagDocumentViewModel()
        vm.org_id = self.vm.get("org_id", 0)
        vm.created_by = app.storage.user.get("username", "Unknown")
        vm.updated_by = app.storage.user.get("username", "Unknown")

        dialog = RagDocumentDialog(vm)
        result = await dialog.show()
        if result == "save":
            await self.vm.call("load", org_id=vm.org_id)

    async def _on_load_documents(self) -> None:
        try:
            org_id = int(self.vm.get("org_id", 1))
        except TypeError, ValueError, OverflowError:
            org_id = 1
        if not org_id.is_integer() or org_id < 1:
            ui.notify("A valid organization ID is required.", type="negative")
            return
        await self.vm.call("load", org_id=int(org_id))

    def _on_export_to_excel(self):
        documents = [r.to_dict() for r in self.vm.get("documents")]
        if documents:
            export_to_excel(documents, filename="documents.xlsx")
