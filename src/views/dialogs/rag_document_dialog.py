from pathlib import Path

from nicegui import events, ui
from nicemvvm.views.view import View

from src.services.document_thumbnail import OFFICE_EXTENSIONS
from src.viewmodels.rag_document import RagDocumentViewModel

DOCUMENT_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    **{
        extension: content_type for content_type, extension in OFFICE_EXTENSIONS.items()
    },
}
SUPPORTED_FILE_EXTENSIONS = tuple(sorted(DOCUMENT_CONTENT_TYPES))


class RagDocumentDialog(View):
    """Dialog for creating or editing a RAG document."""

    def __init__(self, vm: RagDocumentViewModel) -> None:
        """Build the document editor and connect it to the supplied view model.

        Args:
            vm: Document view model that backs the dialog fields.
        """
        super().__init__(vm)
        self.document_vm = vm

        with ui.dialog() as dialog, ui.card().classes("w-120"):
            with ui.row().classes("w-full bg-gray-200 p-2"):
                ui.label("Document Details").classes("text-base")

            ui.input(label="Title").classes("w-full").props("dense").bind_value(
                vm, "title"
            )
            ui.input(label="Description").classes("w-full").props("dense").bind_value(
                vm, "description"
            )
            ui.number(label="Organization ID", min=1, precision=0).classes(
                "w-full"
            ).props("dense").bind_value(vm, "org_id")
            ui.input(label="Language").classes("w-full").props("dense").bind_value(
                vm, "language"
            )

            self.file_label = ui.label(
                f"Selected document: {self.document_vm.file_name}"
                if self.document_vm.file_name
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

        self.document_vm.file_name = event.file.name
        self.document_vm.content_type = content_type
        self.document_vm.content = content
        self.document_vm.title = Path(event.file.name).stem
        self.file_label.set_text(f"Selected document: {event.file.name}")

    async def save(self) -> None:
        """Validate the exposed fields and persist the document before closing."""
        title = (self.document_vm.title or "").strip()
        language = (self.document_vm.language or "").strip()
        try:
            org_id = float(self.document_vm.org_id)
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
        if (
            not self.document_vm.file_name
            or self._content_type_for_filename(self.document_vm.file_name) is None
            or self.document_vm.content_type
            not in {*DOCUMENT_CONTENT_TYPES.values(), "application/x-pdf"}
            or not self.document_vm.content
        ):
            ui.notify(
                "Upload a supported, non-empty document before saving.",
                type="negative",
            )
            return

        self.document_vm.title = title
        self.document_vm.language = language
        self.document_vm.org_id = int(org_id)
        try:
            saved = await self.document_vm.call("save")
        except Exception:
            ui.notify("The document could not be saved.", type="negative")
            return
        if not saved:
            ui.notify("The document content could not be saved.", type="negative")
            return
        self.dialog.submit("save")

    async def show(self) -> str | None:
        """Display the dialog and return the submitted action.

        Returns:
            The submitted action, or None if the dialog was dismissed.
        """
        return await self.dialog
