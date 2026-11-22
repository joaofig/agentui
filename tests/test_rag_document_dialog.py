import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, Mock, patch

from nicegui import events

from src.services.document_thumbnail import OFFICE_EXTENSIONS
from src.viewmodels.rag_document import RagDocumentViewModel
from src.viewmodels.rag_document_list import RagDocumentListViewModel
from src.views.dialogs.rag_document_dialog import (
    DOCUMENT_CONTENT_TYPES,
    SUPPORTED_FILE_EXTENSIONS,
    RagDocumentDialog,
)
from src.views.rag_doc_grid import RagDocumentGrid


class FakeUploadFile:
    """Minimal async upload object for dialog upload tests."""

    def __init__(
        self, name: str, content: bytes, content_type: str = "application/octet-stream"
    ) -> None:
        self.name = name
        self.content = content
        self.content_type = content_type
        self.read = AsyncMock(return_value=content)


class RagDocumentDialogTests(unittest.IsolatedAsyncioTestCase):
    """Tests for document upload validation and dialog submission."""

    def create_dialog(self, vm: RagDocumentViewModel) -> RagDocumentDialog:
        """Create a dialog instance without constructing NiceGUI elements."""
        dialog = object.__new__(RagDocumentDialog)
        dialog.vm = vm
        dialog.document_vm = vm
        dialog.dialog = Mock()
        dialog.file_label = Mock()
        return dialog

    def create_valid_view_model(self) -> RagDocumentViewModel:
        """Create a view model with valid metadata and existing document bytes."""
        return RagDocumentViewModel(
            org_id=4,
            title="A document",
            file_name="document.pdf",
            content_type="application/pdf",
            content=b"existing document bytes",
            language="EN",
        )

    def test_allowed_extensions_match_thumbnail_formats(self) -> None:
        """Expose PDF and exactly the Office extensions accepted by thumbnails."""
        self.assertEqual(
            set(SUPPORTED_FILE_EXTENSIONS), {".pdf", *OFFICE_EXTENSIONS.values()}
        )
        for content_type, extension in OFFICE_EXTENSIONS.items():
            with self.subTest(extension=extension):
                self.assertEqual(DOCUMENT_CONTENT_TYPES[extension], content_type)
        self.assertEqual(DOCUMENT_CONTENT_TYPES[".pdf"], "application/pdf")

    async def test_upload_sets_canonical_type_from_filename(self) -> None:
        """Use the filename extension, not the browser-provided media type."""
        vm = RagDocumentViewModel(content=b"previous bytes")
        dialog = self.create_dialog(vm)
        uploaded_file = FakeUploadFile(
            "new-document.DOCX", b"new document", content_type="text/plain"
        )

        with patch("src.views.dialogs.rag_document_dialog.ui.notify") as notify:
            await dialog._on_upload(
                cast(
                    events.UploadEventArguments,
                    cast(object, SimpleNamespace(file=uploaded_file)),
                )
            )

        self.assertEqual(vm.file_name, "new-document.DOCX")
        self.assertEqual(
            vm.content_type,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertEqual(vm.content, b"new document")
        uploaded_file.read.assert_awaited_once()
        notify.assert_not_called()

    async def test_unsupported_upload_does_not_replace_existing_content(self) -> None:
        """Reject unsupported extensions without discarding previously loaded bytes."""
        vm = self.create_valid_view_model()
        dialog = self.create_dialog(vm)
        uploaded_file = FakeUploadFile("notes.txt", b"new bytes")

        with patch("src.views.dialogs.rag_document_dialog.ui.notify") as notify:
            await dialog._on_upload(
                cast(
                    events.UploadEventArguments,
                    cast(object, SimpleNamespace(file=uploaded_file)),
                )
            )

        self.assertEqual(vm.file_name, "document.pdf")
        self.assertEqual(vm.content_type, "application/pdf")
        self.assertEqual(vm.content, b"existing document bytes")
        uploaded_file.read.assert_not_awaited()
        notify.assert_called_once()

    async def test_empty_upload_does_not_replace_existing_content(self) -> None:
        """Reject empty uploads while retaining the current file metadata and bytes."""
        vm = self.create_valid_view_model()
        dialog = self.create_dialog(vm)
        uploaded_file = FakeUploadFile("replacement.pdf", b"")

        with patch("src.views.dialogs.rag_document_dialog.ui.notify") as notify:
            await dialog._on_upload(
                cast(
                    events.UploadEventArguments,
                    cast(object, SimpleNamespace(file=uploaded_file)),
                )
            )

        self.assertEqual(vm.file_name, "document.pdf")
        self.assertEqual(vm.content, b"existing document bytes")
        notify.assert_called_once()

    async def test_save_rejects_missing_required_fields(self) -> None:
        """Keep the dialog open when any exposed field or document bytes are absent."""
        valid_values = {
            "title": "A document",
            "org_id": 4,
            "language": "EN",
            "file_name": "document.pdf",
            "content_type": "application/pdf",
            "content": b"document bytes",
        }
        missing_fields = (
            "title",
            "org_id",
            "language",
            "file_name",
            "content_type",
            "content",
        )

        for field in missing_fields:
            with self.subTest(field=field):
                vm = RagDocumentViewModel(**valid_values)
                setattr(
                    vm,
                    field,
                    ""
                    if field in {"title", "language", "file_name", "content_type"}
                    else 0
                    if field == "org_id"
                    else None,
                )
                dialog = self.create_dialog(vm)

                with patch("src.views.dialogs.rag_document_dialog.ui.notify") as notify:
                    await dialog.save()

                dialog.dialog.submit.assert_not_called()
                notify.assert_called_once()

    async def test_save_accepts_existing_content_and_closes_after_persistence(
        self,
    ) -> None:
        """Allow edits to retain their loaded content without a second upload."""
        vm = self.create_valid_view_model()
        vm.rag_doc_id = 12
        dialog = self.create_dialog(vm)
        repository = Mock()
        repository.save = AsyncMock(return_value={"rag_doc_id": 12})
        repository.save_content = AsyncMock(return_value=True)

        with (
            patch(
                "src.viewmodels.rag_document.RagDocumentRepository",
                return_value=repository,
            ),
            patch("src.views.dialogs.rag_document_dialog.ui.notify") as notify,
        ):
            await dialog.save()

        dialog.dialog.submit.assert_called_once_with("save")
        repository.save_content.assert_awaited_once_with(
            rag_doc_id=12,
            org_id=4,
            content=b"existing document bytes",
        )
        notify.assert_not_called()

    async def test_save_uses_generated_id_to_persist_uploaded_content(self) -> None:
        """Persist uploaded bytes using the identifier returned by metadata save."""
        vm = self.create_valid_view_model()
        vm.rag_doc_id = 0
        repository = Mock()
        repository.save = AsyncMock(return_value={"rag_doc_id": 37})
        repository.save_content = AsyncMock(return_value=True)

        with patch(
            "src.viewmodels.rag_document.RagDocumentRepository",
            return_value=repository,
        ):
            saved = await vm.save()

        self.assertTrue(saved)
        self.assertEqual(vm.rag_doc_id, 37)
        repository.save_content.assert_awaited_once_with(
            rag_doc_id=37,
            org_id=4,
            content=b"existing document bytes",
        )

    async def test_content_save_failure_keeps_dialog_open(self) -> None:
        """Do not report success when the second persistence stage fails."""
        vm = self.create_valid_view_model()
        dialog = self.create_dialog(vm)
        repository = Mock()
        repository.save = AsyncMock(return_value={"rag_doc_id": 37})
        repository.save_content = AsyncMock(return_value=False)

        with (
            patch(
                "src.viewmodels.rag_document.RagDocumentRepository",
                return_value=repository,
            ),
            patch("src.views.dialogs.rag_document_dialog.ui.notify") as notify,
        ):
            await dialog.save()

        dialog.dialog.submit.assert_not_called()
        notify.assert_called_once()

    async def test_grid_edit_loads_document_and_refreshes_its_organization(
        self,
    ) -> None:
        """Load the selected document before editing and reload its list on save."""
        document_vm = RagDocumentViewModel(rag_doc_id=12, org_id=4)
        document_vm.call = AsyncMock()
        dialog = Mock()
        dialog.show = AsyncMock(return_value="save")
        grid = object.__new__(RagDocumentGrid)
        grid.vm = SimpleNamespace(call=AsyncMock())
        event = SimpleNamespace(args={"rag_doc_id": 12})
        app = SimpleNamespace(
            storage=SimpleNamespace(
                user=SimpleNamespace(get=Mock(return_value="test-user"))
            )
        )

        with (
            patch(
                "src.views.rag_doc_grid.RagDocumentViewModel",
                return_value=document_vm,
            ),
            patch("src.views.rag_doc_grid.RagDocumentDialog", return_value=dialog),
            patch("src.views.rag_doc_grid.app", app),
        ):
            await grid._on_edit(event)

        document_vm.call.assert_awaited_once_with("load", rag_doc_id=12)
        self.assertEqual(document_vm.updated_by, "test-user")
        dialog.show.assert_awaited_once()
        grid.vm.call.assert_awaited_once_with("load", org_id=4)

    async def test_grid_clears_document_selection_when_no_row_is_selected(
        self,
    ) -> None:
        """Clear the selected identifier and disable deletion after deselection."""
        grid = object.__new__(RagDocumentGrid)
        grid.vm = SimpleNamespace(call=AsyncMock(), get=Mock(return_value=4))
        grid.grid = SimpleNamespace(get_selected_row=AsyncMock(return_value=None))

        await grid._row_selection_changed(None)

        grid.vm.call.assert_awaited_once_with(
            "document_selected", rag_doc_id=0, org_id=4
        )

    async def test_load_resets_selection_when_organization_changes(self) -> None:
        """Clear stale row selection when loading another organization's rows."""
        with patch(
            "src.viewmodels.rag_document_list.RagDocumentRepository"
        ) as repository_class:
            repository = repository_class.return_value
            repository.list = AsyncMock(return_value=[])
            vm = RagDocumentListViewModel()

        vm.org_id = 5
        vm.loaded_org_id = 4
        vm.selected_id = 12
        vm.delete_enabled = True

        await vm.load(org_id=5)

        self.assertEqual(vm.selected_id, 0)
        self.assertFalse(vm.delete_enabled)
        self.assertEqual(vm.loaded_org_id, 5)
