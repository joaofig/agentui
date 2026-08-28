import builtins
from typing import LiteralString

from dtos.agent_message import AgentMessageDTO
from repositories.postgres.base import PostgresRepository


class AgentMessageRepository(PostgresRepository):

    async def list(self, agent_context_id: int) -> builtins.list[AgentMessageDTO]:
        sql: LiteralString = """
        SELECT  agent_message_id, agent_context_id, user_id, user_name,
                role, content, created_at, created_by
        FROM    agent_message
        WHERE   agent_context_id = %s
        """
        result = await self.execute_query(sql, (agent_context_id,))
        return [AgentMessageDTO.from_dict(s) for s in result]

    async def delete(self, agent_context_id: int) -> None:
        sql: LiteralString = """
        DELETE FROM agent_message WHERE agent_context_id = %s
        """
        await self.execute_query(sql, (agent_context_id,))

    async def save(self, message: AgentMessageDTO) -> dict:
        insert: LiteralString = """
        INSERT INTO agent_message (user_id, user_name, role, content, created_at, created_by)
        VALUES (%(user_id)s, %(user_name)s, %(role)s, %(content)s, %(created_at)s, %(created_by)s)
        RETURNING agent_message_id
        """
        update: LiteralString = ""
        return await self.insert_or_update(insert, update, message.to_dict())
