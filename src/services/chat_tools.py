from datetime import UTC, datetime

from haystack.tools import tool

# ---------------------------------------------------------------------------
# Tools — plain functions; type hints + Annotated docs become the JSON schema
# ---------------------------------------------------------------------------


@tool
def get_current_time() -> str:
    """Return the current UTC date and time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()
