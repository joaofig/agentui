from nicegui import ui
from nicemvvm.views.view import View

from src.viewmodels.skill import SkillViewModel
from src.viewmodels.skill_list import SkillListViewModel
from src.views.dialogs.delete_warning_dialog import DeleteWarningDialog
from src.views.dialogs.skill_dialog import SkillDialog
from src.views.skill_grid import SkillGrid


class SkillPanel(View):
    """Provide skill management controls and the skill grid."""

    def __init__(self, vm: SkillListViewModel) -> None:
        """Build the skill panel for the supplied list view model.

        Args:
            vm: List view model that backs the skill grid and actions.
        """
        super().__init__(vm)

        with ui.row().classes("w-full h-full"):
            with ui.column().classes("h-full flex-none"):
                with (
                    ui.button(icon="add", on_click=self._add_skill)
                    .classes("text-xs")
                    .props("padding=xs")
                ):
                    ui.tooltip("Add Skill")

                with (
                    ui.button(icon="delete", on_click=self._delete_skill)
                    .bind_enabled(vm, "delete_enabled")
                    .classes("text-xs")
                    .props("padding=xs color=red")
                ):
                    ui.tooltip("Delete Skill")

                with (
                    ui.button(icon="refresh", on_click=self._load_skills)
                    .classes("text-xs")
                    .props("padding=xs")
                ):
                    ui.tooltip("Refresh")

            with ui.column().classes("h-full flex-1"):
                self.grid = SkillGrid(vm)

    async def _add_skill(self) -> None:
        """Open a dialog to create a skill for the current organization."""
        vm = SkillViewModel(org_id=self.vm.get("org_id", 1))
        dialog = SkillDialog(vm)
        if await dialog.show() == "save":
            await self.vm.call("load", org_id=vm.org_id)

    async def _delete_skill(self) -> None:
        """Confirm and delete the selected skill."""
        skill_id = self.vm.get("selected_id")
        org_id = self.vm.get("org_id", 1)
        if not skill_id:
            ui.notify("Select a skill to delete.", type="negative")
            return

        dialog = DeleteWarningDialog("Are you sure you want to delete this skill?")
        if await dialog.show() == "delete":
            dialog.close()
            await self.vm.call("delete", skill_id=skill_id, org_id=org_id)

    async def _load_skills(self) -> None:
        """Reload skills for the current organization."""
        await self.vm.call("load", org_id=self.vm.get("org_id", 1))
