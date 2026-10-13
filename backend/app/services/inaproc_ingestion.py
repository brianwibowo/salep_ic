"""Scheduled/manual ingestion orchestration for Si-RUP and SPSE."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import settings
from app.core.resilience import CircuitBreaker, call_with_resilience
from app.domain.procurement import ProcurementTrack
from app.sources.inaproc.adapters import InaprocAdapter

try:  # Keep parser-only local tooling usable before optional DB deps install.
    from app.db.procurement_repository import IngestionStats, ProcurementRepository
except ModuleNotFoundError:  # pragma: no cover - production installs requirements.txt
    @dataclass
    class IngestionStats:  # type: ignore[no-redef]
        seen: int = 0
        inserted: int = 0
        updated: int = 0
        rejected: int = 0
        unchanged: int = 0

    class ProcurementRepository:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("Dependensi PostgreSQL belum terpasang; install backend/requirements.txt")


SPSE_PUBLIC_TRACKS: tuple[ProcurementTrack, ...] = (
    ProcurementTrack.TENDER,
    ProcurementTrack.NON_TENDER,
    ProcurementTrack.PENCATATAN_NON_TENDER,
    ProcurementTrack.SWAKELOLA,
    ProcurementTrack.DARURAT,
)


class InaprocIngestionService:
    def __init__(self, *, adapter: InaprocAdapter | None = None, repository: ProcurementRepository | None = None) -> None:
        self.adapter = adapter or InaprocAdapter()
        if repository is not None:
            self.repository = repository
        else:
            self.repository = ProcurementRepository(settings.database_url, create_schema=settings.database_auto_create)
        self._circuit = CircuitBreaker(name="source:inaproc")

    async def sync_sirup(self, *, fiscal_year: int, keyword: str = "", limit: int = 500, fetch_details: bool = True) -> dict[str, Any]:
        params = {"fiscal_year": fiscal_year, "keyword": keyword, "limit": limit, "fetch_details": fetch_details}
        run_id = self.repository.start_run(source="sirup", track=ProcurementTrack.SIRUP.value, parameters=params)
        packages = []
        stats = IngestionStats()
        try:
            async for package in self.adapter.iter_sirup(fiscal_year=fiscal_year, keyword=keyword, limit=limit, fetch_details=fetch_details):
                packages.append(package)
            stats = self.repository.save_packages(packages, run_id=run_id)
            self.repository.finish_run(run_id, stats=stats)
            return {"run_id": run_id, "source": "sirup", "track": ProcurementTrack.SIRUP.value, **asdict(stats)}
        except Exception as exc:
            self.repository.finish_run(run_id, stats=stats, status="failed", error=exc)
            raise

    async def sync_spse_track(self, *, track: ProcurementTrack, fiscal_year: int, keyword: str = "", limit: int = 500, fetch_details: bool = True) -> dict[str, Any]:
        if track not in SPSE_PUBLIC_TRACKS:
            raise ValueError(f"Track bukan track SPSE publik: {track}")
        params = {"fiscal_year": fiscal_year, "keyword": keyword, "limit": limit, "fetch_details": fetch_details}
        run_id = self.repository.start_run(source="spse", track=track.value, parameters=params)
        packages = []
        stats = IngestionStats()
        try:
            async for package in self.adapter.iter_spse(track=track, fiscal_year=fiscal_year, keyword=keyword, limit=limit, fetch_details=fetch_details):
                packages.append(package)
            stats = self.repository.save_packages(packages, run_id=run_id)
            self.repository.finish_run(run_id, stats=stats)
            return {"run_id": run_id, "source": "spse", "track": track.value, **asdict(stats)}
        except Exception as exc:
            self.repository.finish_run(run_id, stats=stats, status="failed", error=exc)
            raise

    async def sync_all(self, *, fiscal_years: list[int], keyword: str = "", limit: int = 500, fetch_details: bool = True) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for fiscal_year in fiscal_years:
            results.append(await call_with_resilience(
                lambda year=fiscal_year: self.sync_sirup(fiscal_year=year, keyword=keyword, limit=limit, fetch_details=fetch_details),
                circuit=self._circuit,
                operation_name="inaproc_sync:sirup",
            ))
            for track in SPSE_PUBLIC_TRACKS:
                results.append(await call_with_resilience(
                    lambda track_value=track, year=fiscal_year: self.sync_spse_track(track=track_value, fiscal_year=year, keyword=keyword, limit=limit, fetch_details=fetch_details),
                    circuit=self._circuit,
                    operation_name=f"inaproc_sync:{track.value}",
                ))
        return results
