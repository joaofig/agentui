from datetime import datetime
from typing import Any

from nicegui import binding
from nicemvvm.tools.user import get_user_name
from nicemvvm.viewmodels.view_model import ViewModel

from src.dtos.skill import SkillDTO
from src.repositories.postgres.skill import SkillRepository


@binding.bindable_dataclass
class SkillViewModel(ViewModel):
    """View model for a single skill."""

    skill_id: int = 0
    org_id: int = 1
    name: str = ""
    description: str = ""
    instructions: str = ""
    enabled: bool = False
    version: int = 0
    created_on: datetime = datetime.now().astimezone()
    created_by: str = ""
    updated_on: datetime = datetime.now().astimezone()
    updated_by: str = ""

    def __post_init__(self) -> None:
        """Initialize base view-model behavior after dataclass construction."""
        super().__init__()

    async def _on_call(self, msg: str, **kwargs: Any) -> Any:
        """Handle incoming view actions.

        Args:
            msg: Action message (copy, save, or load).
            **kwargs: Action data such as a skill DTO, name, or org_id.

        Returns:
            None.
        """
        match msg:
            case "copy":
                skill = kwargs.get("skill")
                if isinstance(skill, SkillDTO):
                    self.copy(skill)

            case "save":
                await self.save()

            case "load":
                if "name" in kwargs:
                    org_id = int(kwargs.get("org_id", self.org_id))
                    skill = await SkillRepository().load(
                        org_id=org_id, name=kwargs["name"]
                    )
                    if skill:
                        self.copy(skill)
        return None

    def copy(self, skill: SkillDTO) -> None:
        """Copy fields from a skill DTO into this view model.

        Args:
            skill: Source skill DTO.
        """
        self.skill_id = skill.skill_id
        self.org_id = skill.org_id
        self.name = skill.name
        self.description = skill.description
        self.instructions = skill.instructions
        self.enabled = skill.enabled
        self.version = skill.version
        self.created_on = skill.created_on
        self.created_by = skill.created_by
        self.updated_on = skill.updated_on
        self.updated_by = skill.updated_by

    def to_dto(self) -> SkillDTO:
        """Build a skill DTO from the current view-model state.

        Returns:
            A skill DTO populated with the current fields and audit metadata.
        """
        is_old = self.skill_id > 0
        return SkillDTO(
            skill_id=self.skill_id,
            org_id=self.org_id,
            name=self.name,
            description=self.description,
            instructions=self.instructions,
            enabled=self.enabled,
            version=self.version,
            created_on=self.created_on if is_old else datetime.now().astimezone(),
            created_by=self.created_by if is_old else get_user_name(),
            updated_on=datetime.now().astimezone(),
            updated_by=get_user_name(),
        )

    async def save(self) -> None:
        """Persist this skill and update its generated ID when inserted."""
        skill = self.to_dto()
        saved_skill = await SkillRepository().save(skill)
        skill_id = saved_skill.get("skill_id")
        if isinstance(skill_id, int) and skill_id > 0:
            self.skill_id = skill_id
