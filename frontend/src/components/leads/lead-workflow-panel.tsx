"use client";

import { useState } from "react";
import {
  AlertCircle,
  Check,
  Clock,
  MessageSquareQuote,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  UserRound,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  useAssignableSales,
  useLeadDetail,
  useUpdateLeadStatus,
  useUpdateSalesStatus,
} from "@/hooks/leads/use-leads";
import { ApiServiceError } from "@/utils/api/apiService";
import type { Lead, SalesUser } from "@/types/salep";
import { SalesProgressHistory } from "./lead-sales-progress";

const statusConfig = {
  valid: {
    label: "Valid",
    className:
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-semibold",
  },
  pending: {
    label: "Menunggu Review",
    className:
      "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400 font-semibold",
  },
  invalid: {
    label: "Tidak Valid",
    className:
      "border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 font-medium",
  },
};

const salesStatuses: Lead["sales_status"][] = [
  "Belum Dihubungi",
  "Sedang Dihubungi",
  "Closing",
  "Batal",
];

const dateTime = (value: string) =>
  new Date(value).toLocaleString("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Jakarta",
  });

/** Clean, professional review & assignment workflow panel */
export function LeadWorkflowPanel({
  lead,
  isMarketing,
  onUpdated,
}: {
  lead: Lead;
  isMarketing: boolean;
  onUpdated: (lead: Lead) => void;
}) {
  const detail = useLeadDetail(lead);
  const sales = useAssignableSales(isMarketing);
  const current = detail.data;

  if (detail.isError) {
    return (
      <section
        role="alert"
        className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-sm"
      >
        <p className="font-medium text-destructive">
          {detail.error.message || "Detail lead tidak dapat dimuat."}
        </p>
        <Button
          variant="outline"
          size="sm"
          className="mt-3 text-xs"
          onClick={() => void detail.refetch()}
        >
          Coba lagi
        </Button>
      </section>
    );
  }

  const badge = statusConfig[current.marketing_status] || statusConfig.pending;

  return (
    <section className="overflow-hidden rounded-lg border border-border/80 bg-card shadow-xs">
      {/* Header Panel */}
      <div className="border-b border-border/60 bg-muted/20 px-4 py-3 sm:px-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {isMarketing ? (
              <ShieldCheck className="size-4 text-[#9D0A0E]" />
            ) : (
              <UserCheck className="size-4 text-[#9D0A0E]" />
            )}
            <h3 className="text-sm font-bold text-foreground">
              {isMarketing ? "Review & Penugasan Sales" : "Tindak Lanjut Sales"}
            </h3>
          </div>
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>
      </div>

      <div className="space-y-4 p-4 sm:p-5">
        {/* Ringkasan Status Saat Ini */}
        <div className="rounded-md border border-border/60 bg-muted/30 p-3.5 text-xs">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <span className="text-muted-foreground block text-[11px] font-medium uppercase tracking-wider">
                Reviewer Marketing
              </span>
              <p className="mt-1 font-semibold text-foreground">
                {current.marketing_reviewed_by_username || "Belum direview"}
              </p>
              {current.marketing_reviewed_at && (
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  {dateTime(current.marketing_reviewed_at)}
                </p>
              )}
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px] font-medium uppercase tracking-wider">
                Sales PIC (Penanggung Jawab)
              </span>
              <p className="mt-1 flex items-center gap-1.5 font-semibold text-foreground">
                <UserRound className="size-3.5 text-muted-foreground" />
                {current.assignment?.sales_username || "Belum ditugaskan"}
              </p>
              {current.assignment && (
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  Ditugaskan {dateTime(current.assignment.assigned_at)}
                </p>
              )}
            </div>
          </div>

          {current.marketing_review_note && (
            <div className="mt-3 border-t border-border/50 pt-2.5">
              <span className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
                <MessageSquareQuote className="size-3" />
                Catatan Review:
              </span>
              <p className="mt-1 text-xs italic leading-relaxed text-foreground/90">
                &ldquo;{current.marketing_review_note}&rdquo;
              </p>
            </div>
          )}
        </div>

        {/* Action Form */}
        {isMarketing ? (
          <ReviewForm
            key={`${current.lead_id}:${current.review_version}`}
            lead={current}
            sales={sales.data ?? []}
            salesLoading={sales.isPending}
            salesError={sales.error?.message}
            refreshing={detail.isFetching}
            onRetrySales={() => void sales.refetch()}
            onUpdated={onUpdated}
            onReload={async () => {
              const result = await detail.refetch();
              if (result.error) throw result.error;
              if (result.data) onUpdated(result.data);
            }}
          />
        ) : (
          <SalesFollowUp lead={current} onUpdated={onUpdated} />
        )}
      </div>

      {/* Riwayat Progress Sales */}
      <SalesProgressHistory
        lead={current}
        refreshing={detail.isFetching}
        onRefresh={() => void detail.refetch()}
      />
    </section>
  );
}

