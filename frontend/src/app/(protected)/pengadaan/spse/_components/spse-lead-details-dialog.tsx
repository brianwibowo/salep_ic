"use client";

import { Building2, Clock, Coins, ExternalLink, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { parseSpseLeadContent } from "@/lib/spse-parser";
import type { Lead } from "@/types/salep";

const salesStatuses: Lead["sales_status"][] = [
  "Belum Dihubungi",
  "Sedang Dihubungi",
  "Closing",
  "Batal",
];

interface SpseLeadDetailsDialogProps {
  lead: Lead | null;
  isMarketing: boolean;
  isUpdatingMarketing: boolean;
  isUpdatingSales: boolean;
  onOpenChange: (open: boolean) => void;
  onMarketingStatusChange: (status: Lead["marketing_status"]) => void;
  onSalesStatusChange: (status: Lead["sales_status"]) => void;
}

export function SpseLeadDetailsDialog({
  lead,
  isMarketing,
  isUpdatingMarketing,
  isUpdatingSales,
  onOpenChange,
  onMarketingStatusChange,
  onSalesStatusChange,
}: SpseLeadDetailsDialogProps) {
  const parsed = lead
    ? parseSpseLeadContent(lead.content, lead.author_name)
    : null;

  return (
    <Dialog open={lead !== null} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto rounded-[5px] sm:max-w-2xl">
        {lead && parsed && (
          <>
            <DialogHeader className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Building2 className="size-3.5 text-slate-400" />
                <span>{parsed.agency || lead.author_name || "Instansi Pemerintah"}</span>
                <span>•</span>
                <span className="text-[#9D0A0E]">SPSE LKPP</span>
              </div>
              <DialogTitle className="text-lg font-bold leading-snug">
                {parsed.title}
              </DialogTitle>
              {parsed.badge && (
                <div>
                  <span
                    className={`inline-flex items-center rounded-[4px] px-2.5 py-0.5 text-xs font-semibold ${
                      parsed.badge.variant === "destructive"
                        ? "border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300"
                        : parsed.badge.variant === "warning"
                          ? "border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                          : "border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
                    }`}
                  >
                    {parsed.badge.text}
                  </span>
                </div>
              )}
            </DialogHeader>

            <div className="space-y-5 pt-2">
              {/* Primary Info Cards */}
              <dl className="grid gap-3 rounded-[5px] border bg-muted/20 p-4 sm:grid-cols-2 text-xs">
                <DetailItem
                  label="Status Validasi Marketing"
                  value={
                    lead.marketing_status === "valid"
                      ? "Valid"
                      : lead.marketing_status === "invalid"
                        ? "Tidak Valid"
                        : "Review (Pending)"
                  }
                />
                <DetailItem label="Status Tindak Lanjut" value={lead.sales_status} />

                {parsed.stage && (
                  <DetailItem
                    label="Tahap Tender Saat Ini"
                    value={parsed.stage}
                    icon={<Clock className="size-3 text-slate-400" />}
                  />
                )}

                {parsed.hps && parsed.hps !== "Rp 0" && (
                  <DetailItem
                    label="Nilai HPS"
                    value={parsed.hps}
                    icon={<Coins className="size-3 text-slate-400" />}
                  />
                )}

                {lead.matched_keyword && (
                  <DetailItem
                    label="Keyword Terkait"
                    value={lead.matched_keyword}
                    icon={<Tag className="size-3 text-slate-400" />}
                  />
                )}

                {lead.industry && (
                  <DetailItem
                    label="Industri"
                    value={lead.industry.replace(/_/g, " ")}
                    capitalize
                  />
                )}
              </dl>

              {/* Status Updater */}
              <div className="rounded-[5px] border p-4">
                <label className="block max-w-sm space-y-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {isMarketing
                    ? "Perbarui Status Validasi Marketing"
                    : "Perbarui Status Tindak Lanjut Sales"}
                  {isMarketing ? (
                    <select
                      className="h-9 w-full rounded-[5px] border bg-background px-3 text-xs font-normal text-foreground focus:outline-none focus:ring-1 focus:ring-[#9D0A0E]"
                      value={lead.marketing_status}
                      disabled={isUpdatingMarketing}
                      onChange={(event) =>
                        onMarketingStatusChange(
                          event.target.value as Lead["marketing_status"],
                        )
                      }
                    >
                      <option value="pending">Review (Pending)</option>
                      <option value="valid">Valid</option>
                      <option value="invalid">Tidak Valid</option>
                    </select>
                  ) : (
                    <select
                      className="h-9 w-full rounded-[5px] border bg-background px-3 text-xs font-normal text-foreground focus:outline-none focus:ring-1 focus:ring-[#9D0A0E]"
                      value={lead.sales_status}
                      disabled={isUpdatingSales}
                      onChange={(event) =>
                        onSalesStatusChange(
                          event.target.value as Lead["sales_status"],
                        )
                      }
                    >
                      {salesStatuses.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  )}
                </label>
              </div>

              {/* Tags & Lists */}
              <LeadList title="Kebutuhan Teridentifikasi" items={lead.needs} />
              <LeadList title="Kendala / Catatan" items={lead.pain_points} />

              {/* Ringkasan Parsed Clean Text */}
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Informasi Mentah Paket
                </h3>
                <div className="whitespace-pre-wrap rounded-[5px] bg-muted/40 p-3.5 text-xs font-mono leading-relaxed text-slate-700 dark:text-slate-300 border">
                  {lead.content.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()}
                </div>
              </div>

              {/* Links */}
              <div className="pt-1">
                <Button
                  asChild
                  variant="outline"
                  className="rounded-[5px] border-[#9D0A0E] text-xs font-medium text-[#9D0A0E] hover:bg-[#9D0A0E]/5 hover:text-[#9D0A0E]"
                >
                  <a href={lead.source_url} target="_blank" rel="noreferrer">
                    Buka Pengumuman di Portal SPSE
                    <ExternalLink className="size-3.5 ml-1.5" />
                  </a>
                </Button>
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
