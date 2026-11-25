from typing import Any, LiteralString, cast

from dtos.rag_document import RagDocumentDTO
from repositories.postgres.base import PostgresRepositoryAsync


class RagDocumentRepository(PostgresRepositoryAsync):
    """PostgreSQL repository for `rag_document` records."""

    async def list(self, org_id: int) -> list[RagDocumentDTO]:
        """List documents belonging to an organization.

        Args:
            org_id: Organization whose documents should be returned.

        Returns:
            Document DTOs ordered by creation time, newest first.
        """
        sql: LiteralString = """
        SELECT      rag_doc_id, org_id, title, description, file_name, content_type,
                    page_count, chunk_count, status, language, created_on, created_by,
                    updated_on, updated_by
        FROM        public.rag_document
        WHERE       org_id = %s
        ORDER BY    created_on DESC
        """
        result = await self.execute_query(sql, (org_id,))
        return [RagDocumentDTO.from_dict(cast(dict[str, Any], row)) for row in result]

    async def load(self, rag_doc_id: int) -> RagDocumentDTO | None:
        """Load a document by its primary key.

        Args:
            rag_doc_id: Primary key of the document to load.

        Returns:
            The matching document DTO, or None when no row exists.
        """
        sql: LiteralString = """
        SELECT      rag_doc_id, org_id, title, description, file_name, content_type,
                    content, page_count, chunk_count, language, created_on, created_by,
                    updated_on, updated_by
        FROM        public.rag_document
        WHERE       rag_doc_id = %s
        """
        result = await self.execute_query(sql, (rag_doc_id,))
        if result:
            return RagDocumentDTO.from_dict(
                cast(dict[str, Any], cast(object, result[0]))
            )
        return None

    async def load_content(self, rag_doc_id: int, org_id: int) -> bytes | None:
        """Load only the binary content for a document, on demand.

        Args:
            rag_doc_id: Primary key of the document whose content is requested.
            org_id: Organization ID that must match the document's owner.

        Returns:
            The document's binary content when the row exists and belongs to
            the requested organization, or None otherwise.
        """
        sql: LiteralString = """
        SELECT content
        FROM   public.rag_document
        WHERE  rag_doc_id = %s
            AND org_id = %s
        """
        result = await self.execute_query(sql, (rag_doc_id, org_id))
        if result:
            return cast(dict[str, Any], cast(object, result[0])).get("content")
        return None

    async def save_content(self, rag_doc_id: int, org_id: int, content: bytes) -> bool:
        """Update only the binary content for an existing document.

        Args:
            rag_doc_id: Primary key of the document to update.
            org_id: Organization ID that must match the document's owner.
            content: The binary content to persist.

        Returns:
            True when a row was updated, False when no matching document exists.
        """
        sql: LiteralString = """
        UPDATE public.rag_document
        SET    content = %s
        WHERE  rag_doc_id = %s
            AND org_id = %s
        """
        await self.connect()
        if self.conn:
            async with self.conn.cursor() as cur:
                await cur.execute(sql, (content, rag_doc_id, org_id))
                updated = cur.rowcount > 0
                await self.conn.commit()
            return updated
        return False

    async def delete(self, rag_doc_id: int, org_id: int) -> bool:
        """Delete a document by its primary key, scoped to the owning organization.

        Args:
            rag_doc_id: Primary key of the document to delete.
            org_id: Organization ID that must match the document's owner.

        Returns:
            True when a row was deleted, False when no matching document exists.
        """
        sql: LiteralString = """
        DELETE FROM public.rag_document
        WHERE  rag_doc_id = %s
            AND org_id = %s
        """
        await self.connect()
        if self.conn:
            async with self.conn.cursor() as cur:
                await cur.execute(sql, (rag_doc_id, org_id))
                deleted = cur.rowcount > 0
                await self.conn.commit()
            return deleted
        return False

    async def save(self, document: RagDocumentDTO) -> dict[str, object]:
        """Insert a new document or update an existing one.

        Args:
            document: Document DTO to persist.  The `content` field is
                excluded — use `save_content` for on-demand updates.

        Returns:
            The DTO's database mapping, including a generated ID after insert.
        """
        insert: LiteralString = """
        INSERT INTO public.rag_document (
            org_id, title, description, file_name, content_type, page_count,
            chunk_count, language, created_on, created_by, updated_on, updated_by
        )
        VALUES (
            %(org_id)s, %(title)s, %(description)s, %(file_name)s, %(content_type)s,
            %(page_count)s, %(chunk_count)s, %(language)s, %(created_on)s,
            %(created_by)s, %(updated_on)s, %(updated_by)s
        )
        RETURNING rag_doc_id
        """
        update: LiteralString = """
        UPDATE public.rag_document SET
            org_id = %(org_id)s,
            title = %(title)s,
            description = %(description)s,
            file_name = %(file_name)s,
            content_type = %(content_type)s,
            page_count = %(page_count)s,
            chunk_count = %(chunk_count)s,
            language = %(language)s,
            updated_on = %(updated_on)s,
            updated_by = %(updated_by)s
        WHERE rag_doc_id = %(rag_doc_id)s
            AND org_id = %(org_id)s
        RETURNING rag_doc_id
        """
        data = document.to_dict()
        data.pop("content", None)
        return await self.insert_or_update(insert, update, data, key_field="rag_doc_id")