function ReviewForm({
  lead,
  sales,
  salesLoading,
  salesError,
  refreshing,
  onRetrySales,
  onUpdated,
  onReload,
}: {
  lead: Lead;
  sales: SalesUser[];
  salesLoading: boolean;
  salesError?: string;
  refreshing: boolean;
  onRetrySales: () => void;
  onUpdated: (lead: Lead) => void;
  onReload: () => Promise<void>;
}) {
  const [status, setStatus] = useState(lead.marketing_status);
  const [salesUserId, setSalesUserId] = useState(
    lead.assignment?.sales_user_id ?? "",
  );
  const [note, setNote] = useState(lead.marketing_review_note ?? "");
  const [reloadError, setReloadError] = useState("");
  const review = useUpdateLeadStatus(onUpdated);
  const conflict =
    review.error instanceof ApiServiceError && review.error.status === 409;
  const activeRecipient = sales.some((user) => user.user_id === salesUserId);
  const canSave =
    !refreshing &&
    !review.isPending &&
    !conflict &&
    (status !== "valid" || (!salesLoading && !salesError && activeRecipient));

  return (
    <form
      className="space-y-4 pt-1"
      onSubmit={(event) => {
        event.preventDefault();
        if (!canSave) return;
        review.mutate({
          leadId: lead.lead_id,
          status,
          expectedVersion: lead.review_version,
          salesUserId: status === "valid" ? salesUserId : undefined,
          reviewNote: note,
        });
      }}
    >
      <fieldset
        disabled={review.isPending || refreshing || conflict}
        className="space-y-3.5 disabled:opacity-60"
      >
        {/* Pilihan Hasil Review */}
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          <span>Kualifikasi Status Lead</span>
          <select
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-[#9D0A0E]"
            value={status}
            onChange={(event) =>
              setStatus(event.target.value as Lead["marketing_status"])
            }
          >
            <option value="pending">Menunggu review</option>
            <option value="valid">Valid — Siap ditugaskan ke Sales</option>
            <option value="invalid">Tidak valid / Tidak relevan</option>
          </select>
        </label>

        {/* Pilihan Sales PIC (Hanya jika Valid) */}
        {status === "valid" && (
          <div className="rounded-md border border-[#9D0A0E]/30 bg-[#9D0A0E]/5 p-3.5 space-y-2">
            <label className="block space-y-1.5 text-xs font-semibold text-foreground">
              <span className="flex items-center gap-1.5">
                <UserRound className="size-3.5 text-[#9D0A0E]" />
                Tugaskan ke Sales PIC <span className="text-[#9D0A0E]">*</span>
              </span>
              <p className="text-[11px] font-normal text-muted-foreground">
                Pilih akun Sales yang akan bertanggung jawab menindaklanjuti
                prospek ini.
              </p>
              <select
                required
                disabled={salesLoading || !!salesError}
                value={salesUserId}
                className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-[#9D0A0E]"
                onChange={(event) => setSalesUserId(event.target.value)}
              >
                <option value="">
                  {salesLoading
                    ? "Memuat daftar akun Sales…"
                    : "— Pilih Sales penanggung jawab —"}
                </option>
                {lead.assignment &&
                  !sales.some(
                    (user) => user.user_id === lead.assignment?.sales_user_id,
                  ) && (
                    <option value={lead.assignment.sales_user_id} disabled>
                      {lead.assignment.sales_username || "Sales sebelumnya"}{" "}
                      (nonaktif)
                    </option>
                  )}
                {sales.map((user) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.username}
                  </option>
                ))}
              </select>
            </label>

            {!salesLoading && !salesError && sales.length === 0 && (
              <span className="block text-xs font-normal text-amber-600 dark:text-amber-400">
                Belum ada akun Sales aktif. Hubungi Super Admin untuk membuat
                akun Sales.
              </span>
            )}
          </div>
        )}

        {status !== "valid" && lead.assignment && (
          <p className="rounded border border-amber-500/20 bg-amber-500/10 p-2 text-xs text-amber-800 dark:text-amber-200">
            Penugasan kepada{" "}
            <strong>{lead.assignment.sales_username || "Sales"}</strong> akan
            ditutup. Riwayat tindak lanjut tetap disimpan.
          </p>
        )}

        {/* Catatan Review */}
        <label className="block space-y-1.5 text-xs font-semibold text-foreground">
          <span>
            Catatan Review & Arahan{" "}
            <span className="font-normal text-muted-foreground">
              (opsional)
            </span>
          </span>
          <Textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            maxLength={2000}
            placeholder="Tambahkan konteks, arahan khusus, atau alasan review untuk Sales..."
            className="min-h-20 resize-y text-xs font-normal leading-relaxed"
          />
        </label>
      </fieldset>

      {status === "valid" && salesError && (
        <div
          role="alert"
          className="flex items-center justify-between gap-3 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive"
        >
          <p>Daftar Sales gagal dimuat.</p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRetrySales}
          >
            Coba lagi
          </Button>
        </div>
      )}

      {review.error && (
        <div
          role="alert"
          className="space-y-2 rounded-md border border-amber-300/80 bg-amber-50/60 p-3 text-xs text-amber-900 dark:bg-amber-950/20 dark:text-amber-200"
        >
          <p className="flex items-start gap-1.5 font-medium">
            <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
            {review.error.message}
          </p>
          {conflict && (
            <>
              <p className="text-[11px] text-muted-foreground">
                Perubahan belum tersimpan karena terdapat data terbaru dari user
                lain.
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                disabled={refreshing}
                onClick={async () => {
                  try {
                    await onReload();
                    review.reset();
                    setReloadError("");
                  } catch {
                    setReloadError(
                      "Data terbaru belum dapat dimuat. Silakan coba lagi.",
                    );
                  }
                }}
              >
                <RefreshCw className="size-3" /> Muat data terbaru
              </Button>
            </>
          )}
          {reloadError && <p className="text-destructive">{reloadError}</p>}
        </div>
      )}

      {/* Submit Button */}
      <div className="pt-2">
        <Button
          type="submit"
          disabled={!canSave}
          className="h-10 w-full gap-2 rounded-md bg-[#9D0A0E] text-xs font-semibold text-white cursor-pointer shadow-xs transition-colors hover:bg-[#83080C] disabled:opacity-50"
        >
          <Check className="size-4" />
          {review.isPending
            ? "Menyimpan review…"
            : status === "valid"
              ? "Simpan Review & Assign ke Sales"
              : "Simpan Hasil Review"}
        </Button>
      </div>
    </form>
  );
}

