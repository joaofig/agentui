from typing import LiteralString

from dtos.agent_context import AgentContextDTO
from repositories.postgres.base import PostgresRepository


class AgentContextRepository(PostgresRepository):
    async def load(self, agent_context_id: int) -> AgentContextDTO | None:
        sql: LiteralString = """
        SELECT      agent_context_id, user_id, user_name, context_name,
                    created_at, created_by
        FROM        agent_context
        WHERE       agent_context_id = %(agent_context_id)s
        """
        result = await self.execute_query(sql, (agent_context_id,))
        if result:
            return AgentContextDTO.from_dict(result[0])
        return None

    async def list(self, user_name: str) -> list[AgentContextDTO]:
        sql: LiteralString = """
        SELECT      agent_context_id, user_id, user_name, context_name,
                    created_at, created_by
        FROM        agent_context
        WHERE       user_name = %(user_name)s
        ORDER BY    created_at DESC
        """
        result = await self.execute_query(sql, (user_name,))
        return [AgentContextDTO.from_dict(s) for s in result]


    async def save(self, user: AgentContextDTO) -> dict:
        insert: LiteralString = """
        INSERT INTO agent_context (user_id, user_name, context_name,
                          created_at, created_by)
        VALUES (%(user_id)s, %(user_name)s, %(context_name)s, 
                %(created_at)s, %(created_by)s)
        RETURNING agent_context_id
        """
        update: LiteralString = """
        UPDATE agent_context SET user_id = %(user_id)s, user_name = %(user_name)s, 
                                 context_name = %(context_name)s
        WHERE   agent_context_id = %(agent_context_id)s
        RETURNING agent_context_id
        """
        return await self.insert_or_update(insert, update, user.to_dict())
