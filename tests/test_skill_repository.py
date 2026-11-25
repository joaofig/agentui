import unittest
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

from dtos.skill import SkillDTO
from repositories.postgres.skill import SkillRepository


class FakeCursor:
    def __init__(self, inserted_id: int = 0) -> None:
        """Create a cursor that records SQL and simulates generated IDs.

        Args:
            inserted_id: ID returned by simulated insert statements.
        """
        self.inserted_id = inserted_id
        self.calls: list[tuple[str, Any]] = []
        self.fetchone_result: dict[str, int] | None = None

    async def __aenter__(self) -> FakeCursor:
        """Enter the asynchronous cursor context manager.

        Returns:
            This cursor.
        """
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit the asynchronous cursor context manager.

        Args:
            args: Exception information supplied by the context manager.
        """
        return None

    async def execute(self, query: str, params: Any = None) -> FakeCursor:
        """Record an SQL statement and simulate an insert result.

        Args:
            query: SQL statement to execute.
            params: Values bound to the SQL statement.

        Returns:
            This cursor.
        """
        self.calls.append((query, params))
        if query.lstrip().startswith("INSERT"):
            self.fetchone_result = {"skill_id": self.inserted_id}
        return self

    async def fetchone(self) -> dict[str, int] | None:
        """Return the simulated result of the last insert."""
        return self.fetchone_result


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        """Create a connection that provides the supplied cursor.

        Args:
            cursor: Cursor instance used for all connection operations.
        """
        self.closed = False
        self.cursor_instance = cursor
        self.commit_calls = 0

    def cursor(self) -> FakeCursor:
        """Return the connection's cursor."""
        return self.cursor_instance

    async def commit(self) -> None:
        """Count a simulated transaction commit."""
        self.commit_calls += 1


class SkillRepositoryTests(unittest.IsolatedAsyncioTestCase):
    def create_repository(
        self, cursor: FakeCursor
    ) -> tuple[SkillRepository, FakeConnection]:
        """Create a repository wired to an in-memory async connection."""
        repository = SkillRepository()
        connection = FakeConnection(cursor)
        repository.conn = connection  # type: ignore[assignment]
        repository.connect = AsyncMock(return_value=connection)  # type: ignore[method-assign]
        return repository, connection

    def make_skill(self, skill_id: int = 0) -> SkillDTO:
        """Create a skill with representative values for repository tests."""
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

    async def test_save_inserts_and_returns_generated_skill_id(self) -> None:
        """Insert a skill and include its generated primary key in the result."""
        skill = self.make_skill()
        cursor = FakeCursor(inserted_id=12)
        repository, connection = self.create_repository(cursor)

        result = await repository.save(skill)

        self.assertEqual(result["skill_id"], 12)
        query, params = cursor.calls[0]
        self.assertEqual(query.lstrip().split()[:3], ["INSERT", "INTO", "skill"])
        self.assertIn("RETURNING skill_id", query)
        self.assertNotIn("skill_id", query.split("VALUES", maxsplit=1)[0])
        self.assertEqual(params["org_id"], skill.org_id)
        self.assertEqual(params["created_on"], skill.created_on)
        self.assertEqual(params["created_by"], skill.created_by)
        self.assertEqual(params["updated_on"], skill.updated_on)
        self.assertEqual(params["updated_by"], skill.updated_by)
        self.assertEqual(connection.commit_calls, 1)

    async def test_save_updates_existing_skill_with_updated_audit_fields(self) -> None:
        """Update a skill by its explicit primary key and organization."""
        skill = self.make_skill(skill_id=12)
        cursor = FakeCursor()
        repository, connection = self.create_repository(cursor)

        result = await repository.save(skill)

        self.assertEqual(result["skill_id"], 12)
        query, params = cursor.calls[0]
        self.assertIn("UPDATE skill", query)
        self.assertIn("WHERE skill_id = %(skill_id)s", query)
        self.assertIn("AND org_id = %(org_id)s", query)
        self.assertIn("updated_on = %(updated_on)s", query)
        self.assertIn("updated_by = %(updated_by)s", query)
        self.assertNotIn("created_on =", query)
        self.assertNotIn("created_by =", query)
        self.assertEqual(params["skill_id"], 12)
        self.assertEqual(params["org_id"], skill.org_id)
        self.assertEqual(params["updated_on"], skill.updated_on)
        self.assertEqual(params["updated_by"], skill.updated_by)
        self.assertEqual(connection.commit_calls, 1)

    async def test_delete_is_scoped_to_skill_and_organization(self) -> None:
        """Delete only the skill belonging to the requested organization."""
        cursor = FakeCursor()
        repository, connection = self.create_repository(cursor)

        await repository.delete(12, org_id=3)

        query, params = cursor.calls[0]
        normalized_query = " ".join(query.split())
        self.assertEqual(normalized_query.split()[:3], ["DELETE", "FROM", "skill"])
        self.assertIn("WHERE skill_id = %s", normalized_query)
        self.assertIn("AND org_id = %s", normalized_query)
        self.assertEqual(params, (12, 3))
        self.assertEqual(connection.commit_calls, 1)


if __name__ == "__main__":
    unittest.main()
