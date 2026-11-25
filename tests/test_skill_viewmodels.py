import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.dtos.skill import SkillDTO
from src.viewmodels.skill import SkillViewModel
from src.viewmodels.skill_list import SkillListViewModel


class SkillViewModelTests(unittest.IsolatedAsyncioTestCase):
    def make_skill(self, skill_id: int = 0) -> SkillDTO:
        """Create a skill with representative fields for view-model tests.

        Args:
            skill_id: ID to assign to the skill.

        Returns:
            A populated skill DTO.
        """
        return SkillDTO.model_construct(
            skill_id=skill_id,
            org_id=3,
            name="A skill",
            description="A skill description",
            instructions="Follow these instructions.",
            enabled=True,
            version=2,
            created_on=datetime(2026, 11, 21, 14, 50, tzinfo=UTC),
            created_by="creator",
            updated_on=datetime(2026, 11, 22, 14, 50, tzinfo=UTC),
            updated_by="editor",
        )

    def test_copy_and_to_dto_preserve_skill_fields(self) -> None:
        """Copy DTO data into the view model and convert it back."""
        skill = self.make_skill(skill_id=12)
        view_model = SkillViewModel()

        view_model.copy(skill)
        converted = view_model.to_dto()

        self.assertEqual(converted.skill_id, skill.skill_id)
        self.assertEqual(converted.org_id, skill.org_id)
        self.assertEqual(converted.name, skill.name)
        self.assertEqual(converted.description, skill.description)
        self.assertEqual(converted.instructions, skill.instructions)
        self.assertEqual(converted.enabled, skill.enabled)
        self.assertEqual(converted.version, skill.version)
        self.assertEqual(converted.created_on, skill.created_on)
        self.assertEqual(converted.created_by, skill.created_by)

    def test_from_dict_includes_skill_audit_fields(self) -> None:
        """Hydrate a skill DTO with both domain and inherited audit fields."""
        created_on = datetime(2026, 11, 21, 14, 50, tzinfo=UTC)
        updated_on = datetime(2026, 11, 22, 14, 50, tzinfo=UTC)

        skill = SkillDTO.from_dict(
            {
                "skill_id": 12,
                "org_id": 3,
                "name": "A skill",
                "description": "A skill description",
                "instructions": "Follow these instructions.",
                "enabled": True,
                "version": 2,
                "created_on": created_on,
                "created_by": "creator",
                "updated_on": updated_on,
                "updated_by": "editor",
            }
        )

        self.assertEqual(skill.created_on, created_on)
        self.assertEqual(skill.created_by, "creator")
        self.assertEqual(skill.updated_on, updated_on)
        self.assertEqual(skill.updated_by, "editor")

    async def test_save_persists_skill_and_sets_generated_id(self) -> None:
        """Persist a new skill and copy its generated ID to the view model."""
        repository = AsyncMock()
        repository.save.return_value = {"skill_id": 12}
        view_model = SkillViewModel(
            org_id=3,
            name="A skill",
            description="A skill description",
            instructions="Follow these instructions.",
            enabled=True,
            version=2,
        )

        with patch("src.viewmodels.skill.SkillRepository", return_value=repository):
            await view_model.save()

        self.assertEqual(view_model.skill_id, 12)
        saved_skill = repository.save.await_args.args[0]
        self.assertEqual(saved_skill.name, "A skill")
        self.assertEqual(saved_skill.org_id, 3)

    async def test_load_copies_repository_result(self) -> None:
        """Load a skill by organization and name into the view model."""
        repository = AsyncMock()
        skill = self.make_skill(skill_id=12)
        repository.load.return_value = skill
        view_model = SkillViewModel()

        with patch("src.viewmodels.skill.SkillRepository", return_value=repository):
            await view_model._on_call("load", org_id=3, name="A skill")

        repository.load.assert_awaited_once_with(org_id=3, name="A skill")
        self.assertEqual(view_model.skill_id, 12)
        self.assertEqual(view_model.name, "A skill")


class SkillListViewModelTests(unittest.IsolatedAsyncioTestCase):
    def make_skill(self) -> SkillDTO:
        """Create a representative skill DTO for list tests.

        Returns:
            A populated skill DTO.
        """
        return SkillDTO.model_construct(
            skill_id=12,
            org_id=3,
            name="A skill",
            description="A skill description",
            instructions="Follow these instructions.",
            enabled=True,
            version=2,
            created_on=datetime(2026, 11, 21, 14, 50, tzinfo=UTC),
            created_by="creator",
            updated_on=datetime(2026, 11, 22, 14, 50, tzinfo=UTC),
            updated_by="editor",
        )

    async def test_load_replaces_skills_with_repository_results(self) -> None:
        """Load DTOs into the observable skill list."""
        repository = AsyncMock()
        skill = self.make_skill()
        repository.list.return_value = [skill]
        skills = MagicMock()

        with (
            patch(
                "src.viewmodels.skill_list.SkillRepository",
                return_value=repository,
            ),
            patch("src.viewmodels.skill_list.GridList", return_value=skills),
        ):
            view_model = SkillListViewModel()
            await view_model.load(org_id=3)

        repository.list.assert_awaited_once_with(org_id=3)
        skills.replace.assert_called_once_with([skill.to_dict()])
        self.assertEqual(view_model.org_id, 3)

    async def test_delete_removes_selected_skill_and_resets_selection(self) -> None:
        """Delete a selected skill within its organization and reload."""
        repository = AsyncMock()
        skills = MagicMock()

        with (
            patch(
                "src.viewmodels.skill_list.SkillRepository",
                return_value=repository,
            ),
            patch("src.viewmodels.skill_list.GridList", return_value=skills),
        ):
            view_model = SkillListViewModel()
            view_model.selected_id = 12
            view_model.delete_enabled = True
            view_model.org_id = 3
            await view_model._on_call("delete")

        repository.delete.assert_awaited_once_with(skill_id=12, org_id=3)
        repository.list.assert_awaited_once_with(org_id=3)
        self.assertEqual(view_model.selected_id, 0)
        self.assertFalse(view_model.delete_enabled)


if __name__ == "__main__":
    unittest.main()
