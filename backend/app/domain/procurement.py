"""Canonical procurement status rules for Si-RUP/SPSE and the Final view."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProcurementTrack(str, Enum):
    SIRUP = "sirup"
    TENDER = "tender"
    NON_TENDER = "non_tender"
    PENCATATAN_NON_TENDER = "pencatatan_non_tender"
    SWAKELOLA = "swakelola"
    DARURAT = "darurat"


class FinalReason(str, Enum):
    CONTRACT_COMPLETED = "contract_completed"
    CONTRACT_TERMINATED = "contract_terminated"
    CONTRACT_STOPPED = "contract_stopped"
    TENDER_COMPLETED_NO_CONTRACT = "tender_completed_no_contract"
    UNKNOWN = "unknown_final_reason"


FINAL_REASON_LABELS: dict[FinalReason, str] = {
    FinalReason.CONTRACT_COMPLETED: "Kontrak selesai",
    FinalReason.CONTRACT_TERMINATED: "Pemutusan kontrak",
    FinalReason.CONTRACT_STOPPED: "Penghentian kontrak",
    FinalReason.TENDER_COMPLETED_NO_CONTRACT: "Tender selesai tanpa kontrak",
    FinalReason.UNKNOWN: "Alasan final belum diketahui",
}


def final_reason_label(reason: FinalReason) -> str:
    return FINAL_REASON_LABELS[reason]


class ContractStatus(str, Enum):
    COMPLETED = "Selesai"
    TERMINATED = "Pemutusan Kontrak"
    STOPPED = "Penghentian Kontrak"


class ProcurementPackage(BaseModel):
    """Normalized package fields required before persistence."""

    source: str = Field(pattern="^(sirup|spse)$")
    track: ProcurementTrack
    external_id: str = Field(min_length=1)
    rup_id: str | None = None
    tender_id: str | None = None
    package_name: str = Field(min_length=1)
    description: str | None = None
    organization: str | None = None
    satker: str | None = None
    location: str | None = None
    procurement_type: str | None = None
    procurement_method: str | None = None
    fiscal_year: int = Field(ge=2000, le=2100)
    budget_amount: float | None = Field(default=None, ge=0)
    hps_amount: float | None = Field(default=None, ge=0)
    contract_type: str | None = None
    local_content_flag: bool | None = None
    small_business_flag: bool | None = None
    current_stage_code: str | None = None
    current_stage_label: str | None = None
    contract_status: str | None = None
    source_url: str = Field(min_length=8)
    raw_snapshot_id: str | None = None


def derive_final_reason(
    *,
    current_stage_code: str | None = None,
    current_stage_label: str | None = None,
    contract_status: str | None = None,
) -> FinalReason | None:
    """Derive the Final reason without using an LLM.

    ``None`` means the package does not qualify for the Final view yet.
    Unknown values are intentionally retained as ``UNKNOWN`` only when an
    explicit final-looking label was supplied, so missing data is not
    presented as a false final state.
    """

    status = (contract_status or "").strip().casefold()
    stage = (current_stage_code or "").strip().casefold()
    stage_label = (current_stage_label or "").strip().casefold()

    if status == ContractStatus.COMPLETED.value.casefold():
        return FinalReason.CONTRACT_COMPLETED
    if status == ContractStatus.TERMINATED.value.casefold():
        return FinalReason.CONTRACT_TERMINATED
    if status == ContractStatus.STOPPED.value.casefold():
        return FinalReason.CONTRACT_STOPPED

    completed_markers = {
        "tender_completed",
        "tender_sudah_selesai",
        "tender sudah selesai",
        "selesai",
    }
    if stage in completed_markers or stage_label in completed_markers:
        return FinalReason.TENDER_COMPLETED_NO_CONTRACT

    final_markers = ("sudah selesai", "selesai", "pemutusan", "penghentian")
    if any(marker in stage_label for marker in final_markers):
        return FinalReason.UNKNOWN

    return None


def normalize_final_reason(
    *,
    current_stage_code: str | None = None,
    current_stage_label: str | None = None,
    contract_status: str | None = None,
) -> FinalReason | None:
    """Normalize portal wording before deriving the Final analytics bucket."""

    def compact(value: str | None) -> str:
        return " ".join((value or "").casefold().replace("-", " ").split())

    status = compact(contract_status)
    stage = compact(current_stage_code)
    label = compact(current_stage_label)

    if "pemutusan kontrak" in status or "kontrak diputus" in status:
        return FinalReason.CONTRACT_TERMINATED
    if "penghentian kontrak" in status or "kontrak dihentikan" in status:
        return FinalReason.CONTRACT_STOPPED
    if status in {"selesai", "kontrak selesai", "completed", "complete"}:
        return FinalReason.CONTRACT_COMPLETED
    if any(marker in label for marker in ("pemutusan", "penghentian")):
        return FinalReason.CONTRACT_TERMINATED if "pemutusan" in label else FinalReason.CONTRACT_STOPPED
    if stage in {"tender completed", "tender_sudah_selesai", "tender selesai"} or "tender sudah selesai" in label:
        return FinalReason.TENDER_COMPLETED_NO_CONTRACT
    return derive_final_reason(
        current_stage_code=current_stage_code,
        current_stage_label=current_stage_label,
        contract_status=contract_status,
    )


class FinalPackageView(BaseModel):
    """Stable API projection for a package in the Final view."""

    package_id: str
    package_name: str
    fiscal_year: int
    reason: FinalReason
    reason_label: str
    budget_amount: float | None = None
    hps_amount: float | None = None
    service_category: str | None = None
    managed_service_fit: int | None = Field(default=None, ge=0, le=100)
    source_url: str
    evidence: list[str] = Field(default_factory=list)


def normalize_status_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize portal labels while preserving original values for evidence."""

    result = dict(payload)
    result["current_stage_label"] = " ".join(str(payload.get("current_stage_label") or "").split()) or None
    result["contract_status"] = " ".join(str(payload.get("contract_status") or "").split()) or None
    return result

