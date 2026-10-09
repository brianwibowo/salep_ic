"""Google Sheets service — handles all spreadsheet operations."""

from __future__ import annotations

import json
from datetime import datetime

from app.agent.schemas import LeadRecord
from app.core.config import settings
from app.core.logging import logger

SHEET_HEADERS = [
    "Tanggal",
    "Platform",
    "Nama Prospek",
    "Link Postingan",
    "Isi Kebutuhan",
    "Detail Kebutuhan",
    "Layanan Ditawarkan",
    "Skor Minat",
    "Status Sales",
]


def _lead_to_row(lead: LeadRecord) -> list[str]:
    """Convert a LeadRecord to a clean, sales-focused flat row for Google Sheets."""
    pub_date = ""
    if lead.published_at:
        pub_date = lead.published_at.strftime("%Y-%m-%d")
    elif lead.analyzed_at:
        pub_date = lead.analyzed_at.strftime("%Y-%m-%d")

    platform = lead.source.capitalize()
    author = lead.author_name or "Prospek"
    needs_summary = ", ".join(lead.needs) if lead.needs else "Pembuatan Website"
    services_summary = ", ".join(s.product_name for s in lead.recommended_services) or "Web Development"

    return [
        pub_date,
        platform,
        author,
        lead.source_url,
        lead.content[:500],
        needs_summary,
        services_summary,
        str(lead.lead_score),
        "Belum Dihubungi",
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
            source_url_col = SHEET_HEADERS.index("Link Postingan") + 1
            all_urls = sheet.col_values(source_url_col)
            return source_url in all_urls
        except Exception as e:
            logger.error("Failed to check existing lead: %s", e)
            return False

    async def get_recent_leads(self, limit: int = 30) -> list[dict[str, any]]:
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
