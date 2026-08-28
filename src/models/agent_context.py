from dtos.agent_context import AgentContextDTO
from repositories.postgres.agent_context import AgentContextRepository

class AgentContextModel:
    repo = AgentContextRepository()

    async def load(self, agent_context_id: int) -> AgentContextDTO | None:
        return await self.repo.load(agent_context_id)

    async def list(self, user_name: str) -> list[AgentContextDTO]:
        return await self.repo.list(user_name)

    async def save(self, context: AgentContextDTO) -> dict:
        return await self.repo.save(context)
