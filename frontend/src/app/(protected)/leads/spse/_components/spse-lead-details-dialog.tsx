"use client";

import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  return (
    <Dialog open={lead !== null} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto rounded-[5px] sm:max-w-2xl">
        {lead && (
          <>
            <DialogHeader>
              <DialogTitle>Detail Paket SPSE</DialogTitle>
              <DialogDescription>
                {lead.author_name || "Paket tanpa nama"} · SPSE
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-5">
              <dl className="grid gap-4 rounded-[5px] border p-4 sm:grid-cols-2">
                <DetailItem label="Skor lead" value={`${lead.lead_score}/100`} />
                <DetailItem
                  label="Keyakinan analisis"
                  value={`${Math.round(lead.confidence * 100)}%`}
                />
                <DetailItem label="Status marketing" value={lead.marketing_status} capitalize />
                <DetailItem label="Tindak lanjut" value={lead.sales_status} />
                {lead.industry && (
                  <DetailItem
                    label="Industri"
                    value={lead.industry.replace(/_/g, " ")}
                  />
                )}
                {lead.matched_keyword && (
                  <DetailItem label="Keyword" value={lead.matched_keyword} />
                )}
              </dl>

              <label className="block max-w-sm space-y-2 text-sm font-medium">
                {isMarketing ? "Ubah status marketing" : "Ubah status tindak lanjut"}
                {isMarketing ? (
                  <select
                    className="h-10 w-full rounded-[5px] border bg-background px-3"
                    value={lead.marketing_status}
                    disabled={isUpdatingMarketing}
                    onChange={(event) =>
                      onMarketingStatusChange(
                        event.target.value as Lead["marketing_status"],
                      )
                    }
                  >
                    <option value="pending">Menunggu review</option>
                    <option value="valid">Valid</option>
                    <option value="invalid">Tidak valid</option>
                  </select>
                ) : (
                  <select
                    className="h-10 w-full rounded-[5px] border bg-background px-3"
                    value={lead.sales_status}
                    disabled={isUpdatingSales}
                    onChange={(event) =>
                      onSalesStatusChange(event.target.value as Lead["sales_status"])
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

              <LeadList title="Kebutuhan" items={lead.needs} />
              <LeadList title="Kendala" items={lead.pain_points} />

              {lead.recommended_services.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-semibold">Rekomendasi layanan</h3>
                  <div className="space-y-2">
                    {lead.recommended_services.map((service) => (
                      <div key={service.product_id} className="rounded-[5px] border p-3">
                        <div className="flex items-center justify-between gap-3 text-sm font-medium">
                          <span>{service.product_name}</span>
                          <span className="shrink-0 text-primary">{service.match_score}%</span>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{service.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h3 className="mb-2 text-sm font-semibold">Ringkasan paket</h3>
                <p className="whitespace-pre-wrap rounded-[5px] bg-muted/50 p-4 text-sm leading-6">
                  {lead.content}
                </p>
              </div>

              <Button asChild variant="link" className="h-auto px-0">
                <a href={lead.source_url} target="_blank" rel="noreferrer">
                  Buka pengumuman SPSE <ExternalLink className="size-4" />
                </a>
              </Button>
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
  capitalize = false,
}: {
  label: string;
  value: string;
  capitalize?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={`mt-1 font-medium ${capitalize ? "capitalize" : ""}`}>{value}</dd>
    </div>
  );
}

function LeadList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
