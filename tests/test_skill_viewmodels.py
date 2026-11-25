import unittest
from unittest.mock import AsyncMock, call, patch

from src.dtos.skill import SkillDTO
from src.viewmodels.skill import SkillViewModel
from src.viewmodels.skill_list import SkillListViewModel


class SkillViewModelTests(unittest.IsolatedAsyncioTestCase):
    """Tests for organization-aware skill view models."""

    def make_skill(self) -> SkillDTO:
        """Create a representative skill DTO for view-model tests."""
        return SkillDTO.from_dict(
            {
                "skill_id": 12,
                "org_id": 3,
                "name": "A skill",
                "description": "A description",
                "instructions": "Follow these instructions.",
                "enabled": True,
                "version": 2,
            }
        )

    async def test_load_scopes_skill_lookup_to_organization(self) -> None:
        """Load by name and organization, then copy the returned DTO."""
        skill = self.make_skill()
        repository = AsyncMock()
        repository.load.return_value = skill

        with patch("src.viewmodels.skill.SkillRepository", return_value=repository):
            view_model = SkillViewModel()
            await view_model._on_call("load", org_id=3, name="A skill")

        repository.load.assert_awaited_once_with(org_id=3, name="A skill")
        self.assertEqual(view_model.skill_id, skill.skill_id)
        self.assertEqual(view_model.org_id, skill.org_id)
        self.assertEqual(view_model.name, skill.name)

    async def test_save_preserves_organization_and_generated_id(self) -> None:
        """Save the selected organization and retain the generated skill ID."""
        repository = AsyncMock()
        repository.save.return_value = {"skill_id": 12}

        with patch("src.viewmodels.skill.SkillRepository", return_value=repository):
            view_model = SkillViewModel(org_id=3, name="A skill")
            await view_model.save()

        saved_skill = repository.save.await_args.args[0]
        self.assertEqual(saved_skill.org_id, 3)
        self.assertEqual(view_model.skill_id, 12)

    async def test_list_and_delete_use_the_selected_organization(self) -> None:
        """Pass org_id to both the list and delete repository operations."""
        repository = AsyncMock()
        repository.list.return_value = []

        with patch(
            "src.viewmodels.skill_list.SkillRepository", return_value=repository
        ):
            view_model = SkillListViewModel()
            await view_model._on_call("load", org_id=3)
            await view_model._on_call("delete", skill_id=12, org_id=4)

        repository.list.assert_has_awaits([call(org_id=3), call(org_id=4)])
        repository.delete.assert_awaited_once_with(skill_id=12, org_id=4)


if __name__ == "__main__":
    unittest.main()
