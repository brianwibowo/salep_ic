import Link from "next/link";
import {
  ChevronDown,
  Compass,
  RefreshCw,
  RotateCcw,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { Lead } from "@/types/salep";

const salesStatuses: Lead["sales_status"][] = [
  "Belum Dihubungi",
  "Sedang Dihubungi",
  "Closing",
  "Batal",
];

interface SpseLeadsToolbarProps {
  isMarketing: boolean;
  search: string;
  status: string;
  salesStatus: string;
  isRefreshing: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSalesStatusChange: (value: string) => void;
  onRefresh: () => void;
  onOpenSync?: () => void;
}

export function SpseLeadsToolbar({
  isMarketing,
  search,
  status,
  salesStatus,
  isRefreshing: _isRefreshing,
  onSearchChange,
  onStatusChange,
  onSalesStatusChange,
  onRefresh: _onRefresh,
  onOpenSync,
}: SpseLeadsToolbarProps) {
  const hasActiveFilter = isMarketing ? status !== "all" : salesStatus !== "all";

  const handleResetFilter = () => {
    if (isMarketing) {
      onStatusChange("all");
    } else {
      onSalesStatusChange("all");
    }
  };

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

          <Popover>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                className={`h-9 rounded-[5px] text-xs font-medium shadow-none transition-colors ${
                  hasActiveFilter
                    ? "border-[#9D0A0E]/30 bg-[#9D0A0E]/5 text-[#9D0A0E]"
                    : "text-slate-700 dark:text-slate-200"
                }`}
              >
                <SlidersHorizontal className="size-3.5" />
                Filter
                {hasActiveFilter && (
                  <span className="size-1.5 rounded-full bg-[#9D0A0E]" />
                )}
                <ChevronDown className="size-3.5 text-muted-foreground" />
              </Button>
            </PopoverTrigger>
            <PopoverContent
              align="start"
              className="w-72 space-y-4 rounded-[5px] p-4 shadow-md"
            >
              {isMarketing ? (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Status Validasi Marketing
                  </label>
                  <select
                    className="h-9 w-full rounded-[5px] border bg-background px-3 text-xs font-normal text-foreground focus:outline-none focus:ring-1 focus:ring-[#9D0A0E]"
                    value={status}
                    onChange={(event) => onStatusChange(event.target.value)}
                  >
                    <option value="all">Semua Status</option>
                    <option value="pending">Review (Pending)</option>
                    <option value="valid">Valid</option>
                    <option value="invalid">Tidak Valid</option>
                  </select>
                </div>
              ) : (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Status Tindak Lanjut Sales
                  </label>
                  <select
                    className="h-9 w-full rounded-[5px] border bg-background px-3 text-xs font-normal text-foreground focus:outline-none focus:ring-1 focus:ring-[#9D0A0E]"
                    value={salesStatus}
                    onChange={(event) =>
                      onSalesStatusChange(event.target.value)
                    }
                  >
                    <option value="all">Semua Tindak Lanjut</option>
                    {salesStatuses.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {hasActiveFilter && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleResetFilter}
                  className="w-full h-8 text-xs font-medium text-muted-foreground hover:text-foreground"
                >
                  <RotateCcw className="size-3 mr-1.5" />
                  Reset Filter
                </Button>
              )}
            </PopoverContent>
          </Popover>
        </div>

        {/* Right Side: Sinkronisasi Manual Button */}
        <div className="flex items-center gap-2 self-end md:self-auto">
          {isMarketing && (
            <Button
              type="button"
              onClick={onOpenSync}
              className="h-9 shrink-0 gap-1.5 rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white shadow-none hover:bg-[#83080b]"
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
