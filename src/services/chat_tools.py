from typing import Annotated

from haystack.tools import tool
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Tools — plain functions; type hints + Annotated docs become the JSON schema
# ---------------------------------------------------------------------------


@tool
def get_current_time() -> str:
    """Return the current UTC date and time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()
