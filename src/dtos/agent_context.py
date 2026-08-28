from dtos.base import BaseDTO


class AgentContextDTO(BaseDTO):
    """
    Data Transfer Object for Agent Context.
    """
    agent_context_id: int = 0
    user_id: int = 0
    user_name: str = ""
    context_name: str = ""


    def to_dict(self) -> dict:
        """
        Convert the AgentContextDTO to a dictionary.
        """
        return {
            "agent_context_id": self.agent_context_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "context_name": self.context_name,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an AgentContextDTO from a dictionary.
        """
        return cls(
            agent_context_id=data.get("agent_context_id", 0),
            user_id=data.get("user_id", 0),
            user_name=data.get("user_name", ""),
            context_name=data.get("context_name", ""),
        )