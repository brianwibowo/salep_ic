"use client";

import { FormEvent, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  Clock,
  Layers,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Square,
  X,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useSession } from "@/hooks/auth/use-auth";
import {
  useSaveDiscoveryConfig,
  useSchedulerAction,
  useSchedulerStatus,
} from "@/hooks/discovery/use-discovery";

const PRESET_KEYWORDS = [
  "bikin website",
  "jasa web development",
  "managed service IT",
  "aplikasi mobile",
  "software custom",
  "cloud VPS migrasi",
  "cybersecurity audit",
  "sistem POS kasir",
];

export default function SchedulerPage() {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const scheduler = useSchedulerStatus(isMarketing);
  const saveConfig = useSaveDiscoveryConfig();
  const start = useSchedulerAction("start");
  const stop = useSchedulerAction("stop");
  const trigger = useSchedulerAction("trigger");

  const [keywordListDraft, setKeywordListDraft] = useState<string[] | null>(null);
  const [newKeyword, setNewKeyword] = useState("");
  const [sourceDraft, setSourceDraft] = useState<Array<"threads" | "linkedin"> | null>(null);
  const [limitDraft, setLimitDraft] = useState<number | null>(null);

  const keywords = keywordListDraft ?? scheduler.data?.keywords ?? [];
  const sources: Array<"threads" | "linkedin"> =
    sourceDraft ??
    scheduler.data?.sources.filter(
      (item): item is "threads" | "linkedin" => item === "threads" || item === "linkedin",
    ) ?? ["threads"];
  const limit = limitDraft ?? scheduler.data?.limit_per_run ?? 5;

  if (!isMarketing) {
    return (
      <div className="rounded-[5px] border p-6 text-sm text-muted-foreground">
        Halaman Scheduler hanya dapat diakses oleh akun dengan role Marketing.
      </div>
    );
  }

  const toggleSource = (source: "threads" | "linkedin") => {
    const current = sources;
    if (current.includes(source)) {
      if (current.length === 1) {
        toast.warning("Pilih minimal satu platform sumber.");
        return;
      }
      setSourceDraft(current.filter((s) => s !== source));
    } else {
      setSourceDraft([...current, source]);
    }
  };

  const handleAddKeyword = () => {
    const trimmed = newKeyword.trim();
    if (!trimmed) return;
    if (keywords.includes(trimmed)) {
      toast.info("Keyword sudah ada di daftar.");
      return;
    }
    if (keywords.length >= 40) {
      toast.warning("Maksimal 40 keyword untuk scheduler.");
      return;
    }
    setKeywordListDraft([...keywords, trimmed]);
    setNewKeyword("");
  };

  const handleRemoveKeyword = (kwToRemove: string) => {
    setKeywordListDraft(keywords.filter((kw) => kw !== kwToRemove));
  };

  const handleSaveConfig = async (event: FormEvent) => {
    event.preventDefault();
    if (keywords.length === 0) {
      toast.error("Tambahkan minimal satu keyword untuk scheduler.");
      return;
    }
    try {
      const result = await saveConfig.mutateAsync({
        keywords,
        sources,
        limit_per_run: limit,
      });
      toast.success(
        `Pengaturan tersimpan. Scheduler ${result.is_running ? "aktif & berjalan" : "siap"}.`,
      );
      setKeywordListDraft(null);
      setSourceDraft(null);
      setLimitDraft(null);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Gagal menyimpan pengaturan scheduler",
      );
    }
  };

  const handleAction = async (action: "start" | "stop" | "trigger") => {
    const mutation = action === "start" ? start : action === "stop" ? stop : trigger;
    try {
      await mutation.mutateAsync();
      if (action === "trigger") {
        toast.success("Siklus pencarian latar belakang berhasil dipicu (dispatched).");
      } else {
        toast.success(`Scheduler berhasil ${action === "start" ? "dijalankan" : "dihentikan"}.`);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Aksi scheduler gagal dieksekusi",
      );
    }
  };

  const isActionPending = start.isPending || stop.isPending || trigger.isPending;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header Halaman */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#9D0A0E]">
          <CalendarClock className="size-4" />
          <span>Automated Background Engine</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight">Pengaturan Scheduler</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Konfigurasi otomatisasi pencarian prospek mandiri (autonomous background discovery).
          Pipeline berjalan periodik di backend, menganalisis konten publik, dan menyimpan prospek baru secara otomatis.
        </p>
      </div>

      {/* Kartu Status & Kontrol Siklus */}
      <section className="rounded-[5px] border bg-card p-5 shadow-none">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold">Status Scheduler Otomatis</h2>
              {scheduler.data?.is_running ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                  <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Aktif &amp; Berjalan
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
                  <span className="size-1.5 rounded-full bg-muted-foreground/60" />
                  Tidak Berjalan
                </span>
              )}
            </div>

            <p className="mt-1.5 text-xs text-muted-foreground">
              {scheduler.data?.last_run_at
                ? `Terakhir berjalan: ${new Date(scheduler.data.last_run_at).toLocaleString("id-ID")}`
                : "Belum ada riwayat siklus yang selesai."}
              {scheduler.data?.next_run_at && (
                <> · Jadwal berikutnya: {new Date(scheduler.data.next_run_at).toLocaleString("id-ID")}</>
              )}
            </p>

            {scheduler.data?.last_error && (
              <p className="mt-2 text-xs font-medium text-destructive">
                Error terakhir: {scheduler.data.last_error}
              </p>
            )}
          </div>

          {/* Tombol Aksi Kontrol */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={isActionPending || scheduler.data?.is_running}
              onClick={() => handleAction("start")}
              className="h-9 gap-1.5 rounded-[5px] text-xs font-semibold shadow-none"
            >
              <Play className="size-3.5 fill-current" />
              Mulai Scheduler
            </Button>

            <Button
              type="button"
              variant="outline"
              disabled={isActionPending || !scheduler.data?.is_running}
              onClick={() => handleAction("stop")}
              className="h-9 gap-1.5 rounded-[5px] text-xs font-semibold shadow-none text-destructive hover:text-destructive"
            >
              <Square className="size-3.5 fill-current" />
              Berhenti
            </Button>

            <Button
              type="button"
              disabled={isActionPending}
              onClick={() => handleAction("trigger")}
              className="h-9 gap-1.5 rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white shadow-none hover:bg-[#85080c]"
            >
              <Zap className="size-3.5" />
              Jalankan Sekali Sekarang
            </Button>
          </div>
        </div>

        {/* Metrik Statistik Scheduler */}
        <div className="mt-5 grid grid-cols-1 gap-3 border-t pt-4 sm:grid-cols-3">
          <div className="rounded-[5px] bg-muted/40 p-3">
            <p className="text-xs text-muted-foreground">Total Siklus Selesai</p>
            <p className="mt-1 text-xl font-bold">
              {scheduler.data?.total_cycles_executed ?? 0}
            </p>
          </div>
          <div className="rounded-[5px] bg-muted/40 p-3">
            <p className="text-xs text-muted-foreground">Prospek Ditemukan</p>
            <p className="mt-1 text-xl font-bold">
              {scheduler.data?.total_leads_found ?? 0}
            </p>
          </div>
          <div className="rounded-[5px] bg-muted/40 p-3">
            <p className="text-xs text-muted-foreground">Prospek Memenuhi Kriteria (Qualified)</p>
            <p className="mt-1 text-xl font-bold text-emerald-700 dark:text-emerald-400">
              {scheduler.data?.total_leads_qualified ?? 0}
            </p>
          </div>
        </div>
      </section>

      {/* Formulir Konfigurasi Parameter Scheduler */}
      <section className="rounded-[5px] border bg-card p-5 shadow-none">
        <div>
          <h2 className="text-base font-semibold">Konfigurasi Parameter Scheduler</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Kata kunci dan platform yang dikonfigurasi di sini akan dirotasi secara otomatis oleh background worker setiap siklus.
          </p>
        </div>

        <form className="mt-5 space-y-5" onSubmit={handleSaveConfig}>
          {/* Platform Selector */}
          <div>
            <label className="text-xs font-semibold text-muted-foreground">
              Platform Target Otomatisasi
            </label>
            <div className="mt-2 flex flex-wrap gap-2.5">
              <button
                type="button"
                onClick={() => toggleSource("threads")}
                className={`flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold transition ${
                  sources.includes("threads")
                    ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                Meta Threads
                {sources.includes("threads") && <CheckCircle2 className="size-3.5" />}
              </button>
              <button
                type="button"
                onClick={() => toggleSource("linkedin")}
                className={`flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold transition ${
                  sources.includes("linkedin")
                    ? "border-blue-700 bg-blue-700 text-white"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                LinkedIn Posts
                {sources.includes("linkedin") && <CheckCircle2 className="size-3.5" />}
              </button>
            </div>
          </div>

          {/* Keywords Pool */}
          <div>
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-muted-foreground">
                Kumpulan Kata Kunci Rotasi ({keywords.length}/40)
              </label>
            </div>

            <div className="mt-2 flex gap-2">
              <Input
                placeholder="Ketik kata kunci untuk ditambahkan ke pool scheduler..."
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddKeyword();
                  }
                }}
                disabled={saveConfig.isPending}
                className="h-9 rounded-[5px] text-xs"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddKeyword}
                disabled={!newKeyword.trim() || saveConfig.isPending}
                className="h-9 shrink-0 gap-1 rounded-[5px] text-xs"
              >
                <Plus className="size-3.5" />
                Tambah
              </Button>
            </div>

            {/* Keyword Chips */}
            <div className="mt-3 flex flex-wrap gap-1.5">
              {keywords.map((kw) => (
                <Badge
                  key={kw}
                  variant="secondary"
                  className="gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
                >
                  <span>{kw}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveKeyword(kw)}
                    disabled={saveConfig.isPending}
                    className="rounded-full p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}
              {keywords.length === 0 && (
                <p className="text-xs text-muted-foreground italic">
                  Belum ada keyword. Masukkan minimal 1 keyword agar scheduler dapat beroperasi.
                </p>
              )}
            </div>

            {/* Rekomendasi Cepat */}
            <div className="mt-3">
              <p className="text-[11px] font-medium text-muted-foreground">
                Rekomendasi Cepat:
              </p>
              <div className="mt-1 flex flex-wrap gap-1">
                {PRESET_KEYWORDS.filter((k) => !keywords.includes(k)).map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => {
                      if (keywords.length < 40) {
                        setKeywordListDraft([...keywords, preset]);
                      }
                    }}
                    disabled={saveConfig.isPending || keywords.length >= 40}
                    className="rounded border border-dashed border-muted-foreground/30 px-2 py-0.5 text-[11px] text-muted-foreground transition hover:border-[#9D0A0E] hover:text-[#9D0A0E]"
                  >
                    + {preset}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Limit Per Run */}
          <div>
            <label className="text-xs font-semibold text-muted-foreground">
              Batas Hasil Per Sumber Per Siklus (1 - 50)
            </label>
            <Input
              type="number"
              min={1}
              max={50}
              value={limit}
              onChange={(e) => setLimitDraft(Number(e.target.value))}
              disabled={saveConfig.isPending}
              className="mt-1.5 h-9 w-32 rounded-[5px] text-xs"
            />
            <p className="mt-1 text-[11px] text-muted-foreground">
              Rekomendasi: 5–10 post per sumber agar penggunaan kuota scraper tetap hemat dan terdistribusi merata.
            </p>
          </div>

          {/* Tombol Simpan */}
          <div className="border-t pt-4">
            <Button
              type="submit"
              disabled={saveConfig.isPending || keywords.length === 0}
              className="gap-1.5 rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white hover:bg-[#85080c]"
            >
              {saveConfig.isPending ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  Menyimpan Pengaturan...
                </>
              ) : (
                "Simpan Pengaturan Scheduler"
              )}
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}
