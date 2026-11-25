from haystack.dataclasses import SkillInfo
from haystack.skill_stores.types import SkillStore

from repositories.postgres.skill import SkillRepository


class MemSkillStore(SkillStore):
    def __init__(self, org_id: int = 1):
        self.repo = SkillRepository()
        self.org_id = org_id

        self.skills: dict[str, SkillInfo] = {}

    async def load(self, org_id: int = 0) -> None:
        if org_id == 0:
            org_id = self.org_id

        skills = await self.repo.list(org_id)
        self.skills = {
            skill.name: SkillInfo(name=skill.name, description=skill.description)
            for skill in skills
        }

    def list_skills(self) -> dict[str, SkillInfo]:
        """
        Discover and return all available skills.

        :returns: Mapping of skill name to its metadata.
        """
        return self.skills

    def load_skill(self, name: str) -> tuple[str, list[str]]:
        """
        Return the named skill's instruction body and the manifest of its bundled files.

        :param name: Skill name as returned by `list_skills`.
        :returns: A tuple of (markdown body with frontmatter stripped, sorted list of POSIX-style paths relative
            to the skill root for any bundled files). The file list is empty when the skill bundles no extras.
        :raises KeyError: If no skill with `name` exists.
        """
        if name not in self.skills:
            raise KeyError(f"No skill named '{name}'")
        return self.skills[name].description, []
