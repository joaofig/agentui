from typing import Any

from haystack.dataclasses import ImageContent, FileContent, SkillInfo
from haystack.skill_stores.types import SkillStore

from src.repositories.postgres.skill import SkillRepository


class PgSkillStore(SkillStore):

    def __init__(self, org_id: int = 1):
        self.repo = SkillRepository()


    def list_skills(self) -> dict[str, SkillInfo]:
        """
        Discover and return all available skills.

        :returns: Mapping of skill name to its metadata.
        """
        ...

    def load_skill(self, name: str) -> tuple[str, list[str]]:
        """
        Return the named skill's instruction body and the manifest of its bundled files.

        :param name: Skill name as returned by `list_skills`.
        :returns: A tuple of (markdown body with frontmatter stripped, sorted list of POSIX-style paths relative
            to the skill root for any bundled files). The file list is empty when the skill bundles no extras.
        :raises KeyError: If no skill with `name` exists.
        """
        ...

    def read_skill_file(self, name: str, path: str) -> str | ImageContent | FileContent:
        """
        Read a file bundled with the named skill.

        Implementations should return text files as a `str`, image files as an `ImageContent`, and PDFs as a
        `FileContent`, so a multimodal agent can pass binary assets straight to the model.

        :param name: Skill name as returned by `list_skills`.
        :param path: Path of the file relative to the skill root (e.g. `"reference/forms.md"`).
        :returns: The file's text content (`str`), an `ImageContent` for images, or a `FileContent` for PDFs.
        :raises KeyError: If no skill with `name` exists.
        :raises FileNotFoundError: If the file does not exist within the skill.
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize this store to a dictionary for use with `from_dict`.

        Implement both this method and `from_dict` to make your custom store serializable.
        """
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillStore":
        """
        Deserialize a store from a dictionary produced by `to_dict`.

        Implement both this method and `to_dict` to make your custom store serializable.

        :param data: Dictionary as produced by `to_dict`.
        """