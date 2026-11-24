from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import LiteralString, cast
from uuid import uuid4

import psycopg
from haystack import Document
from haystack.document_stores.types import DuplicatePolicy
from haystack.utils.auth import Secret
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore
from psycopg import sql
from psycopg.errors import DataException, ForeignKeyViolation, NotNullViolation
from psycopg.types.json import Jsonb


class RagDocChunkIntegrationTests(unittest.TestCase):
    """Verify rag_doc_chunk with PostgreSQL, pgvector, and Haystack."""

    connection_string: str
    schema_name: str
    admin_connection: psycopg.Connection
    store: PgvectorDocumentStore

    @classmethod
    def setUpClass(cls) -> None:
        """Create a disposable schema and apply the chunk table definition."""
        connection_string = os.environ.get("RAG_DOC_CHUNK_TEST_CONNECTION_STRING")
        if connection_string is None:
            raise unittest.SkipTest(
                "Set RAG_DOC_CHUNK_TEST_CONNECTION_STRING to a disposable "
                "pgvector database."
            )
        cls.connection_string = connection_string

        cls.schema_name = f"rag_doc_chunk_test_{uuid4().hex}"
        cls.admin_connection = psycopg.connect(cls.connection_string, autocommit=True)
        cls.addClassCleanup(cls.admin_connection.close)
        cls.admin_connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cls.admin_connection.execute(
            sql.SQL("CREATE SCHEMA ") + sql.Identifier(cls.schema_name)
        )
        cls.addClassCleanup(cls.drop_test_schema)
        cls.admin_connection.execute(
            sql.SQL("CREATE TABLE ")
            + sql.Identifier(cls.schema_name, "rag_document")
            + sql.SQL(" (rag_doc_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY)")
        )
        cls.admin_connection.execute(
            sql.SQL("SET search_path TO ")
            + sql.Identifier(cls.schema_name)
            + sql.SQL(", public")
        )

        schema_path = (
            Path(__file__).resolve().parents[1] / "db" / "postgres" / "create_table.sql"
        )
        schema_sql = schema_path.read_text(encoding="utf-8")
        chunk_sql = cast(
            LiteralString,
            schema_sql.split("-- Table: rag_doc_chunk", maxsplit=1)[1].split(
                "CREATE TABLE IF NOT EXISTS chat_thread", maxsplit=1
            )[0],
        )
        cls.admin_connection.execute(sql.SQL(chunk_sql))

    @classmethod
    def drop_test_schema(cls) -> None:
        """Remove the isolated schema created for this integration test."""
        cls.admin_connection.execute(
            sql.SQL("DROP SCHEMA ")
            + sql.Identifier(cls.schema_name)
            + sql.SQL(" CASCADE")
        )

    def tearDown(self) -> None:
        """Close the Haystack store before removing its schema."""
        if hasattr(self, "store"):
            self.store.close()

    def insert_raw_chunk(
        self, chunk_id: str, embedding: str, meta: dict[str, int]
    ) -> None:
        """Insert a raw chunk to exercise database constraints directly."""
        query = (
            sql.SQL("INSERT INTO ")
            + sql.Identifier(self.schema_name, "rag_doc_chunk")
            + sql.SQL(" (id, embedding, content, meta) VALUES (%s, %s::vector, %s, %s)")
        )
        with psycopg.connect(self.connection_string) as connection:
            connection.execute(
                query,
                (chunk_id, embedding, "constraint check", Jsonb(meta)),
            )

    def test_haystack_round_trip_and_integrity_constraints(self) -> None:
        """Round-trip Haystack chunks and verify parent, audit, and vector rules."""
        self.store = PgvectorDocumentStore(
            connection_string=Secret.from_token(self.connection_string),
            create_extension=False,
            schema_name=self.schema_name,
            table_name="rag_doc_chunk",
            embedding_dimension=768,
        )
        parent_id = self.admin_connection.execute(
            sql.SQL("INSERT INTO ")
            + sql.Identifier(self.schema_name, "rag_document")
            + sql.SQL(" DEFAULT VALUES RETURNING rag_doc_id")
        ).fetchone()[0]

        original = Document(
            id="chunk-1",
            content="Initial chunk",
            embedding=[0.1] * 768,
            meta={"rag_doc_id": parent_id, "chunk_index": 0},
        )
        self.assertEqual(self.store.write_documents([original]), 1)
        first_read = self.store.filter_documents()[0]
        created_on = first_read.meta["created_on"]
        created_by = first_read.meta["created_by"]

        replacement = Document(
            id="chunk-1",
            content="Updated chunk",
            embedding=[0.2] * 768,
            meta={"rag_doc_id": parent_id, "chunk_index": 1},
        )
        self.assertEqual(
            self.store.write_documents([replacement], policy=DuplicatePolicy.OVERWRITE),
            1,
        )
        updated_read = self.store.filter_documents()[0]
        self.assertEqual(updated_read.content, "Updated chunk")
        embedding = updated_read.embedding
        if embedding is None:
            self.fail("Haystack returned no embedding for the updated chunk.")
        self.assertEqual(len(embedding), 768)
        for value in embedding:
            self.assertAlmostEqual(value, 0.2, places=6)
        self.assertEqual(updated_read.meta["rag_doc_id"], parent_id)
        self.assertEqual(updated_read.meta["created_on"], created_on)
        self.assertEqual(updated_read.meta["created_by"], created_by)
        self.assertTrue(updated_read.meta["updated_on"])
        self.assertTrue(updated_read.meta["updated_by"])

        valid_embedding = str([0.1] * 768)
        invalid_parent = parent_id + 1_000_000
        with self.assertRaises(ForeignKeyViolation):
            self.insert_raw_chunk(
                "invalid-parent", valid_embedding, {"rag_doc_id": invalid_parent}
            )

        with self.assertRaises(NotNullViolation):
            self.insert_raw_chunk("missing-parent", valid_embedding, {})

        with self.assertRaises(DataException):
            self.insert_raw_chunk("wrong-dimension", "[0.1]", {"rag_doc_id": parent_id})

        self.admin_connection.execute(
            sql.SQL("DELETE FROM ")
            + sql.Identifier(self.schema_name, "rag_document")
            + sql.SQL(" WHERE rag_doc_id = %s"),
            (parent_id,),
        )
        self.assertEqual(self.store.filter_documents(), [])


if __name__ == "__main__":
    unittest.main()
