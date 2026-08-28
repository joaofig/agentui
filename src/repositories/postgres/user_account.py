import builtins
from typing import LiteralString

from src.dtos.user_account import UserAccountDTO
from src.repositories.postgres.base import PostgresRepository


class UserAccountRepository(PostgresRepository):
    def __init__(self):
        super().__init__()

    async def get_user(self, user_name: str, pass_hash: str) -> UserAccountDTO | None:
        sql: LiteralString = """
        SELECT  user_id, user_name, pass_hash, user_role, change_pass,
                created_at, created_by, updated_at, updated_by
        FROM    user_account
        WHERE   user_name = %s AND pass_hash = %s
        """
        result = await self.execute_query(sql, (user_name, pass_hash))
        if result:
            return UserAccountDTO.from_dict(result[0])
        return None

    async def list(self) -> builtins.list[UserAccountDTO]:
        sql: LiteralString = """
        SELECT  user_id, user_name, pass_hash, user_role, change_pass,
                created_at, created_by, updated_at, updated_by
        FROM    user_account
        """
        result = await self.execute_query(sql)
        return [UserAccountDTO.from_dict(s) for s in result]

    async def load(self, user_id: int) -> UserAccountDTO | None:
        sql: LiteralString = """
        SELECT  user_id, user_name, pass_hash, user_role, change_pass,
                created_at, created_by, updated_at, updated_by
        FROM    user_account
        WHERE   user_id = %s
        """
        result = await self.execute_query(sql, (user_id,))
        if result:
            return UserAccountDTO.from_dict(result[0])
        return None

    async def save(self, user: UserAccountDTO) -> dict:
        insert: LiteralString = """
        INSERT INTO user_account (user_name, pass_hash, user_role, change_pass,
                          created_at, created_by, updated_at, updated_by)
        VALUES (%(user_name)s, %(pass_hash)s, %(user_role)s, %(change_pass)s, 
                %(created_at)s, %(created_by)s, %(updated_at)s, %(updated_by)s)
        RETURNING user_id
        """
        update: LiteralString = """
        UPDATE user_account SET user_name = %(user_name)s, pass_hash = %(pass_hash)s, user_role = %(user_role)s,
                        change_pass = %(change_pass)s, updated_at = %(updated_at)s, updated_by = %(updated_by)s
        WHERE   user_id = %(user_id)s
        RETURNING user_id
        """
        return await self.insert_or_update(insert, update, user.to_dict())

    async def delete(self, user_id: int) -> None:
        sql: LiteralString = """
        DELETE FROM user_account WHERE user_id = %s
        """
        await self.execute_query(sql, (user_id,))
