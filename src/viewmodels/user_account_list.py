from typing import Any

from nicegui import binding
from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel

from src.models.user_account import UserAccountModel


@binding.bindable_dataclass
class UserAccountListViewModel(ViewModel):
    def __init__(self):
        super().__init__()
        self.selected_id: int = 0
        self.delete_enabled: bool = False
        self.users = GridList()
        self.model: UserAccountModel = UserAccountModel()
        self.subscribe(channel="user_login_list", message="load", handler=self._on_load)

    async def load(self):
        self.users.replace([u.to_dict() for u in await self.model.list()])

    async def _on_call(self, msg: str, **kwargs) -> Any:
        match msg:
            case "load":
                await self.load()

            case "user_selected":
                if "user_id" in kwargs:
                    self.selected_id = int(str(kwargs["user_id"]))
                    self.delete_enabled = self.selected_id != 0

            case "delete":
                user_id = kwargs.get("user_id", 0)
                if user_id:
                    await self.model.delete(user_id=user_id)
                    await self.load()
                    self.selected_id = 0
                    self.delete_enabled = False
                # await self.broadcast("user_list", "load")
        return None

    async def _on_load(self, **kwargs):
        await self.load()
