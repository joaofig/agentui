from repositories.postgres.base import PostgresRepository


class SkillRrepository(PostgresRepository):

    def __init__(self):
        super().__init__()


    def list(self, org_id: int = 1) -> SkillDTO:
        pass