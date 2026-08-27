import os

import psycopg
from dotenv import load_dotenv
from psycopg import AsyncConnection


async def get_postgres_client() -> AsyncConnection:
    """
    Create and return a Postgres connection instance.

    Returns:
        AsyncConnection: A psycopg AsyncConnection instance.
    """
    load_dotenv()

    # Try getting DSN from environment
    dsn = os.getenv("POSTGRES_URL")

    if not dsn:
        # Construct DSN from individual components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")

        if not db or not user or not password:
            raise ValueError(
                "POSTGRES_URL or (POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD) "
                "must be set in environment variables."
            )

        dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    return await psycopg.AsyncConnection.connect(dsn)
