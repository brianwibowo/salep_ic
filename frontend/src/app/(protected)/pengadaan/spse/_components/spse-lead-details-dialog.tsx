"use client";

import { Building2, Clock, Coins, ExternalLink, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { parseSpseLeadContent } from "@/lib/spse-parser";
import type { Lead } from "@/types/salep";
import { LeadWorkflowPanel } from "@/components/leads/lead-workflow-panel";

interface SpseLeadDetailsDialogProps {
  lead: Lead | null;
  isMarketing: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated: (lead: Lead) => void;
}

export function SpseLeadDetailsDialog({
  lead,
  isMarketing,
  onOpenChange,
  onUpdated,
}: SpseLeadDetailsDialogProps) {
  const parsed = lead
    ? parseSpseLeadContent(lead.content, lead.author_name)
    : null;

  return (
    <Dialog open={lead !== null} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-full max-w-[95vw] sm:max-w-3xl md:max-w-4xl lg:max-w-5xl overflow-hidden p-0 rounded-lg flex flex-col gap-0 shadow-xl border border-border/80">
        {lead && parsed && (
          <>
            {/* Header Popup Dialog */}
            <div className="border-b border-border/80 bg-muted/20 px-6 py-4 pr-12 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shrink-0">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <Building2 className="size-3.5 text-slate-400" />
                    <span className="truncate max-w-[240px]">
                      {parsed.agency || lead.author_name || "Instansi Pemerintah"}
                    </span>
                    <span>•</span>
                    <span className="text-[#9D0A0E]">SPSE LKPP</span>
                  </div>
                  {parsed.badge && (
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                        parsed.badge.variant === "destructive"
                          ? "border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300"
                          : parsed.badge.variant === "warning"
                            ? "border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                            : "border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
                      }`}
                    >
                      {parsed.badge.text}
                    </span>
                  )}
                </div>
                <DialogTitle className="text-xl font-bold tracking-tight text-foreground leading-snug">
                  {parsed.title}
                </DialogTitle>
              </div>

              <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="h-8 gap-1.5 rounded-md border-border/80 text-xs font-medium hover:bg-muted"
                >
                  <a href={lead.source_url} target="_blank" rel="noreferrer">
                    <span>Portal SPSE</span>
                    <ExternalLink className="size-3.5 text-muted-foreground" />
                  </a>
                </Button>
              </div>
            </div>

            {/* Body Popup Dialog */}
            <div className="flex-1 overflow-y-auto p-5 sm:p-6 min-h-0">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* Kolom Kiri: Detail Paket Tender & Informasi (7 cols) */}
                <div className="lg:col-span-7 space-y-5">
                  {/* Primary Info Cards */}
                  <dl className="grid gap-2.5 rounded-lg border border-border/70 bg-muted/20 p-3.5 sm:grid-cols-2 text-xs">
                    {parsed.stage && (
                      <DetailItem
                        label="Tahap Tender Saat Ini"
                        value={parsed.stage}
                        icon={<Clock className="size-3.5 text-slate-400" />}
                      />
                    )}

                    {parsed.hps && parsed.hps !== "Rp 0" && (
                      <DetailItem
                        label="Nilai Pagu / HPS"
                        value={parsed.hps}
                        icon={<Coins className="size-3.5 text-[#9D0A0E]" />}
                      />
                    )}

                    {lead.matched_keyword && (
                      <DetailItem
                        label="Keyword Relevansi"
                        value={lead.matched_keyword}
                        icon={<Tag className="size-3.5 text-slate-400" />}
                      />
                    )}

                    {lead.industry && (
                      <DetailItem
                        label="Industri / Sektor"
                        value={lead.industry.replace(/_/g, " ")}
                        capitalize
                      />
                    )}
                  </dl>

                  {/* Kebutuhan Teridentifikasi */}
                  <LeadList title="Kebutuhan Teridentifikasi" items={lead.needs} />

                  {/* Kendala / Catatan */}
                  <LeadList title="Kendala / Catatan" items={lead.pain_points} />

                  {/* Informasi Mentah Paket */}
                  <div className="rounded-lg border border-border/80 bg-card p-4 space-y-2 shadow-xs">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Ringkasan Konten Pengumuman Tender
                    </h3>
                    <div className="whitespace-pre-wrap rounded-md bg-muted/30 p-3.5 text-xs font-mono leading-relaxed text-slate-800 dark:text-slate-200 border border-border/50 select-text">
                      {lead.content
                        .replace(/<[^>]+>/g, " ")
                        .replace(/\s+/g, " ")
                        .trim()}
                    </div>
                  </div>
                </div>

                {/* Kolom Kanan: Review & Penugasan Sales (5 cols) */}
                <div className="lg:col-span-5 space-y-4">
                  <LeadWorkflowPanel
                    key={lead.lead_id}
                    lead={lead}
                    isMarketing={isMarketing}
                    onUpdated={onUpdated}
                  />
                </div>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function DetailItem({
  label,
  value,
  icon,
  capitalize = false,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  capitalize?: boolean;
}) {
  return (
    <div>
      <dt className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
        {icon}
        {label}
      </dt>
      <dd
        className={`mt-0.5 font-semibold text-slate-900 dark:text-slate-100 ${
          capitalize ? "capitalize" : ""
        }`}
      >
        {value}
      </dd>
    </div>
  );
}

function LeadList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;

  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </h3>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <span
            key={item}
            className="inline-flex items-center rounded-[4px] border bg-background px-2.5 py-1 text-xs font-medium text-slate-700 dark:text-slate-300"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
