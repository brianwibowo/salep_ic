"""LinkedIn data source adapter — scrapes LinkedIn posts via Apify HarvestAPI Actor."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import httpx

from app.agent.schemas import RawLead
from app.core.config import settings
from app.core.logging import logger


class LinkedInSourceAdapter:
    """Scrapes LinkedIn posts using Apify HarvestAPI LinkedIn Post Search (No Cookies required)."""

    @property
    def source_name(self) -> str:
        return "linkedin"

    async def search(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        limit: int,
    ) -> list[RawLead]:
        """Search LinkedIn posts matching keywords via Apify."""
        if not settings.apify_api_token:
            logger.warning("LinkedInSource: APIFY_API_TOKEN is not set, skipping LinkedIn search.")
            return []

        leads: list[RawLead] = []
        actor_id = settings.linkedin_actor_id or "harvestapi~linkedin-post-search"
        api_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={settings.apify_api_token}"

        target_keywords = keywords[:2] if len(keywords) > 2 else keywords

        async with httpx.AsyncClient(timeout=120.0) as client:
            for kw in target_keywords:
                payload: dict[str, Any] = {
                    "searchQueries": [kw],
                    "sortBy": "date",
                    "maxPosts": min(limit, 20),
                }

                try:
                    logger.info("Querying LinkedIn via Apify for keyword: '%s'...", kw)
                    resp = await client.post(api_url, json=payload)
                    if resp.status_code not in (200, 201):
                        logger.error(
                            "LinkedIn Apify error (%d): %s",
                            resp.status_code,
                            resp.text[:200],
                        )
                        continue

                    items = resp.json()
                    if not isinstance(items, list):
                        logger.warning("LinkedIn Apify unexpected format: %s", type(items))
                        continue

                    logger.info("LinkedIn returned %d raw items for '%s'", len(items), kw)
                    for item in items:
                        lead = self._parse_item(item, matched_kw=kw)
                        if lead and lead.content.strip():
                            leads.append(lead)

                except httpx.TimeoutException:
                    logger.warning("LinkedIn search timed out for keyword: '%s'", kw)
                except Exception as e:
                    logger.error("LinkedIn search failed for '%s': %s", kw, e)

        return leads[:limit]

    def _parse_item(self, item: dict[str, Any], matched_kw: str) -> RawLead | None:
        """Parse raw Apify LinkedIn item into a normalized RawLead."""
        content = item.get("content") or ""
        if not content:
            return None

        post_url = item.get("linkedinUrl") or item.get("shareLinkedinUrl") or ""
        author = item.get("author") or {}
        author_name = author.get("name") or author.get("publicIdentifier") or "linkedin_user"
        author_url = author.get("linkedinUrl") or ""

        # Timestamp
        published_at = None
        posted_at_date = item.get("postedAt", {}).get("date")
        if posted_at_date:
            try:
                published_at = datetime.fromisoformat(posted_at_date.replace("Z", "+00:00"))
            except Exception:
                published_at = None

        return RawLead(
            source=self.source_name,
            source_url=post_url,
            author_name=author_name,
            author_profile_url=author_url if author_url else None,
            published_at=published_at,
            content=content,
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
