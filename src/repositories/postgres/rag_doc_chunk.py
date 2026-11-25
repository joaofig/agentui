import builtins
from collections.abc import Sequence
from typing import LiteralString

from nicemvvm.tools.user import get_user_name

from dtos.search_hit import SearchHit
from src.dtos.rag_doc_chunk import RagDocumentChunkDTO
from src.repositories.postgres.base import PostgresRepositoryAsync


class RagDocumentChunkRepository(PostgresRepositoryAsync):
    """PostgreSQL repository for `rag_document` records."""

    async def insert(
        self, rag_doc_chunks: builtins.list[RagDocumentChunkDTO]
    ) -> builtins.list[int]:
        """Insert a new `rag_document_chunk` record."""

        inserted_ids: list[int] = []

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
                    await cur.execute(
                        sql,
                        (
                            chunk.rag_doc_id,
                            chunk.org_id,
                            chunk.page_number,
                            chunk.ordinal,
                            chunk.content,
                            chunk.embedding,
                            get_user_name(),
                        ),
                    )
                    res = await cur.fetchone()
                    if res:
                        rag_chunk_id = res["rag_chunk_id"]
                        chunk.rag_chunk_id = rag_chunk_id
                        inserted_ids.append(rag_chunk_id)

            async with conn.cursor() as cur:
                sql = """
                    UPDATE  rag_document 
                    SET     status = '✅',
                            chunk_count = %s,
                            page_count = %s
                    WHERE   rag_doc_id = %s
                    """
                await cur.execute(
                    sql,
                    (
                        len(rag_doc_chunks),
                        max(c.page_number for c in rag_doc_chunks),
                        rag_doc_chunks[0].rag_doc_id,
                    ),
                )

            await conn.commit()
            await conn.close()
        return inserted_ids

    async def list(self, rag_doc_id: int) -> builtins.list[RagDocumentChunkDTO]:
        sql = """
        SELECT  rag_chunk_id
        ,       rag_doc_id
        ,       org_id
        ,       page_number
        ,       ordinal
        ,       content
        ,       created_on
        ,       created_by
        
        FROM    rag_doc_chunk
        WHERE   rag_doc_id = %s;
            
        """
        result = await self.execute_query(sql, (rag_doc_id,))
        return [RagDocumentChunkDTO.from_dict(s) for s in result]

    async def search_keyword(
        self, org_id: int, query: str, limit: int = 5
    ) -> list[SearchHit]:
        """Full-text and keyword search using PostgreSQL tsvector and ILIKE."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        # We use plainto_tsquery combined with ILIKE for robust matching
        sql = """
                SELECT  c.rag_chunk_id,
                        c.rag_doc_id,
                        COALESCE(d.file_name, '')   AS file_name,
                        COALESCE(d.title, '')       AS title,
                        c.page_number,
                        c.ordinal,
                        c.content,
                        ts_rank_cd(c.tsv, plainto_tsquery('english', %s)) AS rank_score
                FROM    rag_doc_chunk c
                JOIN    rag_document d ON c.rag_doc_id = d.rag_doc_id
                WHERE   c.org_id = %s
                        AND (c.tsv @@ plainto_tsquery('english', %s) 
                                OR c.content ILIKE %s
                                OR d.title ILIKE %s)
              ORDER BY  rank_score DESC, c.rag_chunk_id
              LIMIT     %s;
              """

        like_pattern = f"%{cleaned_query}%"
        rows = self.execute_query(
            sql,
            (cleaned_query, org_id, cleaned_query, like_pattern, like_pattern, limit),
        )

        hits: list[SearchHit] = []
        for row in rows:
            hits.append(
                SearchHit(
                    chunk_id=row[0],
                    document_id=row[1],
                    file_name=row[2],
                    title=row[3],
                    page=row[4],
                    ordinal=row[5],
                    content=row[6],
                    score=float(row[7]) if row[7] is not None else 0.0,
                    search_type="keyword",
                )
            )
        return hits

    async def search_vector(
        self, org_id: int, query_embedding: Sequence[float], limit: int = 5
    ) -> list[SearchHit]:
        """Vector similarity search using cosine distance with pgvector."""
        if not query_embedding:
            return []

        # In pgvector: <=> is cosine distance (0 is identical, 2 is opposite)
        # Similarity score = 1.0 - cosine_distance
        sql = """
                SELECT      c.rag_chunk_id,
                            c.rag_doc_id,
                            COALESCE(d.file_name, '')   AS file_name,
                            COALESCE(d.title, '')       AS title,
                            c.page_number,
                            c.ordinal,
                            c.content,
                            (1 - (c.embedding <=> %s::vector)) AS similarity
                FROM        rag_doc_chunk c
                JOIN        rag_document d ON c.rag_doc_id = d.rag_doc_id
                WHERE       d.org_id = %s
                ORDER BY    c.embedding <=> %s::vector
                LIMIT       %s;
              """
        embeddings = list(query_embedding)
        rows = await self.execute_query(sql, (embeddings, org_id, embeddings, limit))
        hits: list[SearchHit] = []
        for row in rows:
            hits.append(
                SearchHit(
                    chunk_id=row[0],
                    document_id=row[1],
                    file_name=row[2],
                    title=row[3],
                    page=row[4],
                    ordinal=row[5],
                    content=row[6],
                    score=float(row[7]) if row[7] is not None else 0.0,
                    search_type="vector",
                )
            )
        return hits

    async def hybrid_search(
        self,
        org_id: int,
        query: str,
        query_embedding: Sequence[float] | None = None,
        limit: int = 5,
        rrf_k: int = 60,
    ) -> list[SearchHit]:
        """Hybrid search combining keyword search and semantic vector search via RRF.

        Reciprocal Rank Fusion (RRF) formula:
            score = sum(1.0 / (rrf_k + rank_i))
        """
        # Retrieve candidate pools for both methods
        candidate_k = max(limit * 3, 20)
        kw_hits = await self.search_keyword(org_id, query, limit=candidate_k)
        vec_hits = (
            await self.search_vector(org_id, query_embedding, limit=candidate_k)
            if query_embedding
            else []
        )

        if not vec_hits:
            return kw_hits[:limit]
        if not kw_hits:
            return vec_hits[:limit]

        # Compute RRF scores
        rrf_scores: dict[int, float] = {}
        hit_map: dict[int, SearchHit] = {}

        for rank, hit in enumerate(kw_hits, start=1):
            rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + (
                1.0 / (rrf_k + rank)
            )
            hit_map[hit.chunk_id] = hit

        for rank, hit in enumerate(vec_hits, start=1):
            rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + (
                1.0 / (rrf_k + rank)
            )
            if hit.chunk_id not in hit_map:
                hit_map[hit.chunk_id] = hit

        # Sort by final fused RRF score
        sorted_chunk_ids = sorted(
            rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True
        )

        results: list[SearchHit] = []
        for cid in sorted_chunk_ids[:limit]:
            item = hit_map[cid]
            results.append(
                SearchHit(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    file_name=item.file_name,
                    title=item.title,
                    page=item.page,
                    ordinal=item.ordinal,
                    content=item.content,
                    score=rrf_scores[cid],
                    search_type="hybrid",
                    metadata={
                        "raw_score": item.score,
                        "rrf_score": rrf_scores[cid],
                    },
                )
            )

        return results
