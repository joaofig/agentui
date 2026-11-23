from typing import LiteralString, List

from nicemvvm.tools.user import get_user_name

from src.dtos.rag_doc_chunk import RagDocumentChunkDTO
from src.repositories.postgres.base import PostgresRepository


class RagDocumentChunkRepository(PostgresRepository):
    """PostgreSQL repository for `rag_document` records."""

    async def insert(self, rag_doc_chunks: List[RagDocumentChunkDTO]) -> List[int]:
        """Insert a new `rag_document_chunk` record."""

        inserted_ids: List[int] = []

        sql: LiteralString = """
        INSERT INTO rag_doc_chunk (
            rag_doc_id, org_id, page_number, ordinal, content, embedding, created_by
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING rag_chunk_id;
        """

        conn = await self.connect()
        if conn:
            async with conn.cursor() as cur:
                for chunk in rag_doc_chunks:
                    await cur.execute(sql, (
                        chunk.rag_doc_id,
                        chunk.org_id,
                        chunk.page_number,
                        chunk.ordinal,
                        chunk.content,
                        chunk.embedding,
                        get_user_name()
                    ))
                    res = await cur.fetchone()
                    if res:
                        rag_chunk_id = res["rag_chunk_id"]
                        chunk.rag_chunk_id = rag_chunk_id
                        inserted_ids.append(rag_chunk_id)

            async with conn.cursor() as cur:
                sql = """
                    UPDATE  rag_document 
                    SET     status = 'processed',
                            chunk_count = %s,
                            page_count = %s
                    WHERE   rag_doc_id = %s
                    """
                await cur.execute(sql, (len(rag_doc_chunks),
                      max(c.page_number for c in rag_doc_chunks),
                      rag_doc_chunks[0].rag_doc_id))

            await conn.commit()
            await conn.close()
        return inserted_ids
