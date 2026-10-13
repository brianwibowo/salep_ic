from __future__ import annotations

import pytest

from app.services.lead_service import extract_post_from_url


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/admin",
        "https://evilthreads.net/@user/post/1",
        "https://threads.net.evil.example/@user/post/1",
    ],
)
async def test_direct_url_analysis_rejects_non_social_hosts(url: str) -> None:
    with pytest.raises(ValueError, match="HTTPS Threads atau LinkedIn"):
        await extract_post_from_url(url)
