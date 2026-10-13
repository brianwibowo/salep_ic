"use client";

import { useState } from "react";
import {
  Compass,
  Link as LinkIcon,
  Loader2,
  Plus,
  Search,
  Sparkles,
  X,
  CheckCircle2,
  Globe,
  Share2,
  Calendar,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import type { UseMutationResult } from "@tanstack/react-query";
import type { SearchResult, Lead } from "@/types/salep";
import type { ManualSearchInput } from "@/validations/salep-validation";

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

function localDate(date: Date) {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10);
}

interface SocialMediaDiscoveryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  searchMutation: UseMutationResult<SearchResult, Error, ManualSearchInput>;
  analyzeUrlMutation: UseMutationResult<Lead, Error, { url: string; save_to_sheet?: boolean }>;
}

export function SocialMediaDiscoveryDialog({
  open,
  onOpenChange,
  searchMutation,
  analyzeUrlMutation,
}: SocialMediaDiscoveryDialogProps) {
  const [activeTab, setActiveTab] = useState<"keywords" | "direct_url">("keywords");

  // Keyword search state (default 1 keyword agar eksekusi cepat dan tidak memicu timeout Nginx 60s)
  const [keywords, setKeywords] = useState<string[]>(["bikin website"]);
  const [newKeyword, setNewKeyword] = useState("");
  const [sources, setSources] = useState<Array<"threads" | "linkedin">>([
    "threads",
  ]);
  const [startDate, setStartDate] = useState(() =>
    localDate(new Date(Date.now() - 6 * 86_400_000)),
  );
  const [endDate, setEndDate] = useState(() => localDate(new Date()));
  const [limit, setLimit] = useState(5);

  // Direct URL state
  const [directUrl, setDirectUrl] = useState("");

  const handleAddKeyword = () => {
    const trimmed = newKeyword.trim();
    if (!trimmed) return;
    if (keywords.includes(trimmed)) {
      toast.info("Keyword sudah ada di daftar.");
      return;
    }
    if (keywords.length >= 10) {
      toast.warning("Maksimal 10 keyword per pencarian.");
      return;
    }
    setKeywords([...keywords, trimmed]);
    setNewKeyword("");
  };

  const handleRemoveKeyword = (kwToRemove: string) => {
    setKeywords(keywords.filter((kw) => kw !== kwToRemove));
  };

  const toggleSource = (source: "threads" | "linkedin") => {
    if (sources.includes(source)) {
      if (sources.length === 1) {
        toast.warning("Pilih minimal satu platform sumber.");
        return;
      }
      setSources(sources.filter((s) => s !== source));
    } else {
      setSources([...sources, source]);
    }
  };

  const handleRunKeywordSearch = async () => {
    if (keywords.length === 0) {
      toast.error("Tambahkan minimal 1 keyword.");
      return;
    }
    if (sources.length === 0) {
      toast.error("Pilih minimal 1 platform (Threads atau LinkedIn).");
      return;
    }

    try {
      toast.info("Discovery dimulai di latar belakang. Anda dapat menutup pop-up ini kapan saja.");
      await searchMutation.mutateAsync({
        keywords,
        start_date: startDate,
        end_date: endDate,
        sources,
        limit,
      });
      toast.success("Discovery selesai! Data prospek baru telah ditambahkan ke tabel.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Pencarian gagal";
      if (msg.includes("504") || msg.includes("timeout") || msg.includes("Time-out")) {
        toast.error(
          "Server Timeout (504): Proses pencarian melebihi batas 60 detik Nginx staging. Hal ini terjadi karena kuota Apify scraper sedang melebihi batas (Monthly usage limit). Coba gunakan 1 kata kunci atau gunakan tab 'Ambil dari URL Postingan Langsung'.",
          { duration: 8000 }
        );
      } else if (msg.includes("circuit_open") || msg.includes("batas pemakaian")) {
        toast.error(
          "Kuota Scraper Apify Habis: Akun Apify mencapai Monthly usage hard limit. Silakan gunakan tab 'Ambil dari URL Postingan Langsung' untuk ekstraksi tanpa Apify.",
          { duration: 8000 }
        );
      } else {
        toast.error(`Discovery error: ${msg}`);
      }
    }
  };

  const handleRunAnalyzeUrl = async () => {
    const trimmed = directUrl.trim();
    if (!trimmed) {
      toast.error("Masukkan URL postingan Threads atau LinkedIn.");
      return;
    }
    if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) {
      toast.error("Format URL harus diawali https://");
      return;
    }

    try {
      toast.info("Menganalisis URL postingan...");
      const res = await analyzeUrlMutation.mutateAsync({
        url: trimmed,
        save_to_sheet: true,
      });
      toast.success(
        `Berhasil mengambil postingan dari ${res.author_name || "pengguna"} (Skor: ${res.lead_score})!`,
      );
      setDirectUrl("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal menganalisis URL";
      toast.error(`Analisis gagal: ${msg}`);
    }
  };

  const isBusy = searchMutation.isPending || analyzeUrlMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl rounded-lg">
        <DialogHeader className="border-b pb-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#9D0A0E]">
            <Compass className="size-4" />
            <span>Discovery Sosial Media (Real Pipeline)</span>
          </div>
          <DialogTitle className="text-xl font-bold">
            Pencarian & Ekstraksi Prospek
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Scraping konten publik dari Threads &amp; LinkedIn, analisis intent AI,
            scoring otomatis, dan penyimpanan langsung ke PostgreSQL.
          </DialogDescription>
        </DialogHeader>

        {/* Status Background Banner Jika Sedang Berjalan */}
        {isBusy && (
          <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-3.5 text-xs text-blue-900 dark:text-blue-200">
            <div className="flex items-start gap-2.5">
              <Loader2 className="mt-0.5 size-4 animate-spin text-blue-600 dark:text-blue-400 shrink-0" />
              <div>
                <p className="font-semibold">
                  {searchMutation.isPending
                    ? "Sedang mencari & menganalisis prospek dari sosial media..."
                    : "Sedang mengekstrak konten postingan & menjalankan evaluasi AI..."}
                </p>
                <p className="mt-1 text-muted-foreground">
                  Proses ini tetap berjalan di latar belakang jika pop-up ditutup.
                  Tabel leads akan diperbarui secara otomatis setelah selesai.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Selector */}
        <div className="flex items-center gap-2 border-b pb-2">
          <button
            type="button"
            onClick={() => setActiveTab("keywords")}
            className={`flex items-center gap-1.5 rounded-[5px] px-3 py-1.5 text-xs font-semibold transition ${
              activeTab === "keywords"
                ? "bg-[#9D0A0E] text-white shadow-sm"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <Search className="size-3.5" />
            Pencarian Keyword
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("direct_url")}
            className={`flex items-center gap-1.5 rounded-[5px] px-3 py-1.5 text-xs font-semibold transition ${
              activeTab === "direct_url"
                ? "bg-[#9D0A0E] text-white shadow-sm"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <LinkIcon className="size-3.5" />
            Ambil dari URL Postingan Langsung
          </button>
        </div>

        {/* Tab 1: Keywords Scraper */}
        {activeTab === "keywords" && (
          <div className="space-y-4 pt-1">
            {/* Platform Selection */}
            <div>
              <label className="text-xs font-semibold text-muted-foreground">
                Platform Sumber
              </label>
              <div className="mt-1.5 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => toggleSource("threads")}
                  className={`flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold transition ${
                    sources.includes("threads")
                      ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
                      : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <Share2 className="size-3.5" />
                  Meta Threads
                  {sources.includes("threads") && (
                    <CheckCircle2 className="size-3.5" />
                  )}
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
                  <Globe className="size-3.5" />
                  LinkedIn Posts
                  {sources.includes("linkedin") && (
                    <CheckCircle2 className="size-3.5" />
                  )}
                </button>
              </div>
            </div>

            {/* Keyword Management */}
            <div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-muted-foreground">
                  Kata Kunci Pencarian ({keywords.length}/10)
                </label>
              </div>

              {/* Input New Keyword */}
              <div className="mt-1.5 flex gap-2">
                <Input
                  placeholder="Ketik kata kunci (contoh: butuh website, cari vendor IT)..."
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddKeyword();
                    }
                  }}
                  disabled={isBusy}
                  className="h-9 rounded-[5px] text-xs"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleAddKeyword}
                  disabled={!newKeyword.trim() || isBusy}
                  className="h-9 shrink-0 gap-1 rounded-[5px] text-xs"
                >
                  <Plus className="size-3.5" />
                  Tambah
                </Button>
              </div>

              {/* Keyword Chips */}
              <div className="mt-2.5 flex flex-wrap gap-1.5">
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
                      disabled={isBusy}
                      className="rounded-full hover:bg-muted p-0.5 text-muted-foreground hover:text-foreground"
                    >
                      <X className="size-3" />
                    </button>
                  </Badge>
                ))}
              </div>

              {/* Preset suggestions */}
              <div className="mt-3">
                <p className="text-[11px] font-medium text-muted-foreground">
                  Rekomendasi Cepat:
                </p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {PRESET_KEYWORDS.filter((k) => !keywords.includes(k)).map(
                    (preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => {
                          if (keywords.length < 10) {
                            setKeywords([...keywords, preset]);
                          }
                        }}
                        disabled={isBusy || keywords.length >= 10}
                        className="rounded border border-dashed border-muted-foreground/30 px-2 py-0.5 text-[11px] text-muted-foreground transition hover:border-[#9D0A0E] hover:text-[#9D0A0E]"
                      >
                        + {preset}
                      </button>
                    ),
                  )}
                </div>
              </div>
            </div>

            {/* Date range & limit */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground">
                  Dari Tanggal
                </label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  disabled={isBusy}
                  className="mt-1 h-9 rounded-[5px] text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground">
                  Sampai Tanggal
                </label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  disabled={isBusy}
                  className="mt-1 h-9 rounded-[5px] text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground">
                  Limit Hasil
                </label>
                <select
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  disabled={isBusy}
                  className="mt-1 flex h-9 w-full rounded-[5px] border border-input bg-background px-3 py-1 text-xs shadow-sm"
                >
                  <option value={5}>5 post per run</option>
                  <option value={10}>10 post per run</option>
                  <option value={20}>20 post per run</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Direct URL Extraction */}
        {activeTab === "direct_url" && (
          <div className="space-y-4 pt-1">
            <div className="rounded-lg border bg-muted/40 p-3 text-xs text-muted-foreground">
              <p className="font-semibold text-foreground">
                Ekstraksi Langsung Tanpa Kuota Scraper
              </p>
              <p className="mt-1">
                Jika Anda menemukan postingan potensial di Threads atau LinkedIn,
                salin link postingan dan tempel di bawah. Sistem akan mengekstrak teks,
                penulis, metadata, dan menjalankan AI lead scoring secara langsung.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground">
                URL Postingan Threads / LinkedIn
              </label>
              <Input
                placeholder="https://www.threads.net/@nama/post/xyz atau https://www.linkedin.com/..."
                value={directUrl}
                onChange={(e) => setDirectUrl(e.target.value)}
                disabled={isBusy}
                className="mt-1.5 h-9 rounded-[5px] text-xs"
              />
            </div>
          </div>
        )}

        <DialogFooter className="flex-col sm:flex-row gap-2 border-t pt-4">
          {/* Tombol Tutup / Jalankan di Latar Belakang */}
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="rounded-[5px] text-xs"
          >
            {isBusy ? "Tutup (Tetap Berjalan di Background)" : "Batal"}
          </Button>

          {/* Tombol Eksekusi */}
          {activeTab === "keywords" ? (
            <Button
              type="button"
              onClick={handleRunKeywordSearch}
              disabled={isBusy || keywords.length === 0}
              className="gap-1.5 rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white hover:bg-[#85080c]"
            >
              {searchMutation.isPending ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  Sedang Mencari...
                </>
              ) : (
                <>
                  <Sparkles className="size-3.5" />
                  Mulai Pencarian
                </>
              )}
            </Button>
          ) : (
            <Button
              type="button"
              onClick={handleRunAnalyzeUrl}
              disabled={isBusy || !directUrl.trim()}
              className="gap-1.5 rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white hover:bg-[#85080c]"
            >
              {analyzeUrlMutation.isPending ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  Mengekstrak &amp; Menganalisis...
                </>
              ) : (
                <>
                  <LinkIcon className="size-3.5" />
                  Ambil &amp; Analisis Post
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
