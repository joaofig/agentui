from typing import Self

from nicemvvm.tools.user import dict_to_datetime
from src.dtos.base import ReadOnlyDTO


class UserActivityDTO(ReadOnlyDTO):
    user_activity_id: int
    user_id: int
    activity_type: str
    activity_data: str

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            user_activity_id=data.get("user_activity_id", 0),
            user_id=data.get("user_id", 0),
            activity_type=data.get("activity_type", ""),
            activity_data=data.get("activity_data", ""),
            created_at=dict_to_datetime(data, "created_at"),
            created_by=data.get("created_by", "system"),
        )

    def to_dict(self) -> dict:
        return {
            "user_activity_id": self.user_activity_id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "activity_data": self.activity_data,
            **super().to_dict(),
        }
