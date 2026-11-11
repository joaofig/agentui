from typing import Self

from dtos.base import ReadOnlyDTO
from nicemvvm.tools.user import dict_to_datetime


class AgentMessageDTO(ReadOnlyDTO):
    agent_message_id: int = 0
    agent_context_id: int = 0
    user_id: int = 0
    user_name: str = ""
    role: str = ""
    content: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            agent_message_id=data.get("agent_msg_id", 0),
            agent_context_id=data.get("agent_context_id", 0),
            user_id=data.get("user_id", 0),
            user_name=data.get("user_name", ""),
            role=data.get("role", ""),
            content=data.get("content", ""),
            created_on=dict_to_datetime(data, "created_at"),
            created_by=data.get("created_by", "system"),
        )

    def to_dict(self) -> dict:
        return {
            "agent_message_id": self.agent_message_id,
            "agent_context_id": self.agent_context_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "role": self.role,
            "content": self.content,
            **super().to_dict(),
        }
