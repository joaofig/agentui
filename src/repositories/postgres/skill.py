from typing import LiteralString

from repositories.postgres.base import PostgresRepositorySync
from src.dtos.skill import SkillDTO


class SkillRepository(PostgresRepositorySync):
    def __init__(self) -> None:
        """Initialize the skill repository."""
        super().__init__()

    def list(self, org_id: int = 1) -> list[SkillDTO]:
        """List skills belonging to an organization.

        Args:
            org_id: Organization ID whose skills should be listed.

        Returns:
            The organization's skills.
        """
        sql = """
            SELECT  skill_id
            ,       org_id
            ,       name
            ,       description
            ,       instructions
            ,       enabled
            ,       version
            ,       created_on
            ,       created_by
            ,       updated_on
            ,       updated_by
            FROM    skill
            WHERE   org_id = %s
        """
        result = self.execute_query(sql, (org_id,))
        return [SkillDTO.from_dict(row) for row in result]

    def load(self, org_id: int = 1, name: str = "") -> SkillDTO | None:
        """Load a skill by its name within an organization.

        Args:
            org_id: Organization ID that owns the skill.
            name: Name of the skill to load.

        Returns:
            The matching skill, or None when no skill is found.
        """
        sql = """
            SELECT  skill_id
            ,       org_id
            ,       name
            ,       description
            ,       instructions
            ,       enabled
            ,       version
            ,       created_on
            ,       created_by
            ,       updated_on
            ,       updated_by
            FROM    skill
            WHERE   org_id = %s and name = %s
        """
        result = self.execute_query(sql, (org_id, name))
        if result:
            return SkillDTO.from_dict(result[0])
        return None

    def save(self, skill: SkillDTO) -> dict[str, object]:
        """Insert a skill or update an existing skill.

        Args:
            skill: Skill data to persist.

        Returns:
            The database mapping, including the generated skill ID after insert.
        """
        insert: LiteralString = """
            INSERT INTO skill (
                org_id, name, description, instructions, enabled, version,
                created_on, created_by, updated_on, updated_by
            )
            VALUES (
                %(org_id)s, %(name)s, %(description)s, %(instructions)s,
                %(enabled)s, %(version)s, %(created_on)s, %(created_by)s,
                %(updated_on)s, %(updated_by)s
            )
            RETURNING skill_id
        """
        update: LiteralString = """
            UPDATE skill SET
                org_id = %(org_id)s,
                name = %(name)s,
                description = %(description)s,
                instructions = %(instructions)s,
                enabled = %(enabled)s,
                version = %(version)s,
                updated_on = %(updated_on)s,
                updated_by = %(updated_by)s
            WHERE skill_id = %(skill_id)s
                AND org_id = %(org_id)s
        """
        return self.insert_or_update(
            insert, update, skill.to_dict(), key_field="skill_id"
        )

    def delete(self, skill_id: int, org_id: int) -> None:
        """Delete a skill only when it belongs to the requested organization.

        Args:
            skill_id: Primary key of the skill to delete.
            org_id: Organization ID that must match the skill's owner.
        """
        sql: LiteralString = """
            DELETE FROM skill
            WHERE skill_id = %s
                AND org_id = %s
        """
        self.execute_query(sql, (skill_id, org_id))
