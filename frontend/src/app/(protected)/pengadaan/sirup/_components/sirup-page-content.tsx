"use client";

import { useCallback, useMemo, useState } from "react";
import type { PaginationState } from "@tanstack/react-table";
import { useSession } from "@/hooks/auth/use-auth";
import { useDebounce } from "@/hooks/use-debounce";
import {
  useInaprocTracks,
  useSirupPackages,
  useSirupSync,
} from "@/hooks/use-sirup";
import type {
  InaprocSyncStats,
  SirupFilters,
  SirupPackage,
  SirupSort,
} from "@/types/salep";
import { SirupHeader } from "./sirup-header";
import { SirupPackageDetailsDialog } from "./sirup-package-details-dialog";
import { SirupStatsCards } from "./sirup-stats-cards";
import { SirupSyncCard } from "./sirup-sync-card";
import { SirupTable } from "./sirup-table";
import { SirupToolbar } from "./sirup-toolbar";

export function SirupPageContent() {
  const currentYear = new Date().getFullYear();
  const { data: session } = useSession();
  const canRead = session?.role === "marketing" || session?.role === "sales";
  const isMarketing = session?.role === "marketing";

  // Filter & Search states
  const [selectedPackage, setSelectedPackage] = useState<SirupPackage | null>(
    null,
  );
  const [selectedYear, setSelectedYear] = useState<number | undefined>();
  const [search, setSearch] = useState("");
  const [procurementType, setProcurementType] = useState("");
  const [procurementMethod, setProcurementMethod] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sort, setSort] = useState<SirupSort>("newest");
  const debouncedSearch = useDebounce(search, 400);

  // TanStack Table Pagination state (0-indexed)
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 25,
  });

  // Sync states
  const [selectedYears, setSelectedYears] = useState<number[]>([currentYear]);
  const [syncKeyword, setSyncKeyword] = useState("");
  const [syncLimit, setSyncLimit] = useState(500);
  const [fetchDetails, setFetchDetails] = useState(true);
  const [lastSyncStats, setLastSyncStats] = useState<InaprocSyncStats[] | null>(
    null,
  );
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  const resetPage = useCallback(() => {
    setPagination((current) => ({ ...current, pageIndex: 0 }));
  }, []);

  const handleSearchChange = useCallback(
    (value: string) => {
      setSearch(value);
      resetPage();
    },
    [resetPage],
  );

  const handleYearChange = useCallback(
    (year?: number) => {
      setSelectedYear(year);
      resetPage();
    },
    [resetPage],
  );

  const handleTypeChange = useCallback(
    (type: string) => {
      setProcurementType(type);
      resetPage();
    },
    [resetPage],
  );

  const handleMethodChange = useCallback(
    (method: string) => {
      setProcurementMethod(method);
      resetPage();
    },
    [resetPage],
  );

  const handleDateFromChange = useCallback(
    (date: string) => {
      setDateFrom(date);
      resetPage();
    },
    [resetPage],
  );

  const handleDateToChange = useCallback(
    (date: string) => {
      setDateTo(date);
      resetPage();
    },
    [resetPage],
  );

  const handleSortChange = useCallback(
    (newSort: SirupSort) => {
      setSort(newSort);
      resetPage();
    },
    [resetPage],
  );

  const handleResetFilters = useCallback(() => {
    setSelectedYear(undefined);
    setSearch("");
    setProcurementType("");
    setProcurementMethod("");
    setDateFrom("");
    setDateTo("");
    setSort("newest");
    resetPage();
  }, [resetPage]);

  const handleToggleSyncYear = useCallback((year: number) => {
    setSelectedYears((years) =>
      years.includes(year)
        ? years.length > 1
          ? years.filter((item) => item !== year)
          : years
        : [...years, year].sort((a, b) => b - a),
    );
  }, []);

  // API Query parameters: only include active filters if present
  const filters = useMemo<
    SirupFilters & { page: number; limit: number }
  >(() => {
    const activeFilters: SirupFilters & { page: number; limit: number } = {
      page: pagination.pageIndex + 1,
      limit: pagination.pageSize,
      sort,
    };

    if (selectedYear) {
      activeFilters.fiscal_year = selectedYear;
    }
    if (debouncedSearch.trim()) {
      activeFilters.search = debouncedSearch.trim();
    }
    if (procurementType.trim()) {
      activeFilters.procurement_type = procurementType.trim();
    }
    if (procurementMethod.trim()) {
      activeFilters.procurement_method = procurementMethod.trim();
    }
    if (dateFrom.trim()) {
      activeFilters.date_from = dateFrom.trim();
    }
    if (dateTo.trim()) {
      activeFilters.date_to = dateTo.trim();
    }

    return activeFilters;
  }, [
    selectedYear,
    debouncedSearch,
    procurementType,
    procurementMethod,
    dateFrom,
    dateTo,
    sort,
    pagination.pageIndex,
    pagination.pageSize,
  ]);

  const tracksQuery = useInaprocTracks(canRead);
  const packagesQuery = useSirupPackages(filters, canRead);
  const syncMutation = useSirupSync();

  const handleRefresh = useCallback(() => {
    void packagesQuery.refetch();
  }, [packagesQuery]);

  const sirupPortalUrl =
    tracksQuery.data?.sirup ||
    "https://sirup.inaproc.id/sirup/caripaketctr/index";

  const handleSync = useCallback(() => {
    syncMutation.mutate(
      {
        fiscal_years: selectedYears,
        keyword: syncKeyword.trim(),
        limit: syncLimit,
        fetch_details: fetchDetails,
        tracks: ["sirup"],
      },
      {
        onSuccess: (response) => {
          setLastSyncStats(response.results);
          setLastSyncTime(new Date());
        },
      },
    );
  }, [fetchDetails, selectedYears, syncKeyword, syncLimit, syncMutation]);

  const aggregateStats = useMemo(() => {
    if (!lastSyncStats?.length) return null;
    return lastSyncStats.reduce(
      (acc, curr) => ({
        seen: acc.seen + (curr.seen || 0),
        inserted: acc.inserted + (curr.inserted || 0),
        updated: acc.updated + (curr.updated || 0),
        rejected: acc.rejected + (curr.rejected || 0),
        unchanged: acc.unchanged + (curr.unchanged || 0),
      }),
      { seen: 0, inserted: 0, updated: 0, rejected: 0, unchanged: 0 },
    );
  }, [lastSyncStats]);

  const packageData = packagesQuery.data?.items ?? [];
  const totalRecords = packagesQuery.data?.pagination.total ?? 0;

  return (
    <div className="space-y-6">
      <SirupHeader portalUrl={sirupPortalUrl} />

      <SirupSyncCard
        isMarketing={isMarketing}
        isPending={syncMutation.isPending}
        isError={syncMutation.isError}
        errorMessage={syncMutation.error?.message}
        selectedYears={selectedYears}
        syncKeyword={syncKeyword}
        syncLimit={syncLimit}
        fetchDetails={fetchDetails}
        lastSyncTime={lastSyncTime}
        onToggleYear={handleToggleSyncYear}
        onKeywordChange={setSyncKeyword}
        onLimitChange={setSyncLimit}
        onFetchDetailsChange={setFetchDetails}
        onSync={handleSync}
      />

      <SirupStatsCards stats={aggregateStats} />

      <section className="rounded-lg border bg-card shadow-sm">
        <SirupToolbar
          summary={packagesQuery.data?.summary}
          facets={packagesQuery.data?.facets}
          search={search}
          selectedYear={selectedYear}
          procurementType={procurementType}
          procurementMethod={procurementMethod}
          dateFrom={dateFrom}
          dateTo={dateTo}
          sort={sort}
          isRefreshing={packagesQuery.isRefetching}
          onSearchChange={handleSearchChange}
          onYearChange={handleYearChange}
          onTypeChange={handleTypeChange}
          onMethodChange={handleMethodChange}
          onDateFromChange={handleDateFromChange}
          onDateToChange={handleDateToChange}
          onSortChange={handleSortChange}
          onReset={handleResetFilters}
          onRefresh={handleRefresh}
        />

        <div className="p-5">
          <SirupTable
            data={packageData}
            total={totalRecords}
            pagination={pagination}
            isLoading={packagesQuery.isLoading}
            isError={packagesQuery.isError}
            errorMessage={packagesQuery.error?.message}
            onPaginationChange={setPagination}
            onViewPackage={setSelectedPackage}
          />
        </div>
      </section>

      <SirupPackageDetailsDialog
        packageData={selectedPackage}
        onOpenChange={(open) => {
          if (!open) setSelectedPackage(null);
        }}
      />
    </div>
  );
}
