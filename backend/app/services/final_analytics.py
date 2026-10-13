"""Deterministic Final analytics over normalized PostgreSQL procurement data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from app.core.config import settings
from app.domain.procurement import (
    FINAL_REASON_LABELS,
    FinalReason,
    ProcurementTrack,
    normalize_final_reason,
)

try:  # Keep the API importable in parser-only development environments.
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.db.engine import build_engine
    from app.db.models import ProcurementPackageModel
except ModuleNotFoundError:  # pragma: no cover - production installs requirements.txt
    select = None  # type: ignore[assignment]
    Session = Any  # type: ignore[misc,assignment]
    build_engine = None  # type: ignore[assignment]
    ProcurementPackageModel = Any  # type: ignore[assignment,misc]


DEFAULT_FINAL_YEARS = 2

SERVICE_CATEGORY_LABELS = {
    "managed_service": "Managed service & operasi TI",
    "cloud_infrastructure": "Cloud & infrastruktur",
    "cybersecurity": "Cybersecurity",
    "software_application": "Software & aplikasi",
    "network_connectivity": "Jaringan & konektivitas",
    "data_platform": "Data platform & integrasi",
    "hardware_endpoint": "Hardware & endpoint",
    "other_it": "IT lainnya",
    "non_it": "Non-IT / perlu validasi",
}

_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("managed_service", ("managed service", "monitoring server", "pemeliharaan server", "operasional server", "dukungan teknis", "maintenance aplikasi", "helpdesk", "service level", "sla")),
    ("cybersecurity", ("keamanan siber", "cyber security", " cybersecurity", "pentest", "penetration test", "vulnerability", "keamanan informasi", "iso 27001")),
    ("cloud_infrastructure", ("cloud", "server", "data center", "data centre", "hosting", "vps", "backup", "disaster recovery", "virtualisasi")),
    ("network_connectivity", ("jaringan", "network", "internet", "bandwidth", "wifi", "router", "switch", "fiber optic", "konektivitas")),
    ("data_platform", ("database", "data platform", "satu data", "integrasi api", "big data", "analitik data", "dashboard")),
    ("software_application", ("aplikasi", "software", "sistem informasi", "erp", "crm", "portal", "website", "web", "mobile")),
    ("hardware_endpoint", ("komputer", "laptop", "perangkat keras", "hardware", "printer", "pengadaan pc", "cctv")),
)


def classify_service_category(*values: str | None) -> tuple[str, str, list[str]]:
    """Classify IT opportunity using transparent keyword evidence."""
    haystack = " ".join(value or "" for value in values).casefold()
    best_category = "non_it"
    best_matches: list[str] = []
    for category, keywords in _CATEGORY_RULES:
        matches = [keyword.strip() for keyword in keywords if keyword.strip() in haystack]
        if len(matches) > len(best_matches):
            best_category, best_matches = category, matches
    if best_category == "non_it" and any(token in haystack for token in ("pengadaan", "jasa", "barang")):
        best_category = "other_it"
    return best_category, SERVICE_CATEGORY_LABELS[best_category], best_matches


def calculate_sales_priority(
    *,
    category: str,
    reason: FinalReason,
    track: str,
    budget_amount: float | None,
    hps_amount: float | None,
) -> tuple[int, str, str]:
    """Return score, priority and a human-readable next action."""
    score = 25 if category in {"managed_service", "cloud_infrastructure", "cybersecurity", "network_connectivity"} else 10
    score += 20 if reason is FinalReason.TENDER_COMPLETED_NO_CONTRACT else 12 if reason in {FinalReason.CONTRACT_TERMINATED, FinalReason.CONTRACT_STOPPED} else 4
    score += 10 if track in {ProcurementTrack.TENDER.value, ProcurementTrack.NON_TENDER.value} else 4
    amount = hps_amount or budget_amount or 0
    score += 15 if amount >= 1_000_000_000 else 10 if amount >= 250_000_000 else 4 if amount >= 50_000_000 else 0
    score = min(score, 100)
    priority = "high" if score >= 65 else "medium" if score >= 40 else "low"
    if reason in {FinalReason.CONTRACT_TERMINATED, FinalReason.CONTRACT_STOPPED}:
        action = "Validasi akar masalah kontrak, lalu tawarkan recovery/managed service dengan PIC TI."
    elif reason is FinalReason.TENDER_COMPLETED_NO_CONTRACT:
        action = "Lakukan account mapping dan pantau paket lanjutan atau kontrak pengganti."
    elif category == "managed_service":
        action = "Prioritaskan discovery SLA, monitoring, support 24/7, dan kapasitas operasi."
    else:
        action = "Validasi kebutuhan TI dan identifikasi PIC procurement serta pengguna teknis."
    return score, priority, action


@dataclass(frozen=True)
class FinalRecord:
    package_id: str
    source: str
    track: str
    external_id: str
    package_name: str
    organization: str | None
    satker: str | None
    location: str | None
    fiscal_year: int
    budget_amount: float | None
    hps_amount: float | None
    procurement_type: str | None
    procurement_method: str | None
    contract_type: str | None
    current_stage_code: str | None
    current_stage_label: str | None
    contract_status: str | None
    reason: str
    reason_label: str
    source_url: str
    last_seen_at: str
    service_category: str
    service_category_label: str
    category_evidence: list[str]
    managed_service_fit: int
    sales_priority: str
    sales_priority_score: int
    sales_recommendation: str


def selected_years(years: Iterable[int] | None, *, current_year: int | None = None) -> list[int]:
    if years:
        return sorted({int(year) for year in years})
    active = current_year or __import__("datetime").datetime.now().year
    return [active - 1, active]


def reason_for_package(row: Any) -> FinalReason | None:
    return normalize_final_reason(
        current_stage_code=getattr(row, "current_stage_code", None),
        current_stage_label=getattr(row, "current_stage_label", None),
        contract_status=getattr(row, "current_contract_status", None),
    )


def _record(row: Any, reason: FinalReason) -> FinalRecord:
    category, category_label, category_evidence = classify_service_category(
        row.package_name, getattr(row, "description", None), row.procurement_type, row.procurement_method,
    )
    priority_score, priority, recommendation = calculate_sales_priority(
        category=category,
        reason=reason,
        track=row.track,
        budget_amount=row.budget_amount,
        hps_amount=row.hps_amount,
    )
    return FinalRecord(
        package_id=row.id,
        source=row.source,
        track=row.track,
        external_id=row.external_id,
        package_name=row.package_name,
        organization=row.organization,
        satker=row.satker,
        location=row.location,
        fiscal_year=row.fiscal_year,
        budget_amount=row.budget_amount,
        hps_amount=row.hps_amount,
        procurement_type=row.procurement_type,
        procurement_method=row.procurement_method,
        contract_type=row.contract_type,
        current_stage_code=row.current_stage_code,
        current_stage_label=row.current_stage_label,
        contract_status=row.current_contract_status,
        reason=reason.value,
        reason_label=FINAL_REASON_LABELS[reason],
        source_url=row.source_url,
        last_seen_at=row.last_seen_at.isoformat() if row.last_seen_at else "",
        service_category=category,
        service_category_label=category_label,
        category_evidence=category_evidence,
        managed_service_fit=priority_score if category != "non_it" else max(0, priority_score - 15),
        sales_priority=priority,
        sales_priority_score=priority_score,
        sales_recommendation=recommendation,
    )


class FinalAnalyticsService:
    def __init__(self, database_url: str | None = None) -> None:
        if select is None or build_engine is None:
            raise RuntimeError("Dependensi PostgreSQL belum terpasang; install backend/requirements.txt")
        self.engine = build_engine(database_url or settings.database_url)

    def records(
        self,
        *,
        fiscal_years: Iterable[int] | None = None,
        reasons: Iterable[FinalReason | str] | None = None,
        tracks: Iterable[ProcurementTrack | str] | None = None,
        categories: Iterable[str] | None = None,
        search: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[FinalRecord], int]:
        years = selected_years(fiscal_years)
        wanted_reasons = {str(value.value if isinstance(value, FinalReason) else value) for value in (reasons or [])}
        wanted_tracks = {str(value.value if isinstance(value, ProcurementTrack) else value) for value in (tracks or [])}
        wanted_categories = {str(value) for value in (categories or [])}
        normalized_search = search.casefold().strip()
        with Session(self.engine) as session:
            query = select(ProcurementPackageModel).where(
                ProcurementPackageModel.source == "spse",
                ProcurementPackageModel.fiscal_year.in_(years),
            ).order_by(ProcurementPackageModel.fiscal_year.desc(), ProcurementPackageModel.last_seen_at.desc())
            rows = session.scalars(query).all()

        final_rows: list[FinalRecord] = []
        for row in rows:
            reason = reason_for_package(row)
            if reason is None or (wanted_reasons and reason.value not in wanted_reasons):
                continue
            if wanted_tracks and row.track not in wanted_tracks:
                continue
            category, _, _ = classify_service_category(row.package_name, getattr(row, "description", None), row.procurement_type, row.procurement_method)
            if wanted_categories and category not in wanted_categories:
                continue
            if normalized_search and normalized_search not in " ".join(filter(None, (row.package_name, row.organization, row.satker, row.location))).casefold():
                continue
            final_rows.append(_record(row, reason))
        total = len(final_rows)
        return final_rows[offset : offset + limit], total

    def summary(
        self,
        *,
        fiscal_years: Iterable[int] | None = None,
        reasons: Iterable[FinalReason | str] | None = None,
        tracks: Iterable[ProcurementTrack | str] | None = None,
        categories: Iterable[str] | None = None,
        search: str = "",
    ) -> dict[str, Any]:
        rows, total = self.records(
            fiscal_years=fiscal_years,
            reasons=reasons,
            tracks=tracks,
            categories=categories,
            search=search,
            limit=100_000,
        )
        by_reason: dict[str, dict[str, Any]] = {
            reason.value: {"reason": reason.value, "label": FINAL_REASON_LABELS[reason], "count": 0, "budget_amount": 0.0, "hps_amount": 0.0}
            for reason in FinalReason
        }
        by_year: dict[str, dict[str, Any]] = defaultdict(lambda: {"fiscal_year": 0, "count": 0, "budget_amount": 0.0, "hps_amount": 0.0})
        by_track: dict[str, dict[str, Any]] = defaultdict(lambda: {"track": "", "count": 0, "budget_amount": 0.0, "hps_amount": 0.0})
        by_organization: dict[str, dict[str, Any]] = defaultdict(lambda: {"organization": "", "count": 0, "budget_amount": 0.0, "hps_amount": 0.0, "high_priority_count": 0})
        by_category: dict[str, dict[str, Any]] = defaultdict(lambda: {"category": "", "label": "", "count": 0, "budget_amount": 0.0, "hps_amount": 0.0, "high_priority_count": 0, "average_managed_service_fit": 0.0})
        by_priority: dict[str, dict[str, Any]] = defaultdict(lambda: {"priority": "", "count": 0, "budget_amount": 0.0, "hps_amount": 0.0})
        total_budget = 0.0
        total_hps = 0.0
        for row in rows:
            reason = by_reason[row.reason]
            reason["count"] += 1
            reason["budget_amount"] += row.budget_amount or 0.0
            reason["hps_amount"] += row.hps_amount or 0.0
            year = by_year[str(row.fiscal_year)]
            year["fiscal_year"] = row.fiscal_year
            year["count"] += 1
            year["budget_amount"] += row.budget_amount or 0.0
            year["hps_amount"] += row.hps_amount or 0.0
            track = by_track[row.track]
            track["track"] = row.track
            track["count"] += 1
            track["budget_amount"] += row.budget_amount or 0.0
            track["hps_amount"] += row.hps_amount or 0.0
            organization_name = row.organization or "Instansi tidak diketahui"
            organization = by_organization[organization_name]
            organization["organization"] = organization_name
            organization["count"] += 1
            organization["budget_amount"] += row.budget_amount or 0.0
            organization["hps_amount"] += row.hps_amount or 0.0
            organization["high_priority_count"] += int(row.sales_priority == "high")
            category = by_category[row.service_category]
            category["category"] = row.service_category
            category["label"] = row.service_category_label
            category["count"] += 1
            category["budget_amount"] += row.budget_amount or 0.0
            category["hps_amount"] += row.hps_amount or 0.0
            category["high_priority_count"] += int(row.sales_priority == "high")
            category["average_managed_service_fit"] += row.managed_service_fit
            priority = by_priority[row.sales_priority]
            priority["priority"] = row.sales_priority
            priority["count"] += 1
            priority["budget_amount"] += row.budget_amount or 0.0
            priority["hps_amount"] += row.hps_amount or 0.0
            total_budget += row.budget_amount or 0.0
            total_hps += row.hps_amount or 0.0
        for value in by_reason.values():
            value["percentage"] = round((value["count"] / total * 100) if total else 0.0, 2)
        for value in by_category.values():
            value["average_managed_service_fit"] = round(value["average_managed_service_fit"] / value["count"], 1) if value["count"] else 0.0
        return {
            "fiscal_years": selected_years(fiscal_years),
            "total": total,
            "total_budget_amount": total_budget,
            "total_hps_amount": total_hps,
            "by_reason": list(by_reason.values()),
            "by_year": sorted(by_year.values(), key=lambda value: value["fiscal_year"]),
            "by_track": sorted(by_track.values(), key=lambda value: value["count"], reverse=True),
            "by_organization": sorted(by_organization.values(), key=lambda value: (value["high_priority_count"], value["hps_amount"], value["count"]), reverse=True)[:25],
            "by_category": sorted(by_category.values(), key=lambda value: value["count"], reverse=True),
            "by_priority": sorted(by_priority.values(), key=lambda value: {"high": 0, "medium": 1, "low": 2}.get(value["priority"], 3)),
            "recommendations": [
                {
                    "package_id": row.package_id,
                    "package_name": row.package_name,
                    "organization": row.organization,
                    "service_category": row.service_category,
                    "service_category_label": row.service_category_label,
                    "sales_priority": row.sales_priority,
                    "sales_priority_score": row.sales_priority_score,
                    "sales_recommendation": row.sales_recommendation,
                    "source_url": row.source_url,
                }
                for row in sorted(rows, key=lambda value: (value.sales_priority_score, value.hps_amount or value.budget_amount or 0), reverse=True)[:10]
            ],
        }
