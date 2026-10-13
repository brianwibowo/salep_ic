"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ExternalLink,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  ArrowRight,
  TrendingUp,
  FileSpreadsheet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSession } from "@/hooks/auth/use-auth";
import { useInaprocTracks, useSirupSync } from "@/hooks/use-sirup";
import type { InaprocSyncStats } from "@/types/salep";

const numberFormatter = new Intl.NumberFormat("id-ID");

export default function SirupPage() {
  const currentYear = new Date().getFullYear();
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";

  const [selectedYears, setSelectedYears] = useState<number[]>([currentYear]);
  const [keyword, setKeyword] = useState("");
  const [limit, setLimit] = useState<number>(500);
  const [fetchDetails, setFetchDetails] = useState<boolean>(true);
  const [lastSyncStats, setLastSyncStats] = useState<InaprocSyncStats[] | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  const tracksQuery = useInaprocTracks(isMarketing);
  const syncMutation = useSirupSync();

  const sirupPortalUrl =
    tracksQuery.data?.sirup || "https://sirup.inaproc.id/sirup/caripaketctr/index";

  const toggleYear = (year: number) => {
    setSelectedYears((prev) => {
      if (prev.includes(year)) {
        if (prev.length === 1) return prev; // Minimal 1 tahun terpilih
        return prev.filter((y) => y !== year);
      }
      return [...prev, year].sort((a, b) => b - a);
    });
  };

  const handleSync = () => {
    syncMutation.mutate(
      {
        fiscal_years: selectedYears,
        keyword: keyword.trim(),
        limit,
        fetch_details: fetchDetails,
        tracks: ["sirup"],
      },
      {
        onSuccess: (data) => {
          setLastSyncStats(data.results);
          setLastSyncTime(new Date());
        },
      },
    );
  };

  const aggregateStats = lastSyncStats?.reduce(
    (acc, curr) => ({
      seen: acc.seen + (curr.seen || 0),
      inserted: acc.inserted + (curr.inserted || 0),
      updated: acc.updated + (curr.updated || 0),
      rejected: acc.rejected + (curr.rejected || 0),
      unchanged: acc.unchanged + (curr.unchanged || 0),
    }),
    { seen: 0, inserted: 0, updated: 0, rejected: 0, unchanged: 0 },
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span>INAPROC</span>
            <span>•</span>
            <span className="text-[#9D0A0E]">Sistem Informasi Rencana Umum Pengadaan</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            SiRUP — Rencana Umum Pengadaan
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Sinkronisasi dan pantau rencana pengadaan pemerintah yang telah dianggarkan sebelum masuk tahap lelang SPSE.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            asChild
            variant="outline"
            className="h-9 gap-2 rounded-md shadow-none hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <Link href={sirupPortalUrl} target="_blank" rel="noopener noreferrer">
              <span>Buka Portal SiRUP</span>
              <ExternalLink className="size-3.5" />
            </Link>
          </Button>
        </div>
      </div>

      {/* Procurement Lifecycle Indicator */}
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="relative overflow-hidden rounded-lg border border-[#9D0A0E]/30 bg-[#9D0A0E]/5 p-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-[#9D0A0E] text-white">
              <Layers className="size-4" />
            </div>
            <div className="min-w-0">
              <span className="text-xs font-bold uppercase text-[#9D0A0E]">Tahap 1 • Aktif Saat Ini</span>
              <p className="font-semibold text-slate-900 dark:text-white">SiRUP (Perencanaan)</p>
              <p className="truncate text-xs text-muted-foreground">Pagu & paket rencana RUP</p>
            </div>
          </div>
        </div>

        <Link
          href="/pengadaan/spse"
          className="group relative overflow-hidden rounded-lg border bg-card p-4 transition hover:border-slate-300 hover:shadow-sm dark:hover:border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 group-hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200">
                <FileSpreadsheet className="size-4" />
              </div>
              <div className="min-w-0">
                <span className="text-xs font-medium text-muted-foreground">Tahap 2</span>
                <p className="font-semibold text-slate-900 dark:text-white">SPSE (Lelang Aktif)</p>
                <p className="truncate text-xs text-muted-foreground">Tender sedang berlangsung</p>
              </div>
            </div>
            <ArrowRight className="size-4 text-muted-foreground transition group-hover:translate-x-1" />
          </div>
        </Link>

        <Link
          href="/pengadaan/final"
          className="group relative overflow-hidden rounded-lg border bg-card p-4 transition hover:border-slate-300 hover:shadow-sm dark:hover:border-slate-700"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-700 group-hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200">
                <TrendingUp className="size-4" />
              </div>
              <div className="min-w-0">
                <span className="text-xs font-medium text-muted-foreground">Tahap 3</span>
                <p className="font-semibold text-slate-900 dark:text-white">Final (Hasil & Peluang)</p>
                <p className="truncate text-xs text-muted-foreground">Analisis paket selesai/gagal</p>
              </div>
            </div>
            <ArrowRight className="size-4 text-muted-foreground transition group-hover:translate-x-1" />
          </div>
        </Link>
      </div>

      {/* Sync Control Card */}
      <section className="rounded-lg border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Sinkronisasi RUP dari INAPROC
              </h2>
              <p className="text-xs text-muted-foreground">
                Tarik data paket rencana umum pengadaan berdasarkan tahun anggaran dan kata kunci.
              </p>
            </div>
            {lastSyncTime && (
              <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                <CheckCircle2 className="size-3.5 text-emerald-600" />
                Terakhir disinkron: {lastSyncTime.toLocaleTimeString("id-ID")}
              </span>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-12 md:items-end">
            {/* Tahun Anggaran */}
            <div className="space-y-1.5 md:col-span-3">
              <label className="text-xs font-medium text-muted-foreground">Tahun Anggaran</label>
              <div className="flex flex-wrap gap-1.5">
                {[currentYear - 1, currentYear, currentYear + 1].map((year) => {
                  const isSelected = selectedYears.includes(year);
                  return (
                    <button
                      key={year}
                      type="button"
                      onClick={() => toggleYear(year)}
                      disabled={syncMutation.isPending}
                      className={`h-9 rounded-md px-3 text-xs font-semibold transition ${
                        isSelected
                          ? "bg-[#9D0A0E] text-white shadow-sm"
                          : "border bg-background text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                      }`}
                    >
                      {year}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Keyword Filter */}
            <div className="space-y-1.5 md:col-span-4">
              <label className="text-xs font-medium text-muted-foreground">Kata Kunci (Opsional)</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="h-9 pl-9 text-xs"
                  placeholder="Contoh: Server, Cloud, Jaringan, TI..."
                  value={keyword}
                  disabled={syncMutation.isPending}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
            </div>

            {/* Limit */}
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-medium text-muted-foreground">Maksimal Paket</label>
              <select
                aria-label="Maksimal Paket"
                className="h-9 w-full rounded-md border bg-background px-2.5 text-xs font-medium text-slate-800 dark:text-slate-200"
                value={limit}
                disabled={syncMutation.isPending}
                onChange={(e) => setLimit(Number(e.target.value))}
              >
                <option value={100}>100 paket</option>
                <option value={500}>500 paket</option>
                <option value={1000}>1.000 paket</option>
                <option value={2000}>2.000 paket</option>
              </select>
            </div>

            {/* Action Button */}
            <div className="md:col-span-3">
              {isMarketing ? (
                <Button
                  type="button"
                  className="h-9 w-full gap-2 rounded-md bg-[#9D0A0E] text-white hover:bg-[#83080b]"
                  disabled={syncMutation.isPending}
                  onClick={handleSync}
                >
                  <RefreshCw className={`size-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                  {syncMutation.isPending ? "Menyinkronkan..." : "Mulai Sinkronisasi"}
                </Button>
              ) : (
                <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-center text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300">
                  Sinkronisasi hanya dapat dijalankan oleh role Marketing.
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1 text-xs text-muted-foreground">
            <input
              type="checkbox"
              id="fetch_details"
              checked={fetchDetails}
              disabled={syncMutation.isPending}
              onChange={(e) => setFetchDetails(e.target.checked)}
              className="size-3.5 rounded border-slate-300 text-[#9D0A0E] focus:ring-[#9D0A0E]"
            />
            <label htmlFor="fetch_details" className="cursor-pointer select-none">
              Ambil detail lengkap paket (instansi, pagu anggaran, metode pemilihan)
            </label>
          </div>
        </div>
      </section>

      {/* Error alert */}
      {syncMutation.isError && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-destructive">
          <AlertCircle className="mt-0.5 size-5 shrink-0" />
          <div className="text-sm">
            <p className="font-semibold">Sinkronisasi Gagal</p>
            <p className="mt-0.5 text-xs opacity-90">{syncMutation.error.message}</p>
          </div>
        </div>
      )}

      {/* Sync Results Overview */}
      {aggregateStats && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Hasil Sinkronisasi Terakhir
            </h2>
            <span className="text-xs text-muted-foreground">
              {lastSyncStats?.length ?? 0} siklus eksekusi
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard
              title="Total Diproses"
              value={numberFormatter.format(aggregateStats.seen)}
              description="Paket RUP ditemukan"
              badgeColor="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            />
            <StatCard
              title="Paket Baru"
              value={numberFormatter.format(aggregateStats.inserted)}
              description="Berhasil disimpan ke DB"
              badgeColor="bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
            />
            <StatCard
              title="Diperbarui"
              value={numberFormatter.format(aggregateStats.updated)}
              description="Perubahan data pagu/jadwal"
              badgeColor="bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
            />
            <StatCard
              title="Tidak Berubah"
              value={numberFormatter.format(aggregateStats.unchanged)}
              description="Data sudah mutakhir"
              badgeColor="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            />
            <StatCard
              title="Ditolak / Error"
              value={numberFormatter.format(aggregateStats.rejected)}
              description="Format tidak sesuai"
              badgeColor="bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
            />
          </div>

          {/* Breakdown per run */}
          <div className="overflow-hidden rounded-lg border bg-card">
            <div className="border-b px-4 py-3">
              <h3 className="text-sm font-semibold">Rincian Run ID Sinkronisasi</h3>
            </div>
            <div className="divide-y">
              {lastSyncStats?.map((stat, idx) => (
                <div
                  key={stat.run_id || idx}
                  className="flex flex-col gap-2 p-4 text-xs sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="space-y-0.5">
                    <p className="font-mono font-medium text-slate-900 dark:text-white">
                      {stat.run_id}
                    </p>
                    <p className="text-muted-foreground">
                      Track: <span className="font-semibold uppercase">{stat.track}</span> • Sumber:{" "}
                      <span className="capitalize">{stat.source}</span>
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 font-medium">
                    <span className="text-emerald-600 dark:text-emerald-400">
                      +{stat.inserted} baru
                    </span>
                    <span className="text-blue-600 dark:text-blue-400">
                      ~{stat.updated} update
                    </span>
                    <span className="text-slate-500">
                      ={stat.unchanged} sama
                    </span>
                    {stat.rejected > 0 && (
                      <span className="text-destructive">
                        !{stat.rejected} ditolak
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Info Guide Card when no sync has been run yet */}
      {!aggregateStats && (
        <section className="rounded-lg border border-dashed bg-slate-50/50 p-8 text-center dark:bg-slate-900/30">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-[#9D0A0E]/10 text-[#9D0A0E]">
            <Database className="size-6" />
          </div>
          <h3 className="mt-3 text-base font-semibold text-slate-900 dark:text-white">
            Belum Ada Sinkronisasi di Sesi Ini
          </h3>
          <p className="mx-auto mt-1 max-w-md text-xs text-muted-foreground">
            Tekan tombol <strong>Mulai Sinkronisasi</strong> di atas untuk menarik data Rencana Umum Pengadaan dari server INAPROC. Data yang tersinkronisasi akan otomatis masuk ke pipeline evaluasi leads.
          </p>
        </section>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  description,
  badgeColor,
}: {
  title: string;
  value: string;
  description: string;
  badgeColor: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{title}</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${badgeColor}`}>
          {value}
        </span>
      </div>
      <p className="mt-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
        {value}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
