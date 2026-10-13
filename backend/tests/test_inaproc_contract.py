"""Contract tests for the Phase 0 INAPROC schema and captured responses."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.procurement import FinalReason, ProcurementTrack, derive_final_reason, final_reason_label, normalize_final_reason
from app.sources.inaproc.parsers import parse_sirup_rows, parse_spse_rows
from app.services.final_analytics import calculate_sales_priority, classify_service_category


FIXTURES = Path(__file__).parent / "fixtures" / "inaproc"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_sirup_fixture_maps_to_canonical_schema() -> None:
    packages = parse_sirup_rows(load_fixture("sirup_listing.json"), fiscal_year=2026)

    assert len(packages) == 2
    managed = packages[0]
    assert managed.source == "sirup"
    assert managed.track is ProcurementTrack.SIRUP
    assert managed.rup_id == "62222157"
    assert managed.budget_amount == 450_000_000
    assert managed.source_url.endswith("idPaket=62222157")


def test_sirup_datatable_array_uses_the_id_column_not_location() -> None:
    payload = {
        "data": [[
            1,
            "Managed Service",
            "Rp 100.000.000,00",
            "Jasa Lainnya",
            "Produk Dalam Negeri",
            "Usaha Kecil/Koperasi",
            "Pengadaan Langsung",
            "January 2026",
            "Instansi",
            "Satker",
            "Jakarta",
            "62222999",
        ]]
    }
    packages = parse_sirup_rows(payload, fiscal_year=2026)
    assert packages[0].external_id == "62222999"


def test_spse_fixture_preserves_all_final_reasons() -> None:
    packages = parse_spse_rows(
        load_fixture("spse_final.json"),
        track=ProcurementTrack.TENDER,
        fiscal_year=2026,
    )

    reasons = [
        derive_final_reason(
            current_stage_code=package.current_stage_code,
            current_stage_label=package.current_stage_label,
            contract_status=package.contract_status,
        )
        for package in packages
    ]
    assert reasons == [
        FinalReason.CONTRACT_COMPLETED,
        FinalReason.CONTRACT_TERMINATED,
        FinalReason.CONTRACT_STOPPED,
        FinalReason.TENDER_COMPLETED_NO_CONTRACT,
    ]
    assert packages[0].hps_amount == 2_500_000_000


def test_active_tender_is_not_final() -> None:
    assert derive_final_reason(
        current_stage_code="proposal_upload",
        current_stage_label="Upload Dokumen Penawaran",
        contract_status=None,
    ) is None


def test_final_reason_labels_are_stable_for_chart_legends() -> None:
    assert final_reason_label(FinalReason.CONTRACT_COMPLETED) == "Kontrak selesai"
    assert final_reason_label(FinalReason.CONTRACT_TERMINATED) == "Pemutusan kontrak"
    assert final_reason_label(FinalReason.CONTRACT_STOPPED) == "Penghentian kontrak"


def test_final_reason_normalization_handles_portal_variants() -> None:
    assert normalize_final_reason(contract_status="Kontrak Selesai") is FinalReason.CONTRACT_COMPLETED
    assert normalize_final_reason(contract_status="Kontrak Diputus") is FinalReason.CONTRACT_TERMINATED
    assert normalize_final_reason(current_stage_label="Tender sudah selesai") is FinalReason.TENDER_COMPLETED_NO_CONTRACT


def test_final_sales_taxonomy_is_explainable() -> None:
    category, label, evidence = classify_service_category("Pemeliharaan server dan monitoring 24/7")
    assert category == "managed_service"
    assert "pemeliharaan server" in evidence
    assert "Managed service" in label
    score, priority, recommendation = calculate_sales_priority(
        category=category,
        reason=FinalReason.TENDER_COMPLETED_NO_CONTRACT,
        track=ProcurementTrack.TENDER.value,
        budget_amount=500_000_000,
        hps_amount=None,
    )
    assert score >= 65
    assert priority == "high"
    assert recommendation


@pytest.mark.parametrize(
    ("fixture_key", "track"),
    [
        ("tender", ProcurementTrack.TENDER),
        ("non_tender", ProcurementTrack.NON_TENDER),
        ("pencatatan_non_tender", ProcurementTrack.PENCATATAN_NON_TENDER),
        ("swakelola", ProcurementTrack.SWAKELOLA),
        ("darurat", ProcurementTrack.DARURAT),
    ],
)
def test_each_public_spse_track_has_the_same_canonical_contract(fixture_key: str, track: ProcurementTrack) -> None:
    payload = load_fixture("spse_tracks.json")[fixture_key]
    packages = parse_spse_rows(payload, track=track, fiscal_year=2026)

    assert len(packages) == 1
    assert packages[0].source == "spse"
    assert packages[0].track is track
    assert packages[0].fiscal_year == 2026
    assert packages[0].source_url.startswith("https://spse.inaproc.id/nasional/")
    assert packages[0].external_id in packages[0].source_url

