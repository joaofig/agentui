from typing import List

from src.dtos.skill import SkillDTO
from repositories.postgres.base import PostgresRepository


class SkillRepository(PostgresRepository):

    def __init__(self):
        super().__init__()

    async def list(self, org_id: int = 1) -> List[SkillDTO]:
        sql = """
            SELECT  skill_id
            ,       org_id
            ,       name
            ,       description
            ,       instructions
            ,       enabled
            ,       version
            ,       created_on
            ,       created_by
            ,       updated_on
            ,       updated_by
            FROM    skill
            WHERE   org_id = :org_id
        """
        result = await self.execute_query(sql, (org_id, ))
        return [SkillDTO.from_dict(row) for row in result]
