from typing import Any

from nicegui import ui
from nicegui.elements.aggrid import AgGrid
from nicegui.observables import ObservableList
from nicemvvm.views.view import View

from src.viewmodels.skill import SkillViewModel
from src.viewmodels.skill_list import SkillListViewModel
from src.views.dialogs.skill_dialog import SkillDialog


class SkillGrid(View):
    """Display organization skills and open selected skills for editing."""

    def __init__(self, vm: SkillListViewModel) -> None:
        """Build a selectable grid for the supplied skill list.

        Args:
            vm: List view model providing skill rows and selection state.
        """
        super().__init__(vm)

        self.skills = self.vm.get("skills")
        if isinstance(self.skills, ObservableList):
            self.skills.on_change(self._update_grid)

        self.grid = self._build_grid()

    def _build_grid(self) -> AgGrid:
        """Create the skill grid and connect its selection and edit events.

        Returns:
            The configured skill grid.
        """
        columns = [
            {
                "headerName": "Edit",
                "field": "skill_id",
                "width": 50,
                ":cellRenderer": """
                (params) => {
                    const btn = document.createElement('button');
                    btn.innerText = '✏️';
                    btn.style.cssText = 'cursor:pointer; padding:2px 8px;';
                    btn.addEventListener('click', () => {
                        emitEvent('skill-row-edit', params.data);
                    });
                    return btn;
                }
                """,
            },
            {
                "headerName": "Name",
                "field": "name",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
            },
            {
                "headerName": "Description",
                "field": "description",
                "sortable": True,
                "align": "left",
                "filter": "agTextColumnFilter",
            },
            {
                "headerName": "Enabled",
                "field": "enabled",
                "sortable": True,
                "filter": "agSetColumnFilter",
            },
            {
                "headerName": "Version",
                "field": "version",
                "sortable": True,
            },
            {
                "headerName": "Created On",
                "field": "created_on",
                "sortable": True,
            },
            {
                "headerName": "Updated On",
                "field": "updated_on",
                "sortable": True,
            },
        ]
        grid_def = {
            "columnDefs": columns,
            "rowData": self.skills,
            "rowSelection": {
                "mode": "singleRow",
                "checkboxes": False,
                "enableClickSelection": True,
            },
            ":getRowId": "(params) => String(params.data.skill_id)",
        }
        ui.on("skill-row-edit", self._on_edit)

        grid = ui.aggrid(grid_def, theme="balham").classes("w-full h-full")
        grid.on("selectionChanged", self._row_selection_changed)
        return grid

    async def _update_grid(self) -> None:
        """Refresh grid rows and restore the current selection."""
        await self.grid.run_grid_method("setGridOption", "rowData", self.skills)

        skill_id = self.vm.get("selected_id")
        if skill_id:
            await self.grid.run_row_method(str(skill_id), "setSelected", True)

    async def _on_edit(self, event: Any) -> None:
        """Load and display the skill associated with an edit-button event.

        Args:
            event: NiceGUI event containing the selected skill row.
        """
        row_data = event.args
        if not isinstance(row_data, dict):
            return

        try:
            org_id = int(row_data["org_id"])
            skill_id = int(row_data["skill_id"])
            name = str(row_data["name"])
        except KeyError, TypeError, ValueError:
            ui.notify("The selected skill could not be loaded.", type="negative")
            return

        vm = SkillViewModel(org_id=org_id)
        await vm.call("load", org_id=org_id, name=name)
        if vm.skill_id != skill_id:
            ui.notify("The selected skill could not be loaded.", type="negative")
            return

        dialog = SkillDialog(vm)
        if await dialog.show() == "save":
            await self.vm.call("load", org_id=org_id)

    async def _row_selection_changed(self, event: Any) -> None:
        """Update list-view-model selection after a grid selection change.

        Args:
            event: Grid selection event.
        """
        row = await self.grid.get_selected_row()
        if row:
            await self.vm.call(
                "skill_selected",
                skill_id=row["skill_id"],
                org_id=row["org_id"],
            )
        else:
            await self.vm.call(
                "skill_selected",
                skill_id=0,
                org_id=self.vm.get("org_id", 1),
            )
