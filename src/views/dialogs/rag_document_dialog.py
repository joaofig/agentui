from pathlib import Path

from nicegui import events, ui
from nicemvvm.viewmodels.view_model import ViewModel
from nicemvvm.views.view import View

from src.services.document_thumbnail import OFFICE_EXTENSIONS

DOCUMENT_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    **{
        extension: content_type for content_type, extension in OFFICE_EXTENSIONS.items()
    },
}
SUPPORTED_FILE_EXTENSIONS = tuple(sorted(DOCUMENT_CONTENT_TYPES))


class RagDocumentDialog(View):
    """Dialog for creating or editing a RAG document."""

    def __init__(self, vm: ViewModel) -> None:
        """Build the document editor and connect it to the supplied view model.

        Args:
            vm: Document view model that backs the dialog fields.
        """
        super().__init__(vm)

        with ui.dialog() as dialog, ui.card().classes("w-120"):
            with ui.row().classes("w-full bg-gray-200 p-2"):
                ui.label("Document Details").classes("text-base")

            ui.input(label="Title").classes("w-full").props("dense").bind_value(
                vm, "title"
            )
            ui.input(label="Description").classes("w-full").props("dense").bind_value(
                vm, "description"
            )
            ui.input(label="Language").classes("w-full").props("dense").bind_value(
                vm, "language"
            )

            file_name = self.vm.get("file_name", "")
            self.file_label = ui.label(
                f"Selected document: {file_name}"
                if file_name
                else "No document selected"
            ).classes("text-sm")
            ui.upload(
                label="Upload document",
                on_upload=self._on_upload,
                auto_upload=True,
                multiple=False,
            ).props(f"accept={','.join(SUPPORTED_FILE_EXTENSIONS)}").classes("w-full")

            with ui.row():
                ui.button("Save", on_click=self.save).props("no-caps")
                ui.button("Cancel", on_click=lambda: dialog.submit("cancel")).props(
                    "no-caps"
                )
            self.dialog = dialog

    @staticmethod
    def _content_type_for_filename(filename: str) -> str | None:
        """Return the canonical thumbnail media type for a supported filename.

        Args:
            filename: Name of the selected document.

        Returns:
            The canonical media type, or None when the extension is unsupported.
        """
        return DOCUMENT_CONTENT_TYPES.get(Path(filename).suffix.lower())

    async def _on_upload(self, event: events.UploadEventArguments) -> None:
        """Read a supported upload without replacing document data on error.

        Args:
            event: NiceGUI upload event containing the uploaded file.
        """
        content_type = self._content_type_for_filename(event.file.name)
        if content_type is None:
            ui.notify("Unsupported document type.", type="negative")
            return

        try:
            content = await event.file.read()
        except Exception:
            ui.notify("The uploaded document could not be read.", type="negative")
            return
        if not content:
            ui.notify("The uploaded document is empty.", type="negative")
            return

        self.vm.set("file_name", event.file.name)
        self.vm.set("content", content)
        self.vm.set("content_type", content_type)
        self.vm.set("title", Path(event.file.name).stem)

        self.file_label.set_text(f"Selected document: {event.file.name}")

    async def save(self) -> None:
        """Validate the exposed fields and persist the document before closing."""
        title = self.vm.get("title", "").strip()
        language = self.vm.get("language", "").strip()
        try:
            org_id = float(self.vm.get("org_id", 0.0))
        except TypeError, ValueError, OverflowError:
            org_id = 0.0

        if not title:
            ui.notify("Title is required.", type="negative")
            return
        if not org_id.is_integer() or org_id < 1:
            ui.notify("A valid organization ID is required.", type="negative")
            return
        if not language:
            ui.notify("Language is required.", type="negative")
            return

        file_name = self. vm.get("file_name", "")
        if (
            not file_name
            or self._content_type_for_filename(file_name) is None
            or self.vm.get("content_type", "")
            not in {*DOCUMENT_CONTENT_TYPES.values(), "application/x-pdf"}
            or not self.vm.get("content")
        ):
            ui.notify(
                "Upload a supported, non-empty document before saving.",
                type="negative",
            )
            return

        self.vm.set("title", title)
        self.vm.set("language", language)
        self.vm.set("org_id", int(org_id))
        try:
            await self.vm.call("save")
        except Exception as ex:
            ui.notify(f"The document could not be saved: {ex}", type="negative")
            return
        self.dialog.submit("save")

    async def show(self) -> str | None:
        """Display the dialog and return the submitted action.

        Returns:
            The submitted action, or None if the dialog was dismissed.
        """
        return await self.dialog
