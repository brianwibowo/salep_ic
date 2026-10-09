"""Threads data source adapter — scrapes Meta Threads via Apify Actor."""

from __future__ import annotations

from datetime import datetime, date
from typing import Any
import httpx

from app.agent.schemas import RawLead
from app.core.config import settings
from app.core.logging import logger


class ThreadsSourceAdapter:
    """Scrapes Meta Threads posts using Apify threads-search-scraper."""

    @property
    def source_name(self) -> str:
        return "threads"

    async def search(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        limit: int,
    ) -> list[RawLead]:
        """Search Threads posts matching keywords via Apify."""
        if not settings.apify_api_token:
            logger.warning("ThreadsSource: APIFY_API_TOKEN is not set, skipping Threads search.")
            raise RuntimeError("APIFY_API_TOKEN belum dikonfigurasi")

        leads: list[RawLead] = []
        actor_id = settings.threads_actor_id or "igview-owner~threads-search-scraper"
        api_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={settings.apify_api_token}"

        # Apify actor minimum maxPosts is 20
        max_posts = max(20, min(limit, 50))

        # The caller provides explicit bounded queries; do not discard selected keywords.
        target_keywords = list(dict.fromkeys(keywords))

        async with httpx.AsyncClient(timeout=120.0) as client:
            for kw in target_keywords:
                # Do NOT pass after/before to this actor as date filtering breaks recent Threads queries
                payload: dict[str, Any] = {
                    "searchQuery": kw,
                    "sort": "recent",
                    "maxPosts": max_posts,
                }

                try:
                    logger.info("Querying Threads via Apify for keyword: '%s'...", kw)
                    resp = await client.post(api_url, json=payload)
                    if resp.status_code == 403 or "Monthly usage hard limit exceeded" in resp.text:
                        raise RuntimeError(
                            "Apify menolak akses atau batas pemakaian tercapai. Periksa token dan kuota akun Apify."
                        )
                    if resp.status_code not in (200, 201):
                        raise RuntimeError(f"Apify mengembalikan HTTP {resp.status_code}")

                    items = resp.json()
                    if not isinstance(items, list):
                        logger.warning("Threads Apify unexpected format: %s", type(items))
                        raise RuntimeError("Format respons Apify tidak sesuai")

                    logger.info("Threads returned %d raw items for '%s'", len(items), kw)
                    for item in items:
                        lead = self._parse_item(item, matched_kw=kw)
                        if lead and lead.content.strip():
                            if lead.published_at and not (date.fromisoformat(start_date) <= lead.published_at.date() <= date.fromisoformat(end_date)):
                                continue
                            leads.append(lead)

                except httpx.TimeoutException:
                    raise RuntimeError("Apify timeout. Periksa run di Apify sebelum mencoba lagi.") from None
                except httpx.HTTPError:
                    raise RuntimeError("Koneksi ke Apify gagal") from None

        return leads[:limit]

    def _parse_item(self, item: dict[str, Any], matched_kw: str) -> RawLead | None:
        """Parse raw Apify item into a normalized RawLead."""
        # Post text
        caption = item.get("captionText") or item.get("caption") or item.get("text_content") or ""
        if not caption:
            return None

        # Qualification belongs to the IT-wide agent, not a web-only lexical filter.

        # URL
        post_url = item.get("postUrl") or item.get("thread_url") or ""
        post_code = item.get("postCode") or item.get("code") or ""
        if not post_url and post_code:
            post_url = f"https://www.threads.net/t/{post_code}"

        # Author
        user_info = item.get("user") or {}
        username = item.get("username") or user_info.get("username") or ""
        author_name = user_info.get("full_name") or username or "threads_user"
        author_url = f"https://www.threads.net/@{username}" if username else None

        # Timestamp
        published_at = None
        taken_at_iso = item.get("takenAtISO") or item.get("timestamp")
        if taken_at_iso:
            try:
                published_at = datetime.fromisoformat(taken_at_iso.replace("Z", "+00:00"))
            except Exception:
                published_at = None

        return RawLead(
            source=self.source_name,
            source_url=post_url,
            author_name=author_name,
            author_profile_url=author_url,
            published_at=published_at,
            content=caption,
            matched_keyword=matched_kw,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check if Apify token is configured and accessible."""
        if not settings.apify_api_token:
            return {"status": "unavailable", "reason": "APIFY_API_TOKEN is not configured"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"https://api.apify.com/v2/users/me?token={settings.apify_api_token}"
                )
                if res.status_code == 200:
                    return {"status": "ok", "provider": "apify"}
                return {"status": "unavailable", "reason": f"Apify returned {res.status_code}"}
        except Exception as e:
            return {"status": "unavailable", "reason": str(e)}
