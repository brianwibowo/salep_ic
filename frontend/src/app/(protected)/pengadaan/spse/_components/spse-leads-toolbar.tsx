import { RefreshCw, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LeadFiltersPopover } from "@/components/leads/lead-filters-popover";
import type { LeadFilterValues } from "@/lib/lead-filters";

interface SpseLeadsToolbarProps {
  isMarketing: boolean;
  search: string;
  filterValues: LeadFilterValues;
  isRefreshing: boolean;
  onSearchChange: (value: string) => void;
  onFiltersChange: (value: LeadFilterValues) => void;
  onRefresh: () => void;
  onOpenSync?: () => void;
}

export function SpseLeadsToolbar({
  isMarketing,
  search,
  filterValues,
  isRefreshing: _isRefreshing,
  onSearchChange,
  onFiltersChange,
  onRefresh,
  onOpenSync,
}: SpseLeadsToolbarProps) {
  return (
    <div className="border-b bg-card/60 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        {/* Left Side: Search Input & Filter */}
        <div className="flex flex-1 flex-wrap items-center gap-2.5">
          <div className="relative w-full sm:w-72 md:w-80">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-9 rounded-[5px] pl-9 pr-8 text-sm shadow-none focus-visible:ring-[#9D0A0E]/20"
              placeholder="Cari paket, instansi, kebutuhan…"
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
            />
            {search && (
              <button
                type="button"
                onClick={() => onSearchChange("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                title="Hapus pencarian"
              >
                <X className="size-3.5" />
              </button>
            )}
          </div>

          <LeadFiltersPopover
            values={filterValues}
            onChange={onFiltersChange}
            isMarketing={isMarketing}
            sourcePreset="spse"
          />

          <Button
            type="button"
            variant="outline"
            className="h-9 gap-2 rounded-[5px] text-xs"
            onClick={onRefresh}
            disabled={_isRefreshing}
            title="Muat ulang data SPSE"
            aria-label="Muat ulang data SPSE"
          >
            <RefreshCw
              className={`size-3.5 ${_isRefreshing ? "animate-spin" : ""}`}
            />
          </Button>
        </div>

        {/* Right Side: Sinkronisasi Manual Button */}
        <div className="flex items-center gap-2 self-end md:self-auto">
          {isMarketing && (
            <Button
              type="button"
              onClick={onOpenSync}
              className="h-9 shrink-0 gap-1.5 rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white cursor-pointer shadow-none hover:bg-[#83080b]"
            >
              <RefreshCw className="size-3.5" />
              Sinkronisasi Manual
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
