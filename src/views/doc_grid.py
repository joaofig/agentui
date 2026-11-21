from nicegui import ui
from nicegui.elements.aggrid import AgGrid
from nicegui.observables import ObservableList
from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View


class DocumentGrid(View):
    def __init__(self, vm: ViewModel):
        super().__init__(vm)

        self.users = self.vm.get("users")
        if isinstance(self.users, ObservableList):
            self.users.on_change(self._update_grid)

        self.grid = self._build_grid()

    def _build_grid(self) -> AgGrid:
        columns = [
            {
                "headerName": "Edit",
                "field": "user_id",
                "width": 50,
                ":cellRenderer": """
                (params) => {
                    const btn = document.createElement('button');
                    btn.innerText = '✏️';
                    btn.style.cssText = 'cursor:pointer; padding:2px 8px;';
                    btn.addEventListener('click', () => {
                        emitEvent('user-row-edit', params.data);
                    });
                return btn;
                }
                """,
            },
            {
                "headerName": "User Name", "field": "user_name", "sortable": True, "align": "left",
                "filter": "agTextColumnFilter", "floatingFilter": False,
            },
            {
                "headerName": "Role", "field": "user_role", "sortable": True, "align": "left",
                "filter": "agTextColumnFilter", "floatingFilter": False,
            },
            {
                "headerName": "Created At", "field": "created_at", "sortable": True, "align": "left",
                "filter": "agTextColumnFilter", "floatingFilter": False,
            },
            {
                "headerName": "Created By", "field": "created_by", "sortable": True, "align": "left",
                "filter": "agTextColumnFilter", "floatingFilter": False,
            },
            {
                "headerName": "Updated At", "field": "updated_at", "sortable": True, "align": "left",
                "filter": "agTextColumnFilter", "floatingFilter": False,
            },
            {
                "headerName": "Updated By", "field": "updated_by", "sortable": True, "align": "left",
                "filter": "agTextColumnFilter", "floatingFilter": False,
            },
        ]
        grid_def = {
            "columnDefs": columns,
            "rowData": self.users,
            "rowSelection": {
                "mode": "singleRow",
                "checkboxes": False,
                "enableClickSelection": True,
            },
            ":getRowId": "(params) => String(params.data.user_id)",
        }
        ui.on("user-row-edit", self._on_edit)

        grid = ui.aggrid(grid_def, theme="balham").classes("w-full h-full")
        grid.on("selectionChanged", lambda event: self._row_selection_changed(event))
        return grid

    async def _update_grid(self):
        pass

    async def _row_selection_changed(self, event):
        row = await self.grid.get_selected_row()
        if row:
            await self.vm.call("document_selected", user=row, user_id=row["document_id"])
