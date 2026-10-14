import { Database, Filter, RefreshCw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { SirupListResponse, SirupSort } from "@/types/salep";
import { formatCurrency, formatNumber } from "@/utils/formatting/string";

interface SirupToolbarProps {
  summary?: SirupListResponse["summary"];
  facets?: SirupListResponse["facets"];
  search: string;
  selectedYear?: number;
  procurementType: string;
  procurementMethod: string;
  dateFrom: string;
  dateTo: string;
  sort: SirupSort;
  isRefreshing?: boolean;
  onSearchChange: (value: string) => void;
  onYearChange: (year?: number) => void;
  onTypeChange: (type: string) => void;
  onMethodChange: (method: string) => void;
  onDateFromChange: (date: string) => void;
  onDateToChange: (date: string) => void;
  onSortChange: (sort: SirupSort) => void;
  onReset: () => void;
  onRefresh: () => void;
}

export function SirupToolbar({
  summary,
  facets,
  search,
  selectedYear,
  procurementType,
  procurementMethod,
  dateFrom,
  dateTo,
  sort,
  isRefreshing,
  onSearchChange,
  onYearChange,
  onTypeChange,
  onMethodChange,
  onDateFromChange,
  onDateToChange,
  onSortChange,
  onReset,
  onRefresh,
}: SirupToolbarProps) {
  const currentYear = new Date().getFullYear();

  return (
    <div className="border-b p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Database className="size-4 text-[#9D0A0E]" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Data SiRUP Tersimpan
            </h2>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {summary?.total
              ? `${formatNumber(summary.total)} paket ditemukan`
              : "Belum ada paket yang sesuai filter"}
            {summary?.total_budget_amount
              ? ` · Total pagu ${formatCurrency(summary.total_budget_amount)}`
              : ""}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="sirup-search">
            Cari paket SiRUP
          </label>
          <div className="relative min-w-[230px] flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="sirup-search"
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="Cari nama, instansi, satker..."
              className="h-9 pl-9 text-xs"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-2 text-xs"
            onClick={onReset}
          >
            <Filter className="size-3.5" />
            Reset filter
          </Button>
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-2 text-xs"
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Muat ulang data paket"
          >
            <RefreshCw className={cn("size-3.5", isRefreshing && "animate-spin")} />
          </Button>
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
        <select
          aria-label="Filter Tahun"
          className="h-9 rounded-md border bg-background px-2.5 text-xs font-medium text-slate-800 dark:text-slate-200"
          value={selectedYear ?? "all"}
          onChange={(event) =>
            onYearChange(
              event.target.value === "all"
                ? undefined
                : Number(event.target.value),
            )
          }
        >
          <option value="all">Semua tahun</option>
          {(facets?.fiscal_years ?? [currentYear]).map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>

        <select
          aria-label="Filter Jenis Pengadaan"
          className="h-9 rounded-md border bg-background px-2.5 text-xs font-medium text-slate-800 dark:text-slate-200"
          value={procurementType}
          onChange={(event) => onTypeChange(event.target.value)}
        >
          <option value="">Semua jenis</option>
          {(facets?.procurement_types ?? []).map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>

        <select
          aria-label="Filter Metode Pengadaan"
          className="h-9 rounded-md border bg-background px-2.5 text-xs font-medium text-slate-800 dark:text-slate-200"
          value={procurementMethod}
          onChange={(event) => onMethodChange(event.target.value)}
        >
          <option value="">Semua metode</option>
          {(facets?.procurement_methods ?? []).map((method) => (
            <option key={method} value={method}>
              {method}
            </option>
          ))}
        </select>

        <Input
          aria-label="Tanggal mulai sinkronisasi"
          type="date"
          value={dateFrom}
          onChange={(event) => onDateFromChange(event.target.value)}
          className="h-9 text-xs"
        />

        <Input
          aria-label="Tanggal akhir sinkronisasi"
          type="date"
          value={dateTo}
          onChange={(event) => onDateToChange(event.target.value)}
          className="h-9 text-xs"
        />

        <select
          aria-label="Urutan data"
          className="h-9 rounded-md border bg-background px-2.5 text-xs font-medium text-slate-800 dark:text-slate-200"
          value={sort}
          onChange={(event) => onSortChange(event.target.value as SirupSort)}
        >
          <option value="newest">Terbaru</option>
          <option value="oldest">Terlama</option>
          <option value="budget_desc">Pagu terbesar</option>
          <option value="budget_asc">Pagu terkecil</option>
        </select>
      </div>
    </div>
  );
}
