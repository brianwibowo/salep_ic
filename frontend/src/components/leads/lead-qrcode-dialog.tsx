"use client";

import { useRef, useState } from "react";
import {
  AlertCircle,
  Building2,
  Check,
  Clock,
  Coins,
  Copy,
  Download,
  ExternalLink,
  QrCode,
  Smartphone,
  Tag,
} from "lucide-react";
import { QRCodeCanvas } from "qrcode.react";
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
import { parseSpseLeadContent } from "@/lib/spse-parser";
import type { Lead } from "@/types/salep";

interface LeadQrCodeDialogProps {
  lead: Lead | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function LeadQrCodeDialog({
  lead,
  open,
  onOpenChange,
}: LeadQrCodeDialogProps) {
  const [copied, setCopied] = useState(false);
  const qrRef = useRef<HTMLDivElement>(null);

  if (!lead) return null;

  const url = lead.source_url?.trim() || "";
  const hasUrl = Boolean(url);
  const isSpse = lead.source === "spse";
  const spseParsed = isSpse
    ? parseSpseLeadContent(lead.content, lead.author_name)
    : null;

  const handleCopyUrl = async () => {
    if (!hasUrl) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success("Tautan konten prospek berhasil disalin ke clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Gagal menyalin tautan.");
    }
  };

