from nicegui import ui
from nicemvvm.views.view import View

from src.viewmodels.skill import SkillViewModel


class SkillDialog(View):
    """Dialog for creating or editing an individual skill."""

    def __init__(self, vm: SkillViewModel) -> None:
        """Build the skill editor and bind its fields to the view model.

        Args:
            vm: Skill view model that backs the dialog fields.
        """
        super().__init__(vm)

        with ui.dialog() as dialog, ui.card().classes("w-120"):
            with ui.row().classes("w-full bg-gray-200 p-2"):
                ui.label("Skill Details").classes("text-base")

            ui.input(label="Name").classes("w-full").props("dense").bind_value(
                vm, "name"
            )
            ui.textarea(label="Description").classes("w-full").props(
                "dense"
            ).bind_value(vm, "description")
            ui.textarea(label="Instructions").classes("w-full").props(
                "dense"
            ).bind_value(vm, "instructions")
            ui.number(label="Version", min=0, step=1).classes("w-full").props(
                "dense"
            ).bind_value(vm, "version")
            ui.checkbox(text="Enabled").bind_value(vm, "enabled")

            with ui.row():
                ui.button("Save", on_click=self.save).props("no-caps")
                ui.button("Cancel", on_click=lambda: dialog.submit("cancel")).props(
                    "no-caps"
                )
            self.dialog = dialog

    async def save(self) -> None:
        """Validate skill fields, persist the skill, and close on success."""
        name = self.vm.get("name", "").strip()
        if not name:
            ui.notify("Name is required.", type="negative")
            return

        try:
            version = float(self.vm.get("version", 0))
            org_id = int(self.vm.get("org_id", 0))
        except TypeError, ValueError, OverflowError:
            ui.notify("A valid version and organization are required.", type="negative")
            return
        if not version.is_integer() or version < 0 or org_id < 1:
            ui.notify("A valid version and organization are required.", type="negative")
            return

        self.vm.set("name", name)
        self.vm.set("version", int(version))
        try:
            await self.vm.call("save")
        except Exception as ex:
            ui.notify(f"The skill could not be saved: {ex}", type="negative")
            return
        self.dialog.submit("save")

    async def show(self) -> str | None:
        """Display the dialog and return the submitted action.

        Returns:
            The submitted action, or None if the dialog was dismissed.
        """
        return await self.dialog
