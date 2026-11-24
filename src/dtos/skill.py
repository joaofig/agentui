from dataclasses import dataclass
from datetime import datetime
from typing import Self

from src.dtos.base import BaseDTO


@dataclass
class SkillDTO(BaseDTO):
    skill_id: int
    org_id: int
    name: str
    description: str
    instructions: str
    enabled: bool
    version: int

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            skill_id=data.get("skill_id", 0),
            org_id=data.get("org_id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            enabled=data.get("enabled", False),
            version=data.get("version", 0),

            created_on=data.get("created_on", datetime.now().astimezone()),
            created_by=data.get("created_by", "admin"),
            updated_on=data.get("updated_on", datetime.now().astimezone()),
            updated_by=data.get("updated_by", "admin"),
        )

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "enabled": self.enabled,
            "version": self.version,

            "created_on": self.created_on,
            "created_by": self.created_by,
            "updated_on": self.updated_on,
            "updated_by": self.updated_by,
        }