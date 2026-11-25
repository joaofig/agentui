from typing import Any, LiteralString

from nicemvvm.tools.singleton import singleton
from psycopg import AsyncConnection, rows, Connection

from src.repositories.postgres.client import get_postgres_client_async, get_postgres_client_sync


@singleton
class PostgresCentral:
    conn_async: AsyncConnection | None = None
    conn_sync: Connection | None = None

    async def connect_async(self) -> AsyncConnection | None:
        if not self.conn_async or self.conn_async.closed:
            self.conn_async = await get_postgres_client_async()
            # Set row factory to dict_row to match Supabase's dictionary-based results
            self.conn_async.row_factory = rows.dict_row
        return self.conn_async

    def connect_sync(self) -> Connection | None:
        if not self.conn_async or self.conn_async.closed:
            self.conn_sync = get_postgres_client_sync()
            # Set row factory to dict_row to match Supabase's dictionary-based results
            self.conn_sync.row_factory = rows.dict_row
        return self.conn_sync


class PostgresRepositoryAsync:
    def __init__(self):
        self.conn: AsyncConnection | None = None

    async def connect(self) -> AsyncConnection | None:
        self.conn = await PostgresCentral().connect_async()
        return self.conn

    async def execute_query(
        self, sql: LiteralString, params: tuple | list | None = None
    ) -> list[tuple[Any, ...]] | list[dict[Any, Any]]:
        await self.connect()
        if self.conn:
            async with self.conn.cursor() as cur:
                await cur.execute(sql, params)
                if (
                    sql.strip().upper().startswith("SELECT")
                    or "RETURNING" in sql.upper()
                ):
                    return await cur.fetchall()
                await self.conn.commit()
        return []

    async def insert_or_update(
        self,
        insert: LiteralString,
        update: LiteralString,
        value: dict,
        key_field: str = "",
    ) -> dict:
        await self.connect()
        if self.conn:
            if key_field:
                row_id = key_field
            else:
                row_id_fields = [k for k in value if k == "id" or k.endswith("_id")]
                # Fallback if no obvious ID field.
                row_id = row_id_fields[0] if row_id_fields else "id"

            async with self.conn.cursor() as cur:
                if value.get(row_id, 0) > 0:
                    # UPDATE
                    await cur.execute(update, value)
                    await self.conn.commit()
                else:
                    # INSERT
                    id_value = await cur.execute(insert, value)
                    result = await id_value.fetchone()
                    if result:
                        value[row_id] = result[row_id]
                    await self.conn.commit()
        return value


class PostgresRepositorySync:
    def __init__(self):
        self.conn: Connection | None = None

    def connect(self) -> Connection | None:
        self.conn = PostgresCentral().connect_sync()
        return self.conn

    def execute_query(
        self, sql: LiteralString, params: tuple | list | None = None
    ) -> list[tuple[Any, ...]] | list[dict[Any, Any]]:
        self.connect()
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                if (
                    sql.strip().upper().startswith("SELECT")
                    or "RETURNING" in sql.upper()
                ):
                    return cur.fetchall()
                self.conn.commit()
        return []

    def insert_or_update(
        self,
        insert: LiteralString,
        update: LiteralString,
        value: dict,
        key_field: str = "",
    ) -> dict:
        self.connect()
        if self.conn:
            if key_field:
                row_id = key_field
            else:
                row_id_fields = [k for k in value if k == "id" or k.endswith("_id")]
                # Fallback if no obvious ID field.
                row_id = row_id_fields[0] if row_id_fields else "id"

            with self.conn.cursor() as cur:
                if value.get(row_id, 0) > 0:
                    # UPDATE
                    cur.execute(update, value)
                    self.conn.commit()
                else:
                    # INSERT
                    id_value = cur.execute(insert, value)
                    result = id_value.fetchone()
                    if result:
                        value[row_id] = result[row_id]
                    self.conn.commit()
        return value
