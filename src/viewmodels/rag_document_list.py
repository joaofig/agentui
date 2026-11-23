from typing import Any

from nicegui import binding
from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel

from src.repositories.postgres.rag_document import RagDocumentRepository


@binding.bindable_dataclass
class RagDocumentListViewModel(ViewModel):
    """View model for listing RAG documents."""

    def __init__(self) -> None:
        """Initialize the document list, repository, and load subscription."""
        super().__init__()
        self.selected_id: int = 0
        self.delete_enabled: bool = False
        self.org_id: int = 1
        self.loaded_org_id: int = 1
        self.documents = GridList()
        self.repo: RagDocumentRepository = RagDocumentRepository()
        self.subscribe(
            channel="rag_document_list", message="load", handler=self._on_load
        )

    async def load(self, org_id: int = 0) -> None:
        """Load all documents for the given organization.

        Args:
            org_id: Organization filter; defaults to 0.
        """
        if org_id != self.loaded_org_id:
            self.selected_id = 0
            self.delete_enabled = False
        docs = await self.repo.list(org_id=org_id)
        self.documents.replace([doc.to_dict() for doc in docs])
        self.org_id = org_id
        self.loaded_org_id = org_id

    async def _on_call(self, msg: str, **kwargs) -> Any:
        """Handle incoming calls from the view.

        Args:
            msg: Action message (load, document_selected, delete).
            **kwargs: Additional context such as rag_doc_id or org_id.

        Returns:
            None.
        """
        match msg:
            case "load":
                org_id = kwargs.get("org_id", self.org_id)
                await self.load(org_id=org_id)

            case "document_selected":
                if "rag_doc_id" in kwargs:
                    self.selected_id = int(str(kwargs["rag_doc_id"]))
                    self.delete_enabled = self.selected_id != 0
                    self.org_id = int(kwargs.get("org_id", self.org_id))

            case "delete":
                rag_doc_id = int(kwargs.get("rag_doc_id", self.selected_id) or 0)
                org_id = int(kwargs.get("org_id", self.org_id) or 0)
                if rag_doc_id > 0 and org_id > 0:
                    deleted = await self.repo.delete(
                        rag_doc_id=rag_doc_id, org_id=org_id
                    )
                    if deleted:
                        await self.load(org_id=org_id)
                    self.selected_id = 0
                    self.delete_enabled = False
        return None

    async def _on_load(self, **kwargs) -> None:
        """Broadcast handler to reload the document list.

        Args:
            **kwargs: Optional org_id filter.
        """
        org_id = kwargs.get("org_id", self.org_id)
        await self.load(org_id=org_id)
