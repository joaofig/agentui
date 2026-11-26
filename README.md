# agentui

A browser-based AI agent application built with NiceGUI, Haystack, PostgreSQL, and OpenAI-compatible models.

## Features

- Streamed chat with integrations for current time, Mojeek web search,
  knowledge-base tools, and skills (see current limitations below).
- Organization-scoped document and skill management. Admin users also see the Admin tab.
- PostgreSQL storage for accounts, documents, document chunks, and skills, with
  pgvector embeddings and PostgreSQL full-text search.
- Document thumbnail generation for PDFs, Microsoft Office formats, and OpenDocument formats.
- Login with a five-minute inactivity timeout.

## Requirements

- Python 3.14 or newer and [`uv`](https://docs.astral.sh/uv/).
- PostgreSQL with the `pgvector` extension available.
- An OpenAI-compatible API key and, optionally, a compatible API base URL.
- A Mojeek Search API key for the agent's web-search tool.
- LibreOffice Writer, Calc, and Impress to render Office and OpenDocument
  thumbnails. PDF thumbnails use PyMuPDF and do not require LibreOffice.

The repository's `Dockerfile` currently uses Python 3.12, which does not meet the
Python version declared in `pyproject.toml`. Use the local `uv` workflow below or
update the image before relying on that Dockerfile.

## RAG document chunks

`db/postgres/create_table.sql` enables pgvector and creates a custom
`rag_doc_chunk` table. Each chunk references a document and organization and
stores its page, ordinal, text, 1536-dimensional embedding, generated text-search
vector, and creation audit fields. It is not a Haystack `PgvectorDocumentStore`
table.

The current indexing implementation extracts and indexes PDF content only.
Office and OpenDocument uploads can be stored but are not indexed for search.
The knowledge-base chat tools are registered with the agent, but their
synchronous wrappers currently call asynchronous service/repository methods
without awaiting them; do not rely on those tools until this integration is
corrected.

## Configuration

Set these environment variables in your shell or a `.env` file in the project root:

| Variable | Required | Default / purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes | API key used by the chat and embedding clients. |
| `OPENAI_API_URL` | No | Base URL for the OpenAI-compatible API. |
| `AGENT_CHAT_MODEL` | No | Chat model; defaults to `Qwen/Qwen3.8-27B`. |
| `MOJEEK_API_KEY` | Yes for web search | API key for the configured Mojeek web-search tool. |
| `POSTGRES_URL` | One connection option required | Full PostgreSQL connection URL. Alternatively, set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`; `POSTGRES_HOST` defaults to `localhost` and `POSTGRES_PORT` to `5432`. |
| `AGENT_EMBED_MODEL` | No | Embedding model; falls back to `EMBEDDING_MODEL`, then `qwen3-embedding-8b`. |
| `AGENT_EMBED_DIM` | No | Embedding dimension; falls back to `EMBEDDING_DIM`, then `1536`. Must match the database vector column. |
| `PORT` | No | HTTP port; defaults to `8080`. |

The schema declares `rag_doc_chunk.embedding` as `vector(1536)`. If you change
the embedding dimension, update the schema to match the model output as well.

## Setup and run

1. Create a PostgreSQL database with `pgvector` available and configure the
   variables described above. For example, when using a connection URL, set
   `POSTGRES_URL`.
2. **Only for a new, disposable database**, apply the schema:

   ```sh
   psql "$POSTGRES_URL" -f db/postgres/create_table.sql
   ```

   **Warning:** this script drops and recreates several tables with `CASCADE`;
   it deletes existing application data. Back up any database you intend to
   keep, and do not run this as a routine migration.
3. Install the project and start the application:

   ```sh
   uv sync
   uv run main.py
   ```

4. Open `http://localhost:8080`. The schema seeds an `admin` account with the
   password `ai-agent`; change this password before exposing the application
   beyond a local test environment.

## Current limitations

- The Skills tab stores skill descriptions and instructions, but the chat's
  in-memory skill store currently loads only the description as skill content;
  bundled skill files are not implemented.
- Document indexing currently supports PDFs only. Uploading other supported
  formats stores the file for document management and thumbnail rendering, not
  knowledge-base search.
- The knowledge-base tools are exposed to the agent but their synchronous/async
  service boundary is incomplete, as described above.

## Document thumbnails

`GET /api/organizations/{org_id}/rag-documents/{rag_doc_id}/thumbnail` renders the
first page of a supported PDF, Microsoft Office, or OpenDocument file as an image.
The default response is a 64-by-64 JPEG; `format=png` selects PNG, and `width` and
`height` independently set the output canvas dimensions (each from 1 to 1024 pixels).

For example,
`/api/organizations/1/rag-documents/42/thumbnail?format=png&width=128&height=96`
returns a padded 128-by-96 PNG. LibreOffice Writer, Calc, and Impress must be
installed for Office and OpenDocument conversions; PDF thumbnails use PyMuPDF.
