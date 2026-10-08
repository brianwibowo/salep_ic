"""Public SPSE Nasional listing source adapter (homepage listings only)."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from app.agent.schemas import RawLead


SPSE_NATIONAL_URL = "https://spse.inaproc.id/nasional"


class _TenderParser(HTMLParser):
    """Extract tender rows from the public listing tables, without browser automation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, str]] = []
        self._row: dict[str, str] | None = None
        self._cell = False
        self._anchor = False
        self._anchor_href = ""
        self._anchor_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "tr":
            self._row = {"cells": "", "title": "", "url": ""}
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = True
        elif tag == "a" and self._row is not None:
            self._anchor = True
            self._anchor_href = attrs_dict.get("href") or ""
            self._anchor_text = ""

    def handle_data(self, data: str) -> None:
        if self._row is not None and self._cell:
            self._row["cells"] += f" {data.strip()}"
        if self._anchor:
            self._anchor_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor:
            text = " ".join(self._anchor_text.split())
            if "/lelang/" in self._anchor_href and text:
                self._row["title"] = text
                self._row["url"] = urljoin(SPSE_NATIONAL_URL, self._anchor_href)
            self._anchor = False
        elif tag in {"td", "th"}:
            self._cell = False
        elif tag == "tr" and self._row is not None:
            cells = " ".join(self._row["cells"].split())
            if self._row["url"] and self._row["title"]:
                self._row["cells"] = cells
                self.rows.append(self._row)
            self._row = None


class SPSESourceAdapter:
    """Fetch public tenders visible on the SPSE Nasional homepage."""

    @property
    def source_name(self) -> str:
        return "spse"

    async def search(
        self,
        keywords: list[str],
        start_date: str = "",
        end_date: str = "",
        limit: int = 50,
    ) -> list[RawLead]:
        del start_date, end_date  # The homepage does not expose a reliable publish date.
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                SPSE_NATIONAL_URL,
                headers={"User-Agent": "SALEP public procurement discovery/1.0"},
            )
            response.raise_for_status()

        parser = _TenderParser()
        parser.feed(response.text)
        terms = [term.casefold() for term in keywords if term.strip()]
        results: list[RawLead] = []
        seen: set[str] = set()
        for row in parser.rows:
            title = row["title"].strip()
            details = row["cells"]
            haystack = f"{title} {details}".casefold()
            matched = next((term for term in terms if term in haystack), None)
            if not matched or row["url"] in seen:
                continue
            seen.add(row["url"])
            results.append(
                RawLead(
                    source="spse",
                    source_url=row["url"],
                    author_name="SPSE Nasional",
                    content=f"Nama paket: {title}\nInformasi paket: {details}",
                    matched_keyword=matched,
                )
            )
            if len(results) >= limit:
                break
        return results

    async def health_check(self) -> dict[str, str]:
        return {"status": "ok", "source": SPSE_NATIONAL_URL}