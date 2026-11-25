from typing import Any

from nicegui import binding
from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel

from src.repositories.postgres.skill import SkillRepository


@binding.bindable_dataclass
class SkillListViewModel(ViewModel):
    """View model for listing skills belonging to an organization."""

    def __init__(self) -> None:
        """Initialize the skill list, repository, and reload subscription."""
        super().__init__()
        self.selected_id: int = 0
        self.delete_enabled: bool = False
        self.org_id: int = 1
        self.skills = GridList()
        self.repo: SkillRepository = SkillRepository()
        self.subscribe(channel="skill_list", message="load", handler=self._on_load)

    async def load(self, org_id: int = 1) -> None:
        """Load skills for the specified organization.

        Args:
            org_id: Organization ID used to filter the skill table.
        """
        skills = await self.repo.list(org_id=org_id)
        self.skills.replace([skill.to_dict() for skill in skills])
        self.org_id = org_id

    async def _on_call(self, msg: str, **kwargs: Any) -> Any:
        """Handle incoming list actions.

        Args:
            msg: Action message (load, skill_selected, or delete).
            **kwargs: Action data such as a skill_id or org_id.

        Returns:
            None.
        """
        match msg:
            case "load":
                org_id = int(kwargs.get("org_id", self.org_id))
                await self.load(org_id=org_id)

            case "skill_selected":
                if "skill_id" in kwargs:
                    self.selected_id = int(str(kwargs["skill_id"]))
                    self.delete_enabled = self.selected_id != 0
                    self.org_id = int(kwargs.get("org_id", self.org_id))

            case "delete":
                skill_id = int(kwargs.get("skill_id", self.selected_id) or 0)
                org_id = int(kwargs.get("org_id", self.org_id))
                if skill_id > 0 and org_id > 0:
                    await self.repo.delete(skill_id=skill_id, org_id=org_id)
                    await self.load(org_id=org_id)
                    self.selected_id = 0
                    self.delete_enabled = False
        return None

    async def _on_load(self, **kwargs: Any) -> None:
        """Reload skills after a list-load notification.

        Args:
            **kwargs: Optional org_id used to filter the skill table.
        """
        org_id = int(kwargs.get("org_id", self.org_id))
        await self.load(org_id=org_id)
