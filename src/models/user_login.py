import builtins
from datetime import datetime

from src.dtos.user_login import UserLoginDTO
from src.repositories.postgres.user_login import UserLoginRepository


class UserModel:
    repo = UserLoginRepository()

    @classmethod
    def empty(cls) -> UserLoginDTO:
        return UserLoginDTO(
            user_id=0,
            user_name="",
            pass_hash="",
            user_role="User",
            change_pass=False,
            created_by="",
            created_at=datetime.now(),
            updated_by="",
            updated_at=datetime.now()
        )

    async def save(self, dto: UserLoginDTO):
        user = await self.repo.save(dto)
        dto.user_id = user["user_id"]

    async def delete(self, user_id: int):
        await self.repo.delete(user_id)

    async def load(self, user_id: int) -> UserLoginDTO | None:
        return await self.repo.load(user_id)

    async def list(self) -> builtins.list[UserLoginDTO]:
        return await self.repo.list()

    async def get_user(self, user_name: str, pass_hash: str) -> UserLoginDTO | None:
        return await self.repo.get_user(user_name, pass_hash)
