"use client";

import { useMemo } from "react";
import {
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  Loader2,
  Building2,
  AlertCircle,
  Activity,
  Layers,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useSpseSchedule } from "@/hooks/leads/use-leads";
import type { Lead } from "@/types/salep";

interface SpseScheduleDialogProps {
  lead: Lead | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SpseScheduleDialog({
  lead,
  open,
  onOpenChange,
}: SpseScheduleDialogProps) {
  const { data, isLoading, isError, error } = useSpseSchedule(
    open && lead ? lead.lead_id : null,
  );

  const stages = data?.stages ?? [];

  const completedCount = useMemo(
    () => stages.filter((s) => s.status === "completed").length,
    [stages],
  );

  const progressPercentage = useMemo(() => {
    if (!stages.length) return 0;
    return Math.round((completedCount / stages.length) * 100);
  }, [completedCount, stages.length]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader className="border-b pb-4">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-primary">
            <Layers className="size-4" />
            <span>Sistem Pengadaan Secara Elektronik (SPSE)</span>
          </div>
          <DialogTitle className="text-xl font-bold">
            Tahapan & Jadwal Proses Tender
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {lead?.author_name ? (
              <span className="flex items-center gap-1.5 font-medium text-foreground">
                <Building2 className="size-4 shrink-0 text-muted-foreground" />
                {lead.author_name}
              </span>
            ) : (
              "Informasi jadwal lelang resmi dari LPSE/SPSE Nasional"
            )}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="size-8 animate-spin text-primary" />
            <p className="mt-3 text-sm font-medium">
              Mengambil progres tahapan jadwal dari SPSE…
            </p>
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-destructive">
            <div className="flex items-center gap-2 font-semibold">
              <AlertCircle className="size-5" />
              <span>Gagal memuat jadwal</span>
            </div>
            <p className="mt-1 text-sm">
              {error instanceof Error
                ? error.message
                : "Terjadi gangguan saat menghubungi server SPSE."}
            </p>
          </div>
        ) : data ? (
          <div className="space-y-6 pt-2">
            {/* Header Status Ringkasan */}
            <div className="rounded-lg border bg-card p-4 shadow-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
                <div>
                  <span className="text-xs text-muted-foreground">ID Tender SPSE:</span>
                  <span className="ml-1.5 font-mono text-sm font-bold text-foreground">
                    #{data.tender_id}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Progres:</span>
                  <Badge variant="outline" className="font-semibold text-primary">
                    {completedCount} dari {stages.length} Tahap Selesai ({progressPercentage}%)
                  </Badge>
                </div>
              </div>

              <div className="mt-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Tahap saat ini:</span>
                  <span className="flex items-center gap-1 font-semibold text-primary">
                    <Activity className="size-3.5 animate-pulse" />
                    {data.current_stage}
                  </span>
                </div>
                <Progress value={progressPercentage} className="mt-2 h-2" />
              </div>
            </div>

            {/* Timeline Stepper */}
            <div>
              <h4 className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Rincian Jadwal Pelaksanaan Lelang
              </h4>

              <div className="relative pl-6">
                {/* Garis vertikal timeline */}
                <div className="absolute top-3 bottom-3 left-2.5 w-0.5 bg-border" />

                <div className="space-y-6">
                  {stages.map((stage) => {
                    const isCompleted = stage.status === "completed";
                    const isActive = stage.status === "active";
                    const hasChanges =
                      stage.changes && stage.changes.toLowerCase() !== "tidak ada";

                    return (
                      <div key={stage.no} className="relative flex items-start gap-4">
                        {/* Dot / Icon */}
                        <div
                          className={`absolute -left-6 flex size-5.5 -translate-x-1/2 items-center justify-center rounded-full border text-xs font-bold transition-colors ${
                            isCompleted
                              ? "border-emerald-500 bg-emerald-500 text-white"
                              : isActive
                                ? "border-primary bg-primary text-primary-foreground ring-4 ring-primary/20"
                                : "border-muted-foreground/30 bg-background text-muted-foreground"
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="size-3.5" />
                          ) : isActive ? (
                            <Activity className="size-3 animate-pulse" />
                          ) : (
                            <span>{stage.no}</span>
                          )}
                        </div>

                        {/* Content */}
                        <div
                          className={`flex-1 rounded-md border p-3.5 transition-colors ${
                            isActive
                              ? "border-primary/40 bg-primary/5 shadow-xs"
                              : "bg-card/50"
                          }`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <h5
                              className={`text-sm font-semibold ${
                                isActive ? "text-primary" : "text-foreground"
                              }`}
                            >
                              {stage.stage}
                            </h5>
                            {isActive ? (
                              <Badge className="bg-primary text-xs text-primary-foreground">
                                Sedang Berlangsung
                              </Badge>
                            ) : isCompleted ? (
                              <Badge
                                variant="outline"
                                className="border-emerald-500/40 bg-emerald-50 text-xs text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                              >
                                Selesai
                              </Badge>
                            ) : (
                              <Badge
                                variant="outline"
                                className="border-muted text-xs text-muted-foreground"
                              >
                                Akan Datang
                              </Badge>
                            )}
                          </div>

                          <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
                            <span className="inline-flex items-center gap-1">
                              <Calendar className="size-3.5" />
                              Mulai: <strong className="text-foreground">{stage.start}</strong>
                            </span>
                            <span className="inline-flex items-center gap-1">
                              <Clock className="size-3.5" />
                              Sampai: <strong className="text-foreground">{stage.end}</strong>
                            </span>
                          </div>

                          {hasChanges && (
                            <div className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                              <span className="font-medium">Catatan:</span> {stage.changes}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Footer Action */}
            <div className="flex items-center justify-between border-t pt-4">
              <span className="text-xs text-muted-foreground">
                Data diperbarui langsung dari portal lelang publik inaproc.id
              </span>
              {data.source_url && (
                <a
                  href={data.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent"
                >
                  Buka Portal Resmi SPSE <ExternalLink className="size-3.5" />
                </a>
              )}
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
