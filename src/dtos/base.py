from datetime import datetime

from pydantic import BaseModel

from nicemvvm.tools.user import get_user_name


class ReadOnlyDTO(BaseModel):
    created_on: datetime = datetime.now()
    created_by: str = ""

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_on.isoformat(),
            "created_by": self.created_by,
        }

    def log_change(self, own_id: int):
        if own_id == 0:
            self.created_on = datetime.now()
            self.created_by = get_user_name()


class BaseDTO(ReadOnlyDTO):
    updated_on: datetime = datetime.now()
    updated_by: str = ""

    def to_dict(self) -> dict:
        return {
            "updated_at": self.updated_on.isoformat(),
            "updated_by": self.updated_by,
        } | super().to_dict()

    def log_change(self, own_id: int):
        self.updated_on = datetime.now()
        self.updated_by = get_user_name()

        super().log_change(own_id)
