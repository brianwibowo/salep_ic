"use client";

import { useState } from "react";
import {
  ExternalLink,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  X,
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
import { useSPSESearch } from "@/hooks/discovery/use-discovery";

const PRESET_SPSE_KEYWORDS = [
  "software",
  "aplikasi",
  "sistem informasi",
  "server",
  "jaringan",
  "cloud",
  "pemeliharaan",
  "keamanan",
];

interface SpseSyncDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function SpseSyncDialog({
  open,
  onOpenChange,
  onSuccess,
}: SpseSyncDialogProps) {
  const [keywords, setKeywords] = useState<string[]>([
    "software",
    "aplikasi",
    "server",
    "jaringan",
  ]);
  const [keywordDraft, setKeywordDraft] = useState("");
  const [limit, setLimit] = useState(30);

  const searchMutation = useSPSESearch();

  const addKeyword = (kw?: string) => {
    const target = (kw || keywordDraft).trim();
    if (!target) return;
    if (
      keywords.some(
        (item) => item.toLocaleLowerCase() === target.toLocaleLowerCase(),
      )
    ) {
      toast.info(`Keyword "${target}" sudah ada.`);
      return;
    }
    if (keywords.length >= 20) {
      toast.error("Maksimal 20 keyword untuk satu siklus sinkronisasi.");
      return;
    }
    setKeywords((current) => [...current, target]);
    if (!kw) setKeywordDraft("");
  };

  const removeKeyword = (target: string) => {
    setKeywords((current) => current.filter((item) => item !== target));
  };

  const handleStartSync = async () => {
    const cleaned = [
      ...new Set(keywords.map((kw) => kw.trim()).filter(Boolean)),
    ];
    if (cleaned.length === 0) {
      toast.error("Masukkan minimal satu keyword untuk sinkronisasi SPSE.");
      return;
    }

    try {
      const result = await searchMutation.mutateAsync({
        keywords: cleaned,
        limit,
      });

      toast.success(
        `Sinkronisasi SPSE selesai: ${result.matched} paket ditemukan, ${result.saved} paket disimpan.`,
      );
      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Sinkronisasi paket dari SPSE gagal dijalankan.",
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto rounded-[5px] sm:max-w-xl">
        <DialogHeader className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span>INAPROC</span>
            <span>•</span>
            <span className="text-[#9D0A0E]">Portal SPSE Nasional</span>
          </div>
          <DialogTitle className="text-lg font-bold">
            Sinkronisasi Manual Paket SPSE
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Ambil tender dan lelang pengadaan IT terbaru dari portal SPSE
            Nasional secara langsung ke database SALEP.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 pt-2">
          {/* Preset Keywords */}
          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Rekomendasi Kata Kunci Pengadaan IT
            </label>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {PRESET_SPSE_KEYWORDS.map((preset) => {
                const isSelected = keywords.some(
                  (k) => k.toLowerCase() === preset.toLowerCase(),
                );
                return (
                  <button
                    key={preset}
                    type="button"
                    disabled={searchMutation.isPending}
                    onClick={() =>
                      isSelected ? removeKeyword(preset) : addKeyword(preset)
                    }
                    className={`inline-flex items-center gap-1 rounded-[4px] px-2.5 py-1 text-xs font-medium transition-colors ${
                      isSelected
                        ? "border border-[#9D0A0E] bg-[#9D0A0E] text-white"
                        : "border border-slate-200 bg-background text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                  >
                    {preset}
                    {isSelected ? (
                      <X className="size-3" />
                    ) : (
                      <Plus className="size-3 opacity-60" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Keyword Input */}
          <div className="space-y-2">
            <label
              htmlFor="spse-sync-keyword-input"
              className="text-xs font-semibold text-slate-700 dark:text-slate-300"
            >
              Tambah Kata Kunci Kustom
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="spse-sync-keyword-input"
                  value={keywordDraft}
                  disabled={searchMutation.isPending}
                  onChange={(e) => setKeywordDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addKeyword();
                    }
                  }}
                  placeholder="Contoh: datacenter, fiber optic, erp…"
                  className="h-9 rounded-[5px] pl-9 text-xs"
                />
              </div>
              <Button
                type="button"
                variant="outline"
                disabled={!keywordDraft.trim() || searchMutation.isPending}
                onClick={() => addKeyword()}
                className="h-9 rounded-[5px] text-xs font-semibold"
              >
                Tambah
              </Button>
            </div>

            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {keywords.map((kw) => (
                  <span
                    key={kw}
                    className="inline-flex items-center gap-1.5 rounded-[4px] border border-[#9D0A0E]/30 bg-[#9D0A0E]/5 px-2 py-0.5 text-xs font-medium text-[#9D0A0E] dark:bg-[#9D0A0E]/15 dark:text-red-300"
                  >
                    {kw}
                    <button
                      type="button"
                      disabled={searchMutation.isPending}
                      onClick={() => removeKeyword(kw)}
                      className="text-[#9D0A0E]/70 hover:text-[#9D0A0E] dark:text-red-300"
                      title={`Hapus ${kw}`}
                    >
                      <X className="size-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Limit Option */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Batas Maksimal Paket
            </label>
            <select
              value={limit}
              disabled={searchMutation.isPending}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="h-9 w-full rounded-[5px] border bg-background px-3 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-[#9D0A0E]"
            >
              <option value={10}>10 paket per pencarian (Cepat)</option>
              <option value={30}>30 paket per pencarian (Standar)</option>
              <option value={50}>50 paket per pencarian</option>
              <option value={100}>100 paket per pencarian</option>
            </select>
            <p className="text-[11px] text-muted-foreground">
              Sistem akan memindai halaman lelang SPSE Nasional dan hanya
              menyimpan paket yang sesuai kata kunci.
            </p>
          </div>

          <div className="rounded-[5px] border border-blue-200 bg-blue-50/60 p-3 text-xs text-blue-900 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300">
            <p className="font-semibold flex items-center gap-1.5">
              <Layers className="size-3.5 text-blue-600 dark:text-blue-400" />
              Peran Sinkronisasi vs Discovery SPSE
            </p>
            <p className="mt-1 text-[11px] leading-relaxed text-blue-800 dark:text-blue-300">
              Tindakan ini menyinkronkan data langsung dari portal publik{" "}
              <strong>spse.inaproc.id</strong> ke daftar review Leads SPSE.
              Paket yang baru ditemukan akan berstatus{" "}
              <strong>Review (Pending)</strong> agar dapat divalidasi oleh Tim
              Marketing.
            </p>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0 pt-2">
          <Button
            type="button"
            variant="outline"
            className="rounded-[5px] text-xs"
            disabled={searchMutation.isPending}
            onClick={() => onOpenChange(false)}
          >
            Batal
          </Button>
          <Button
            type="button"
            disabled={searchMutation.isPending || keywords.length === 0}
            onClick={handleStartSync}
            className="rounded-[5px] bg-[#9D0A0E] text-xs font-semibold text-white hover:bg-[#83080b]"
          >
            {searchMutation.isPending ? (
              <>
                <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                Menyinkronkan dari SPSE…
              </>
            ) : (
              <>
                <RefreshCw className="mr-1.5 size-3.5" />
                Mulai Sinkronisasi
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
