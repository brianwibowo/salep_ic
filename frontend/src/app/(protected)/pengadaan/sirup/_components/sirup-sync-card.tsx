import { AlertCircle, CheckCircle2, RefreshCw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SirupSyncCardProps {
  isMarketing: boolean;
  isPending: boolean;
  isError: boolean;
  errorMessage?: string;
  selectedYears: number[];
  syncKeyword: string;
  syncLimit: number;
  fetchDetails: boolean;
  lastSyncTime: Date | null;
  onToggleYear: (year: number) => void;
  onKeywordChange: (keyword: string) => void;
  onLimitChange: (limit: number) => void;
  onFetchDetailsChange: (fetchDetails: boolean) => void;
  onSync: () => void;
}

export function SirupSyncCard({
  isMarketing,
  isPending,
  isError,
  errorMessage,
  selectedYears,
  syncKeyword,
  syncLimit,
  fetchDetails,
  lastSyncTime,
  onToggleYear,
  onKeywordChange,
  onLimitChange,
  onFetchDetailsChange,
  onSync,
}: SirupSyncCardProps) {
  const currentYear = new Date().getFullYear();
  const availableYears = [currentYear - 1, currentYear, currentYear + 1];

  return (
    <div className="space-y-4">
      <section className="rounded-lg border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1 border-b pb-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Sinkronisasi & Discovery SiRUP
              </h2>
              <p className="text-xs text-muted-foreground">
                Ambil data terbaru dari portal SiRUP berdasarkan tahun dan kata
                kunci, lalu langsung lihat hasilnya pada tabel di bawah.
              </p>
            </div>
            {lastSyncTime && (
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="size-3.5 text-emerald-600" />
                Terakhir: {lastSyncTime.toLocaleTimeString("id-ID")}
              </span>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-12 md:items-end">
            <div className="space-y-1.5 md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground">
                Tahun anggaran
              </label>
              <div className="flex flex-wrap gap-1.5">
                {availableYears.map((year) => (
                  <button
                    key={year}
                    type="button"
                    disabled={isPending}
                    onClick={() => onToggleYear(year)}
                    className={`h-9 rounded-md px-3 text-xs font-semibold transition ${
                      selectedYears.includes(year)
                        ? "bg-[#9D0A0E] text-white"
                        : "border bg-background text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5 md:col-span-4">
              <label
                htmlFor="sirup-sync-keyword"
                className="text-xs font-medium text-muted-foreground"
              >
                Kata kunci sinkronisasi (opsional)
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="sirup-sync-keyword"
                  className="h-9 pl-9 text-xs"
                  placeholder="Contoh: server, cloud, jaringan"
                  value={syncKeyword}
                  disabled={isPending}
                  onChange={(event) => onKeywordChange(event.target.value)}
                />
              </div>
            </div>

            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-medium text-muted-foreground">
                Maksimal paket
              </label>
              <select
                aria-label="Maksimal Paket"
                className="h-9 w-full rounded-md border bg-background px-2.5 text-xs"
                value={syncLimit}
                disabled={isPending}
                onChange={(event) => onLimitChange(Number(event.target.value))}
              >
                <option value={100}>100 paket</option>
                <option value={500}>500 paket</option>
                <option value={1000}>1.000 paket</option>
                <option value={2000}>2.000 paket</option>
              </select>
            </div>

            <div className="md:col-span-3">
              {isMarketing ? (
                <Button
                  className="h-9 w-full gap-2 rounded-md bg-[#9D0A0E] text-xs font-semibold text-white shadow-none hover:bg-[#83080C]"
                  disabled={isPending}
                  onClick={onSync}
                >
                  <RefreshCw
                    className={`size-4 ${isPending ? "animate-spin" : ""}`}
                  />
                  {isPending ? "Menyinkronkan..." : "Mulai Sinkronisasi"}
                </Button>
              ) : (
                <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-center text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300">
                  Sinkronisasi hanya dapat dilakukan oleh role Marketing
                </div>
              )}
            </div>
          </div>

          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={fetchDetails}
              disabled={isPending}
              onChange={(event) => onFetchDetailsChange(event.target.checked)}
              className="size-3.5 rounded border-slate-300 text-[#9D0A0E]"
            />
            Ambil detail lengkap paket (instansi, pagu anggaran, metode pemilihan)
          </label>
        </div>
      </section>

      {isError && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">
          <AlertCircle className="mt-0.5 size-5 shrink-0" />
          <div>
            <p className="font-semibold">Sinkronisasi gagal</p>
            <p className="mt-0.5 text-xs opacity-90">{errorMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
}
