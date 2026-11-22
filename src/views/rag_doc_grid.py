from typing import Any

from nicegui import app, ui
from nicegui.elements.aggrid import AgGrid
from nicegui.observables import ObservableList
from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View

from src.viewmodels.rag_document import RagDocumentViewModel
from src.views.dialogs.rag_document_dialog import RagDocumentDialog


class RagDocumentGrid(View):
    def __init__(self, vm: ViewModel) -> None:
        """Build a selectable grid for the supplied document list.

        Args:
            vm: List view model providing document rows and selection state.
        """
        super().__init__(vm)

        self.documents = self.vm.get("documents")
        if isinstance(self.documents, ObservableList):
            self.documents.on_change(self._update_grid)

        self.grid = self._build_grid()

    def _build_grid(self) -> AgGrid:
        columns = [
            {
                "headerName": "Edit",
                "field": "rag_doc_id",
                "width": 50,
                ":cellRenderer": """
                (params) => {
                    const btn = document.createElement('button');
                    btn.innerText = '✏️';
                    btn.style.cssText = 'cursor:pointer; padding:2px 8px;';
                    btn.addEventListener('click', () => {
                        emitEvent('rag-document-row-edit', params.data);
                    });
                return btn;
                }
                """,
            },
            {
                "headerName": "Title",
                "field": "title",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
                "floatingFilter": False,
            },
            {
                "headerName": "File Name",
                "field": "file_name",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
                "floatingFilter": False,
            },
            {
                "headerName": "Language",
                "field": "language",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
                "floatingFilter": False,
            },
            {
                "headerName": "Organization ID",
                "field": "org_id",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
                "floatingFilter": False,
            },
            {
                "headerName": "Created On",
                "field": "created_on",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
                "floatingFilter": False,
            },
            {
                "headerName": "Updated On",
                "field": "updated_on",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
                "floatingFilter": False,
            },
        ]
        grid_def = {
            "columnDefs": columns,
            "rowData": self.documents,
            "rowSelection": {
                "mode": "singleRow",
                "checkboxes": False,
                "enableClickSelection": True,
            },
            ":getRowId": "(params) => String(params.data.rag_doc_id)",
        }
        ui.on("rag-document-row-edit", self._on_edit)

        grid = ui.aggrid(grid_def, theme="balham").classes("w-full h-full")
        grid.on("selectionChanged", lambda event: self._row_selection_changed(event))
        return grid

    async def _update_grid(self):
        await self.grid.run_grid_method("setGridOption", "rowData", self.documents)

        rag_doc_id = self.vm.get("selected_id")
        if rag_doc_id:
            await self.grid.run_row_method(str(rag_doc_id), "setSelected", True)

    async def _on_edit(self, event: Any) -> None:
        row_data = event.args
        if not row_data:
            return

        vm = RagDocumentViewModel()
        vm.updated_by = app.storage.user.get("username", "Unknown")
        await vm.call("load", rag_doc_id=row_data["rag_doc_id"])
        if not vm.rag_doc_id:
            ui.notify("The selected document could not be loaded.", type="negative")
            return

        dialog = RagDocumentDialog(vm)
        if await dialog.show() == "save":
            await self.vm.call("load", org_id=vm.org_id)

    async def _row_selection_changed(self, event: Any) -> None:
        row = await self.grid.get_selected_row()
        if row:
            await self.vm.call(
                "document_selected",
                document=row,
                rag_doc_id=row["rag_doc_id"],
                org_id=row["org_id"],
            )
        else:
            await self.vm.call(
                "document_selected",
                rag_doc_id=0,
                org_id=self.vm.get("org_id", 0),
            )