function SalesFollowUp({
  lead,
  onUpdated,
}: {
  lead: Lead;
  onUpdated: (lead: Lead) => void;
}) {
  const [status, setStatus] = useState(lead.sales_status);
  const [note, setNote] = useState("");
  const update = useUpdateSalesStatus();

  return (
    <form
      className="space-y-3.5 pt-1"
      onSubmit={(event) => {
        event.preventDefault();
        if (!note.trim() || update.isPending) return;
        update.mutate(
          { leadId: lead.lead_id, status, note },
          {
            onSuccess: (updated) => {
              onUpdated(updated);
              setStatus(updated.sales_status);
              setNote("");
            },
          },
        );
      }}
    >
      <label className="block space-y-1.5 text-xs font-semibold text-foreground">
        <span>Status Tindak Lanjut</span>
        <select
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm font-normal text-foreground shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-[#9D0A0E]"
          value={status}
          disabled={update.isPending}
          onChange={(event) =>
            setStatus(event.target.value as Lead["sales_status"])
          }
        >
          {salesStatuses.map((value) => (
            <option key={value}>{value}</option>
          ))}
        </select>
      </label>

      <label className="block space-y-1.5 text-xs font-semibold text-foreground">
        <span>Catatan Aktivitas / Follow-Up</span>
        <Textarea
          required
          maxLength={2000}
          value={note}
          disabled={update.isPending}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Misal: Sudah menghubungi via WhatsApp, klien meminta penawaran paket cloud VPS..."
          className="min-h-20 resize-y text-xs font-normal leading-relaxed"
        />
      </label>

      {update.error && (
        <p role="alert" className="text-xs text-destructive">
          {update.error.message}
        </p>
      )}

      <Button
        type="submit"
        disabled={!note.trim() || update.isPending}
        className="h-10 w-full rounded-md bg-[#9D0A0E] text-xs font-semibold text-white shadow-xs transition-colors hover:bg-[#83080C] disabled:opacity-50"
      >
        {update.isPending ? "Menyimpan progres…" : "Simpan Tindak Lanjut"}
      </Button>
    </form>
  );
}
