"""Google Sheets service — handles all spreadsheet operations."""

from __future__ import annotations

import json
from datetime import datetime

from app.agent.schemas import LeadRecord
from app.core.config import settings
from app.core.logging import logger

SHEET_HEADERS = [
    "lead_id",
    "source",
    "source_url",
    "author_name",
    "author_profile_url",
    "published_at",
    "matched_keyword",
    "content",
    "is_potential_lead",
    "intent",
    "industry",
    "needs",
    "pain_points",
    "recommended_services",
    "lead_score",
    "confidence",
    "evidence",
    "analyzed_at",
    "status",
]


def _lead_to_row(lead: LeadRecord) -> list[str]:
    """Convert a LeadRecord to a flat row for Google Sheets."""
    services_summary = ", ".join(
        f"{s.product_name} ({s.match_score}%)" for s in lead.recommended_services
    )
    return [
        lead.lead_id,
        lead.source,
        lead.source_url,
        lead.author_name or "",
        lead.author_profile_url or "",
        lead.published_at.isoformat() if lead.published_at else "",
        lead.matched_keyword,
        lead.content[:500],
        str(lead.is_potential_lead),
        lead.intent.value,
        lead.industry or "",
        ", ".join(lead.needs),
        ", ".join(lead.pain_points),
        services_summary,
        str(lead.lead_score),
        f"{lead.confidence:.2f}",
        " | ".join(lead.evidence),
        lead.analyzed_at.isoformat(),
        lead.status.value,
    ]


class GoogleSheetsService:
    """Service for persisting leads to Google Sheets."""

    def __init__(self):
        self._client = None
        self._sheet = None

    def _get_sheet(self):
        """Lazily initialize Google Sheets connection."""
        if self._sheet is not None:
            return self._sheet

        if not settings.google_sheets_id or not settings.google_service_account_json:
            logger.warning("Google Sheets not configured — operations will be skipped")
            return None

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            import os

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            sa_config = settings.google_service_account_json.strip()
            if sa_config.startswith("{"):
                info = json.loads(sa_config)
                creds = Credentials.from_service_account_info(info, scopes=scopes)
            elif os.path.exists(sa_config):
                creds = Credentials.from_service_account_file(sa_config, scopes=scopes)
            else:
                logger.warning(
                    "Service account file '%s' not found and not a JSON string — skipping Sheets write",
                    sa_config,
                )
                return None

            self._client = gspread.authorize(creds)
            self._sheet = self._client.open_by_key(settings.google_sheets_id).sheet1

            existing = self._sheet.row_values(1)
            if not existing:
                self._sheet.append_row(SHEET_HEADERS)
                logger.info("Initialized Google Sheets headers")

            logger.info("Google Sheets connected: %s", settings.google_sheets_id)
            return self._sheet

        except Exception as e:
            logger.error("Failed to connect to Google Sheets: %s", e)
            return None

    async def append_lead(self, lead: LeadRecord) -> bool:
        """Append a single lead to Google Sheets.

        Returns:
            True if successful, False otherwise.
        """
        sheet = self._get_sheet()
        if sheet is None:
            logger.warning("Skipping Sheets write — not configured")
            return False

        try:
            if await self.find_existing_lead(lead.source_url):
                logger.info("Duplicate lead skipped: %s", lead.source_url)
                return False

            row = _lead_to_row(lead)
            sheet.append_row(row)
            logger.info("Lead appended to Sheets: %s", lead.lead_id)
            return True

        except Exception as e:
            logger.error("Failed to append lead: %s", e)
            return False

    async def append_leads(self, leads: list[LeadRecord]) -> int:
        """Append multiple leads to Google Sheets.

        Returns:
            Number of successfully appended leads.
        """
        count = 0
        for lead in leads:
            if await self.append_lead(lead):
                count += 1
        return count

    async def find_existing_lead(self, source_url: str) -> bool:
        """Check if a lead with this source_url already exists.

        Returns:
            True if lead already exists in the sheet.
        """
        sheet = self._get_sheet()
        if sheet is None:
            return False

        try:
            source_url_col = SHEET_HEADERS.index("source_url") + 1
            all_urls = sheet.col_values(source_url_col)
            return source_url in all_urls
        except Exception as e:
            logger.error("Failed to check existing lead: %s", e)
            return False

    async def get_recent_leads(self, limit: int = 30) -> list[dict[str, Any]]:
        """Fetch the most recent leads from the Google Sheet in reverse chronological order."""
        sheet = self._get_sheet()
        if sheet is None:
            return []

        try:
            records = sheet.get_all_records()
            return list(reversed(records))[:limit]
        except Exception as e:
            logger.error("Failed to read leads from Sheets: %s", e)
            return []


sheets_service = GoogleSheetsService()
