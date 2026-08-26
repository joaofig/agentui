from typing import LiteralString

from dtos.user_activity import UserActivityDTO
from repositories.postgres.base import PostgresRepository


class UserActivityRepository(PostgresRepository):
    def __init__(self):
        super().__init__()

    async def list(self, user_name: str) -> list[UserActivityDTO]:
        sql: LiteralString = """
        SELECT      user_activity_id, user_id, user_name, user_action,
                    created_at, created_by
        FROM        user_activity
        WHERE       user_name = %(user_name)s
        ORDER BY    created_at DESC
        """
        result = await self.execute_query(sql, (user_name, ))
        return [UserActivityDTO.from_dict(s) for s in result]

    async def save(self, user: UserActivityDTO) -> dict:
        user.user_activity_id = 0  # Ensure that we always insert a new record

        insert: LiteralString = """
        INSERT INTO user_activity (
            user_id,
            user_name,
            user_action,
            created_at, created_by)
        VALUES (%(user_id)s, %(user_name)s, %(user_action)s,
                %(created_at)s, %(created_by)s)
        RETURNING user_activity_id
        """
        update: LiteralString = ""
        return await self.insert_or_update(insert, update, user.to_dict(),
                                           key_field="user_activity_id")
