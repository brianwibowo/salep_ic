"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  Layers,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useSpseSchedule } from "@/hooks/leads/use-leads";
import type { Lead } from "@/types/salep";

interface SpseScheduleCardProps {
  lead: Lead | null;
  defaultExpanded?: boolean;
}

export function SpseScheduleCard({
  lead,
  defaultExpanded = false,
}: SpseScheduleCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const { data, isLoading, isError, error, refetch, isRefetching } =
    useSpseSchedule(lead ? lead.lead_id : null);

  const stages = useMemo(() => data?.stages ?? [], [data?.stages]);

  const completedCount = useMemo(
    () => stages.filter((s) => s.status === "completed").length,
    [stages],
  );

  const progressPercentage = useMemo(() => {
    if (!stages.length) return 0;
    return Math.round((completedCount / stages.length) * 100);
  }, [completedCount, stages.length]);

  const activeStage = useMemo(
    () => stages.find((s) => s.status === "active"),
    [stages],
  );

  if (!lead) return null;

  return (
    <div className="rounded-lg border border-border/80 bg-card shadow-xs overflow-hidden">
      {/* Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 border-b border-border/70 bg-muted/20 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-md bg-[#9D0A0E]/10 text-[#9D0A0E] dark:bg-[#9D0A0E]/20">
            <Calendar className="size-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Pantau Jadwal & Progres Lelang SPSE
            </h4>
            {data?.tender_id && (
              <span className="text-[11px] font-mono text-muted-foreground">
                ID Tender: #{data.tender_id}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {data && (
            <Badge
              variant="outline"
              className="text-[11px] font-semibold text-[#9D0A0E] border-[#9D0A0E]/30 bg-[#9D0A0E]/5"
            >
              {completedCount}/{stages.length} Tahap Selesai ({progressPercentage}%)
            </Badge>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={() => void refetch()}
            disabled={isLoading || isRefetching}
            title="Muat ulang jadwal"
            aria-label="Muat ulang jadwal"
            className="size-7 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw
              className={`size-3.5 ${isRefetching ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
      </div>

      {/* Body Card */}
      <div className="p-4 space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center gap-2.5 py-6 text-muted-foreground text-xs">
            <Loader2 className="size-4 animate-spin text-[#9D0A0E]" />
            <span>Mengambil jadwal tahapan lelang dari SPSE LKPP…</span>
          </div>
        ) : isError ? (
          <div className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-xs text-destructive flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="size-4 shrink-0" />
              <span>
                {error instanceof Error
                  ? error.message
                  : "Gagal memuat jadwal lelang SPSE."}
              </span>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 text-xs shrink-0"
              onClick={() => void refetch()}
            >
              Coba Lagi
            </Button>
          </div>
        ) : data && stages.length > 0 ? (
          <>
            {/* Progres Bar & Tahap Aktif Highlight */}
            <div className="rounded-lg border border-border/60 bg-muted/30 p-3.5 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                <span className="font-medium text-muted-foreground flex items-center gap-1.5">
                  <Activity className="size-3.5 text-[#9D0A0E] animate-pulse" />
                  Tahap Saat Ini:
                </span>
                <span className="font-bold text-foreground">
                  {data.current_stage || activeStage?.stage || "Tahap Berlangsung"}
                </span>
              </div>

              <Progress value={progressPercentage} className="h-2" />

              {activeStage && (
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 pt-1 text-xs text-muted-foreground border-t border-border/50">
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="size-3 text-slate-400" />
                    <span>Mulai:</span>
                    <strong className="text-foreground font-semibold">
                      {activeStage.start}
                    </strong>
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Clock className="size-3 text-[#9D0A0E]" />
                    <span>Batas Akhir:</span>
                    <strong className="text-[#9D0A0E] font-semibold">
                      {activeStage.end}
                    </strong>
                  </span>
                  {activeStage.changes &&
                    activeStage.changes.toLowerCase() !== "tidak ada" && (
                      <span className="text-amber-600 dark:text-amber-400 text-[11px] font-medium">
                        (Perubahan: {activeStage.changes})
                      </span>
                    )}
                </div>
              )}
            </div>

            {/* Toggle Expand / Collapse Seluruh Tahap */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setIsExpanded((prev) => !prev)}
                className="w-full flex items-center justify-between rounded-md border border-border/60 bg-background px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-muted/50 dark:text-slate-200 transition"
              >
                <span className="flex items-center gap-1.5">
                  <Layers className="size-3.5 text-muted-foreground" />
                  <span>
                    {isExpanded
                      ? "Sembunyikan Rincian Semua Tahapan"
                      : `Lihat Rincian Seluruh Tahapan (${stages.length} Tahap)`}
                  </span>
                </span>
                {isExpanded ? (
                  <ChevronUp className="size-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="size-4 text-muted-foreground" />
                )}
              </button>

              {/* Rincian Stepper Timeline saat expanded */}
              {isExpanded && (
                <div className="mt-4 relative pl-5 pr-1 border-l-2 border-border/70 ml-2 space-y-4">
                  {stages.map((stage) => {
                    const isCompleted = stage.status === "completed";
                    const isActive = stage.status === "active";
                    const hasChanges =
                      stage.changes && stage.changes.toLowerCase() !== "tidak ada";

                    return (
                      <div key={stage.no} className="relative group">
                        {/* Dot indicator */}
                        <div
                          className={`absolute -left-[27px] top-1 flex size-5 items-center justify-center rounded-full border text-[10px] font-bold ${
                            isCompleted
                              ? "border-emerald-500 bg-emerald-500 text-white"
                              : isActive
                                ? "border-[#9D0A0E] bg-[#9D0A0E] text-white ring-4 ring-[#9D0A0E]/20"
                                : "border-slate-300 bg-background text-slate-500 dark:border-slate-700"
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="size-3" />
                          ) : isActive ? (
                            <Activity className="size-3 animate-pulse" />
                          ) : (
                            <span>{stage.no}</span>
                          )}
                        </div>

                        {/* Card Stage */}
                        <div
                          className={`rounded-md border p-3 text-xs transition ${
                            isActive
                              ? "border-[#9D0A0E]/40 bg-[#9D0A0E]/5 shadow-xs"
                              : "border-border/60 bg-card/60"
                          }`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-1.5">
                            <h5
                              className={`font-semibold ${
                                isActive ? "text-[#9D0A0E]" : "text-foreground"
                              }`}
                            >
                              {stage.stage}
                            </h5>
                            {isActive ? (
                              <Badge className="bg-[#9D0A0E] text-[10px] text-white px-2 py-0.5">
                                Sedang Berlangsung
                              </Badge>
                            ) : isCompleted ? (
                              <Badge
                                variant="outline"
                                className="border-emerald-500/40 bg-emerald-50 text-[10px] text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                              >
                                Selesai
                              </Badge>
                            ) : (
                              <Badge
                                variant="outline"
                                className="border-muted text-[10px] text-muted-foreground"
                              >
                                Akan Datang
                              </Badge>
                            )}
                          </div>

                          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                            <span>
                              Mulai: <strong className="text-foreground">{stage.start}</strong>
                            </span>
                            <span>•</span>
                            <span>
                              Sampai: <strong className="text-foreground">{stage.end}</strong>
                            </span>
                          </div>

                          {hasChanges && (
                            <p className="mt-1.5 text-[11px] text-amber-600 dark:text-amber-400">
                              <span className="font-semibold">Catatan:</span> {stage.changes}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Official LPSE link */}
            {data.source_url && (
              <div className="pt-1 flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Sumber jadwal resmi SPSE LKPP</span>
                <a
                  href={data.source_url}
                  target="_blank"
                  rel="noopener"
                  referer="https://spse.inaproc.id/"
                  referrer="https://spse.inaproc.id/"
                  className="inline-flex items-center gap-1 text-[#9D0A0E] hover:underline font-medium"
                >
                  Buka Portal SPSE <ExternalLink className="size-3" />
                </a>
              </div>
            )}
          </>
        ) : (
          <div className="rounded-md border border-border/70 bg-muted/20 p-3.5 text-center text-xs text-muted-foreground">
            <p>Jadwal tahapan tender untuk paket ini belum tersedia dari SPSE.</p>
          </div>
        )}
      </div>
    </div>
  );
}
