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
- An OpenAI-compatible API key and endpoint

## Configuration

Create a `.env` file or provide environment variables before running the app.

Common variables:
