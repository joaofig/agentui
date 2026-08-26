import builtins

from src.dtos.user_activity import UserActivityDTO
from src.repositories.postgres.user_activity import UserActivityRepository


class UserActivityModel:
    repo = UserActivityRepository()

    async def save(self, dto: UserActivityDTO):
        user = await self.repo.save(dto)
        dto.user_activity_id = user["user_activity_id"]

    async def list(self, user_name: str) -> builtins.list[UserActivityDTO]:
        return await self.repo.list(user_name)