  const handleDownloadQr = () => {
    if (!qrRef.current) return;
    const canvas = qrRef.current.querySelector("canvas");
    if (!canvas) {
      toast.error("QR Code belum siap untuk diunduh.");
      return;
    }

    try {
      const pngUrl = canvas.toDataURL("image/png");
      const downloadLink = document.createElement("a");
      const rawName = isSpse
        ? spseParsed?.title || lead.author_name || "spse-tender"
        : lead.author_name || "lead";
      const safeAuthor = rawName
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .slice(0, 30);
      downloadLink.href = pngUrl;
      downloadLink.download = `qr-lead-${safeAuthor}-${lead.lead_id.slice(0, 8)}.png`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      toast.success("QR Code berhasil diunduh sebagai gambar PNG!");
    } catch {
      toast.error("Gagal mengunduh gambar QR Code.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full max-w-lg max-h-[92vh] flex flex-col overflow-hidden rounded-xl p-0 border border-border/80 shadow-2xl bg-card">
        {/* Header */}
        <DialogHeader className="border-b border-border/60 bg-muted/20 px-6 py-4 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-lg bg-[#9D0A0E]/10 text-[#9D0A0E] dark:bg-[#9D0A0E]/20">
              <QrCode className="size-5" />
            </div>
            <div>
              <DialogTitle className="text-base font-bold text-foreground">
                {isSpse ? "QR Code Paket Pengadaan SPSE" : "QR Code Konten Lead"}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Pindai dengan kamera smartphone untuk membuka tautan langsung via HP
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Content Body - Scrollable to prevent any truncation */}
        <div className="flex-1 overflow-y-auto min-h-0 space-y-4 px-6 py-5">
          {/* Metadata Card */}
          <div className="rounded-lg border border-border/70 bg-muted/30 p-3.5 space-y-2 text-xs">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <span className="inline-flex items-center rounded-full border border-[#9D0A0E]/30 bg-[#9D0A0E]/10 px-2.5 py-0.5 text-[11px] font-semibold text-[#9D0A0E] uppercase">
                  {isSpse ? "SPSE LKPP" : lead.source || "leads"}
                </span>
                {spseParsed?.badge && (
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      spseParsed.badge.variant === "destructive"
                        ? "border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300"
                        : "border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                    }`}
                  >
                    {spseParsed.badge.text}
                  </span>
                )}
              </div>

              {lead.matched_keyword && (
                <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                  <Tag className="size-3 shrink-0" />
                  {lead.matched_keyword}
                </span>
              )}
            </div>

            {/* Title / Package Name without truncation */}
            <div>
              <h4 className="font-bold text-foreground text-sm leading-snug break-words">
                {isSpse
                  ? spseParsed?.title || lead.author_name || "Paket Pengadaan SPSE"
                  : lead.author_name || "Prospek Tanpa Nama"}
              </h4>
            </div>

            {/* Additional SPSE Metadata (Instansi, Tahap, HPS) */}
            {isSpse && spseParsed && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t border-border/50 text-[11px] text-muted-foreground">
                {spseParsed.agency && (
                  <div className="flex items-center gap-1.5 truncate">
                    <Building2 className="size-3.5 text-slate-400 shrink-0" />
                    <span className="font-medium text-foreground truncate">
                      {spseParsed.agency}
                    </span>
                  </div>
                )}
                {spseParsed.hps && spseParsed.hps !== "Rp 0" && (
                  <div className="flex items-center gap-1.5">
                    <Coins className="size-3.5 text-[#9D0A0E] shrink-0" />
                    <span className="font-semibold text-foreground">
                      HPS: {spseParsed.hps}
                    </span>
                  </div>
                )}
                {spseParsed.stage && (
                  <div className="flex items-center gap-1.5 sm:col-span-2">
                    <Clock className="size-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">Tahap: <strong className="text-foreground">{spseParsed.stage}</strong></span>
                  </div>
                )}
              </div>
            )}

            {/* Social Media Content snippet if not SPSE */}
            {!isSpse && lead.content && (
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3 pt-1 border-t border-border/50">
                &ldquo;{lead.content}&rdquo;
              </p>
            )}
          </div>

          {/* QR Code Container */}
          {hasUrl ? (
            <div className="flex flex-col items-center">
              <div
                ref={qrRef}
                className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-slate-200/80 bg-white p-4 shadow-inner dark:border-slate-800"
              >
                {/* Visual scan frame corners */}
                <div className="absolute top-2 left-2 size-3.5 border-t-2 border-l-2 border-[#9D0A0E] rounded-tl-sm pointer-events-none" />
                <div className="absolute top-2 right-2 size-3.5 border-t-2 border-r-2 border-[#9D0A0E] rounded-tr-sm pointer-events-none" />
                <div className="absolute bottom-2 left-2 size-3.5 border-b-2 border-l-2 border-[#9D0A0E] rounded-bl-sm pointer-events-none" />
                <div className="absolute bottom-2 right-2 size-3.5 border-b-2 border-r-2 border-[#9D0A0E] rounded-br-sm pointer-events-none" />

                <QRCodeCanvas
                  value={url}
                  size={190}
                  level="Q"
                  marginSize={1}
                />
              </div>

              {/* Guidance for Mobile Users */}
              <div className="mt-2.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                <Smartphone className="size-3.5 text-[#9D0A0E]" />
                <span>Arahkan kamera HP ke QR Code untuk membuka di browser ponsel</span>
              </div>

              {/* URL Preview & Actions */}
              <div className="mt-3.5 w-full space-y-2">
                <div className="flex items-start justify-between gap-2 rounded-md border border-border/70 bg-muted/40 p-2.5 text-xs">
                  <span className="font-mono text-[11px] text-muted-foreground break-all leading-normal select-all">
                    {url}
                  </span>
                  <button
                    type="button"
                    onClick={handleCopyUrl}
                    className="shrink-0 text-slate-500 hover:text-foreground transition p-1 rounded hover:bg-muted"
                    title={copied ? "Tersalin!" : "Salin URL"}
                    aria-label="Salin URL"
                  >
                    {copied ? (
                      <Check className="size-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="size-3.5" />
                    )}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs gap-1.5"
                    onClick={handleDownloadQr}
                  >
                    <Download className="size-3.5" />
                    <span>Unduh Gambar QR</span>
                  </Button>
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs gap-1.5"
                  >
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener"
                      {...(isSpse
                        ? {
                            referer: "https://spse.inaproc.id/",
                            referrer: "https://spse.inaproc.id/",
                          }
                        : {})}
                    >
                      <span>Buka di Tab Baru</span>
                      <ExternalLink className="size-3.5" />
                    </a>
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-center text-xs text-amber-800 dark:text-amber-200">
              <AlertCircle className="mx-auto mb-1.5 size-5 text-amber-600 dark:text-amber-400" />
              <p className="font-medium">URL Konten Tidak Ditemukan</p>
              <p className="mt-1 text-muted-foreground">
                Prospek ini tidak memiliki tautan konten sumber yang dapat diakses.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <DialogFooter className="border-t border-border/60 bg-muted/10 px-6 py-3 shrink-0">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="w-full text-xs"
          >
            Tutup
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
