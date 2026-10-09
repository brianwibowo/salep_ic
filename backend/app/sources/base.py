"""Base source adapter protocol — all source adapters implement this interface."""

from __future__ import annotations

from typing import Protocol

from app.agent.schemas import RawLead


class SourceAdapter(Protocol):
    """Protocol for data source adapters.

    Each adapter searches a specific source (e.g., social media, forums)
    and returns normalized RawLead objects.
    """

    @property
    def source_name(self) -> str:
        """Unique identifier for this source."""
        ...

    async def search(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        limit: int,
    ) -> list[RawLead]:
        """Search the source for posts matching keywords within a date range.

        Args:
            keywords: List of search terms.
            start_date: ISO date string (YYYY-MM-DD).
            end_date: ISO date string (YYYY-MM-DD).
            limit: Maximum number of results.

        Returns:
            List of normalized RawLead objects.
        """
        ...

    async def health_check(self) -> dict:
        """Check if the source is available.

        Returns:
            Dict with 'status' key ('ok' or 'unavailable') and optional 'reason'.
        """
        ...
