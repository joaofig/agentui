# agentui

A web-based AI agent playground built with NiceGUI, Haystack, and OpenAI-compatible chat models.

## Overview

`agentui` provides a browser-based interface for interacting with an AI chat agent. It includes:

- A NiceGUI web UI
- Login and inactivity-based session handling
- Role-based admin access
- A chat-oriented agent workspace
- Haystack-based agent integration
- OpenAI-compatible chat model configuration through environment variables
- PostgreSQL/pgvector support for vector-enabled storage workflows

## Requirements

- Python >= 3.14
- `uv`
- PostgreSQL with pgvector, if using the database-backed functionality
- LibreOffice Writer, Calc, and Impress, for thumbnails of Office and OpenDocument files
- An OpenAI-compatible API key and endpoint

## Configuration

Create a `.env` file or provide environment variables before running the app.

Common variables:

## Document thumbnails

The authenticated `GET /api/rag-documents/{rag_doc_id}/thumbnail` endpoint renders
the first page of a PDF, Word, Excel, PowerPoint, or OpenDocument file as an image.
It uses the document's `content` and `content_type` fields. The default response
is a 64-by-64 JPEG; `format=png` selects PNG, and `width` and `height` independently
set the output canvas dimensions (each from 1 to 1024 pixels).

For example, `/api/rag-documents/42/thumbnail?format=png&width=128&height=96`
returns a padded 128-by-96 PNG. LibreOffice must be installed locally for Office
and OpenDocument conversions; the application container installs the Writer,
Calc, and Impress components automatically.
