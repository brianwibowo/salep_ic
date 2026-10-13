"""Pure parsers for captured public Si-RUP and SPSE responses.

The live fetchers can change independently from these parsers. Contract tests
use sanitized fixtures so a portal markup/API change is visible in CI.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from app.domain.procurement import ProcurementPackage, ProcurementTrack


def clean_text(value: Any) -> str:
    return " ".join(re.sub(r"<[^>]*>", " ", str(value or "")).split())


def parse_flag(value: Any, *, positive_markers: tuple[str, ...]) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    text = clean_text(value).casefold()
    if not text:
        return None
    if any(marker in text for marker in positive_markers):
        return True
    if text in {"false", "0", "tidak", "bukan"} or any(marker in text for marker in ("impor", "bukan usaha")):
        return False
    return None


def parse_amount(value: Any) -> float | None:
    """Parse common Indonesian Rupiah strings into a numeric amount."""

    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Rp", "").replace("rp", "").replace(" ", "")
    multiplier = 1.0
    if text.casefold().endswith("m"):
        multiplier = 1_000_000.0
        text = text[:-1]
    elif text.casefold().endswith("jt"):
        multiplier = 1_000_000.0
        text = text[:-2]
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    elif "," in text:
        head, tail = text.rsplit(",", 1)
        text = f"{head.replace(',', '')}.{tail}"
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def normalize_stage_code(label: str | None) -> str | None:
    clean = " ".join((label or "").split()).casefold()
    if not clean:
        return None
    if "sudah selesai" in clean or clean == "selesai":
        return "tender_completed"
    if "pengumuman" in clean:
        return "announcement"
    if "aanwijzing" in clean or "pemberian penjelasan" in clean:
        return "clarification"
    if "upload" in clean and "penawaran" in clean:
        return "proposal_upload"
    if "evaluasi" in clean:
        return "evaluation"
    if "pemenang" in clean:
        return "winner_announcement"
    return re.sub(r"[^a-z0-9]+", "_", clean).strip("_") or None


def _source_url(base_url: str, row: dict[str, Any], default_path: str) -> str:
    fallback = urljoin(base_url, default_path)
    candidate = str(row.get("source_url") or "").strip()
    expected_host = (urlparse(base_url).hostname or "").casefold().rstrip(".")
    parsed = urlparse(candidate)
    if parsed.scheme == "https" and (parsed.hostname or "").casefold().rstrip(".") == expected_host:
        return candidate
    return fallback


def parse_sirup_rows(
    payload: dict[str, Any],
    *,
    fiscal_year: int,
    base_url: str = "https://sirup.inaproc.id/",
) -> list[ProcurementPackage]:
    """Parse a captured Si-RUP table payload into canonical packages."""

    results: list[ProcurementPackage] = []
    for row in payload.get("data", []):
        if isinstance(row, list):
            if len(row) < 12:
                continue
            row = {
                "external_id": row[11],
                "package_name": row[1],
                "budget_amount": row[2],
                "procurement_type": row[3],
                "local_content_flag": row[4],
                "small_business_flag": row[5],
                "procurement_method": row[6],
                "organization": row[8],
                "satker": row[9],
                "location": row[10],
            }
        package_id = str(row.get("external_id") or row.get("idPaket") or row.get("id") or "").strip()
        name = clean_text(row.get("package_name") or row.get("nama_paket") or row.get("paket"))
        if not package_id or not name:
            continue
        results.append(
            ProcurementPackage(
                source="sirup",
                track=ProcurementTrack.SIRUP,
                external_id=package_id,
                rup_id=package_id,
                package_name=name,
                organization=row.get("organization") or row.get("klpd") or row.get("kldi"),
                satker=row.get("satker") or row.get("satuanKerja"),
                location=row.get("location") or row.get("lokasi"),
                procurement_type=row.get("procurement_type") or row.get("jenisPengadaan") or row.get("jenis"),
                fiscal_year=fiscal_year,
                budget_amount=parse_amount(row.get("budget_amount") or row.get("pagu")),
                procurement_method=row.get("procurement_method") or row.get("metode"),
                local_content_flag=parse_flag(
                    row.get("local_content_flag") if row.get("local_content_flag") is not None else row.get("isPDN"),
                    positive_markers=("produk dalam negeri", "dalam negeri"),
                ),
                small_business_flag=parse_flag(
                    row.get("small_business_flag") if row.get("small_business_flag") is not None else row.get("isUMK"),
                    positive_markers=("usaha kecil", "koperasi"),
                ),
                source_url=_source_url(base_url, row, f"sirup/rup/detailPaketPenyedia2020?idPaket={package_id}"),
            )
        )
    return results


def parse_spse_rows(
    payload: dict[str, Any],
    *,
    track: ProcurementTrack,
    fiscal_year: int,
    base_url: str = "https://spse.inaproc.id/nasional/",
) -> list[ProcurementPackage]:
    """Parse a captured SPSE table response for any public track."""

    results: list[ProcurementPackage] = []
    for raw_row in payload.get("data", []):
        if isinstance(raw_row, list):
            if len(raw_row) < 5:
                continue
            row: dict[str, Any] = {
                "external_id": raw_row[0],
                "package_name": raw_row[1],
                "organization": raw_row[2],
                "current_stage_label": raw_row[3],
                "hps_amount": raw_row[4],
            }
        elif isinstance(raw_row, dict):
            row = raw_row
        else:
            continue

        external_id = str(row.get("external_id") or row.get("kode") or row.get("kode_tender") or "").strip()
        package_name = clean_text(row.get("package_name") or row.get("nama_paket"))
        if not external_id or not package_name:
            continue
        stage_label = clean_text(row.get("current_stage_label") or row.get("tahap")) or None
        contract_status = clean_text(row.get("contract_status") or row.get("status_kontrak")) or None
        detail_paths = {
            ProcurementTrack.TENDER: f"lelang/{external_id}/pengumumanlelang",
            ProcurementTrack.NON_TENDER: f"nontender/{external_id}/pengumumanpl",
            ProcurementTrack.PENCATATAN_NON_TENDER: f"pencatatan/pengumumannonspk?id={external_id}",
            ProcurementTrack.SWAKELOLA: f"swakelola/{external_id}/pengumuman",
            ProcurementTrack.DARURAT: f"darurat/pengumumandarurat?id={external_id}",
        }
        detail_path = detail_paths.get(track, f"lelang/{external_id}/pengumumanlelang")
        results.append(
            ProcurementPackage(
                source="spse",
                track=track,
                external_id=external_id,
                tender_id=external_id,
                package_name=package_name,
                organization=row.get("organization") or row.get("instansi"),
                satker=row.get("satker"),
                location=row.get("location") or row.get("lokasi"),
                procurement_type=row.get("procurement_type") or row.get("jenis"),
                procurement_method=row.get("procurement_method") or row.get("metode"),
                fiscal_year=fiscal_year,
                hps_amount=parse_amount(row.get("hps_amount") or row.get("hps")),
                contract_type=row.get("contract_type"),
                current_stage_code=normalize_stage_code(stage_label),
                current_stage_label=stage_label,
                contract_status=contract_status,
                source_url=_source_url(base_url, row, detail_path),
            )
        )
    return results

