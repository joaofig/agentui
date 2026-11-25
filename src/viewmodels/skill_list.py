from typing import Any

from nicegui import binding
from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel

from src.repositories.postgres.skill import SkillRepository


@binding.bindable_dataclass
class SkillListViewModel(ViewModel):
    """View model for listing and managing skills."""

    def __init__(self) -> None:
        """Initialize the skill list, repository, and load subscription."""
        super().__init__()
        self.selected_id: int = 0
        self.delete_enabled: bool = False
        self.org_id: int = 1
        self.skills: GridList = GridList()
        self.repository: SkillRepository = SkillRepository()
        self.subscribe(channel="skill_list", message="load", handler=self._on_load)

    async def load(self, org_id: int | None = None) -> None:
        """Load skills for the specified organization.

        Args:
            org_id: Organization ID to load; defaults to the current organization.
        """
        organization_id = self.org_id if org_id is None else org_id
        skills = await self.repository.list(org_id=organization_id)
        self.skills.replace([skill.to_dict() for skill in skills])
        self.org_id = organization_id

    async def _on_call(self, msg: str, **kwargs: Any) -> Any:
        """Handle actions requested by the skill-list view.

        Args:
            msg: Action message (load, skill_selected, or delete).
            **kwargs: Optional skill ID and organization ID.

        Returns:
            None.
        """
        match msg:
            case "load":
                org_id = kwargs.get("org_id", self.org_id)
                await self.load(org_id=int(org_id))

            case "skill_selected":
                if "skill_id" in kwargs:
                    self.selected_id = int(str(kwargs["skill_id"]))
                    self.delete_enabled = self.selected_id != 0
                    self.org_id = int(kwargs.get("org_id", self.org_id))

            case "delete":
                skill_id = int(kwargs.get("skill_id", self.selected_id) or 0)
                org_id = int(kwargs.get("org_id", self.org_id) or 0)
                if skill_id > 0 and org_id > 0:
                    await self.repository.delete(skill_id=skill_id, org_id=org_id)
                    await self.load(org_id=org_id)
                    self.selected_id = 0
                    self.delete_enabled = False
        return None

    async def _on_load(self, **kwargs: Any) -> None:
        """Reload skills after a load notification.

        Args:
            **kwargs: Optional organization ID filter.
        """
        org_id = kwargs.get("org_id", self.org_id)
        await self.load(org_id=int(org_id))
