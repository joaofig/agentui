from typing import Any

from nicemvvm.tools.observability import GridList
from nicemvvm.viewmodels.view_model import ViewModel


class ChatThreadsViewModel(ViewModel):

    def __init__(self):
        super().__init__()
        self.threads = GridList()

    async def _on_call(self, msg: str, **kwargs) -> Any:
        return None
