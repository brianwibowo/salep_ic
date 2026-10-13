import Link from "next/link";
import {
  ChevronDown,
  Compass,
  RefreshCw,
  Search,
  SlidersHorizontal,
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
}

export function SpseLeadsToolbar({
  isMarketing,
  search,
  status,
  salesStatus,
  isRefreshing,
  onSearchChange,
  onStatusChange,
  onSalesStatusChange,
  onRefresh,
}: SpseLeadsToolbarProps) {
  return (
    <div className="border-b p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        {/* Sisi Kiri: Search Input & Filter */}
        <div className="flex flex-1 flex-wrap items-center gap-2">
          <label className="relative w-full sm:w-72 md:w-80">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-9 pl-9 rounded-[5px]"
              placeholder="Cari paket, instansi, kebutuhan…"
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </label>

          <Popover>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                className="h-9 rounded-[5px] shadow-none"
              >
                <SlidersHorizontal className="size-4" />
                Filter
                <ChevronDown className="size-4 text-muted-foreground" />
              </Button>
            </PopoverTrigger>
            <PopoverContent
              align="start"
              className="w-72 space-y-4 rounded-[5px]"
            >
              {isMarketing ? (
                <label className="block space-y-1.5 text-sm font-medium">
                  Status validasi
                  <select
                    className="h-9 w-full rounded-[5px] border bg-background px-3 font-normal"
                    value={status}
                    onChange={(event) => onStatusChange(event.target.value)}
                  >
                    <option value="all">Semua status marketing</option>
                    <option value="pending">Menunggu review</option>
                    <option value="valid">Valid</option>
                    <option value="invalid">Tidak valid</option>
                  </select>
                </label>
              ) : (
                <label className="block space-y-1.5 text-sm font-medium">
                  Status tindak lanjut
                  <select
                    className="h-9 w-full rounded-[5px] border bg-background px-3 font-normal"
                    value={salesStatus}
                    onChange={(event) =>
                      onSalesStatusChange(event.target.value)
                    }
                  >
                    <option value="all">Semua tindak lanjut</option>
                    {salesStatuses.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </PopoverContent>
          </Popover>
        </div>

        {/* Sisi Kanan: Button Discovery & Refresh (Icon Only) */}
        <div className="flex items-center gap-2 self-end md:self-auto">
          {isMarketing && (
            <Button
              asChild
              variant="outline"
              className="h-9 shrink-0 rounded-[5px] border-[#9D0A0E] text-[#9D0A0E] shadow-none hover:bg-[#9D0A0E]/5 hover:text-[#9D0A0E]"
            >
              <Link href="/discovery/spse">
                <Compass className="size-4" />
                Discovery
              </Link>
            </Button>
          )}

          <Button
            type="button"
            variant="outline"
            size="icon"
            className="rounded-[5px] shadow-none"
            disabled={isRefreshing}
            onClick={onRefresh}
            title={isRefreshing ? "Memuat ulang…" : "Refresh data"}
            aria-label="Refresh data"
          >
            <RefreshCw
              className={isRefreshing ? "size-4 animate-spin" : "size-4"}
            />
          </Button>
        </div>
      </div>
    </div>
  );
}
