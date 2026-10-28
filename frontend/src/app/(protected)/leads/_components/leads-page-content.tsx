"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type PaginationState,
} from "@tanstack/react-table";
import {
  Compass,
  Eye,
  ExternalLink,
  Search,
  RefreshCw,
  Trash2,
  Calendar,
  Clock,
  Loader2,
  FileText,
  Target,
  AlertCircle,
  Sparkles,
  Tag,
  QrCode,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DataTablePagination } from "@/components/ui/data-table-pagination";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { LeadWorkflowPanel } from "@/components/leads/lead-workflow-panel";
import { LeadFiltersPopover } from "@/components/leads/lead-filters-popover";
import { SalesProgressCell } from "@/components/leads/lead-sales-progress";
import { createLeadFilters, leadQueryFilters } from "@/lib/lead-filters";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SpseScheduleDialog } from "@/components/leads/spse-schedule-dialog";
import { SocialMediaDiscoveryDialog } from "@/components/leads/social-media-discovery-dialog";
import { LeadQrCodeDialog } from "@/components/leads/lead-qrcode-dialog";
import { SpseScheduleCard } from "@/components/leads/spse-schedule-card";
import { useSession } from "@/hooks/auth/use-auth";
import { useDebounce } from "@/hooks/use-debounce";
import { useManualSearch } from "@/hooks/discovery/use-discovery";
import {
  useAnalyzeUrl,
  useDeleteLead,
  useLeads,
} from "@/hooks/leads/use-leads";
import { Lead } from "@/types/salep";
import { formatDate } from "@/utils/formatting/string";

export function LeadsPageContent({
  sourcePreset = "all",
}: {
  sourcePreset?: "all" | "social_media" | "spse";
}) {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const [selectedSpseLead, setSelectedSpseLead] = useState<Lead | null>(null);
  const [search, setSearch] = useState("");
  const [filterValues, setFilterValues] = useState(() =>
    createLeadFilters(sourcePreset),
  );
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedQrLead, setSelectedQrLead] = useState<Lead | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Lead | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 50,
  });
  const debouncedSearch = useDebounce(search, 300);
  const page = pagination.pageIndex + 1;
  const filters = {
    search: debouncedSearch,
    ...leadQueryFilters(filterValues, isMarketing),
    page,
    limit: pagination.pageSize,
  };
  const leads = useLeads(filters);
  const deleteLead = useDeleteLead();
  const searchMutation = useManualSearch();
  const analyzeUrlMutation = useAnalyzeUrl();
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);

  const setFilter = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    setPagination((current) => ({ ...current, pageIndex: 0 }));
  };

  const columns = useMemo<ColumnDef<Lead>[]>(
    () => [
      {
        accessorKey: "author_name",
        header: "Prospek",
        cell: ({ row }) => {
          const lead = row.original;
          const isSpse = lead.source === "spse";
          return (
            <div className="max-w-xl whitespace-normal">
              <p className="font-medium">
                {lead.author_name || "Prospek tanpa nama"}
              </p>
              <p className="mt-1 line-clamp-2 text-muted-foreground">
                {lead.content}
              </p>
              {lead.needs?.length > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Kebutuhan: {lead.needs.join(", ")}
                </p>
              )}
              {isSpse && (
                <div className="mt-2.5">
                  <button
                    type="button"
                    onClick={() => setSelectedSpseLead(lead)}
                    className="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-700 transition hover:bg-blue-500/20 dark:text-blue-300"
                  >
                    <Calendar className="size-3.5" />
                    <span>Pantau Jadwal & Progres SPSE</span>
                  </button>
                </div>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: "source",
        header: "Sumber",
        cell: ({ row }) => (
          <span className="capitalize">{row.original.source}</span>
        ),
      },
      {
        accessorKey: "created_at",
        header: "Dibuat",
        cell: ({ row }) =>
          row.original.created_at ? formatDate(row.original.created_at) : "—",
      },
      {
        accessorKey: "lead_score",
        header: "Skor",
        cell: ({ row }) => (
          <span className="rounded-full bg-primary/10 px-2.5 py-1 font-semibold text-primary">
            {row.original.quality_flags?.includes("llm_analysis_failed")
              ? "Belum dianalisis"
              : row.original.lead_score}
          </span>
        ),
      },
      {
        accessorKey: "marketing_status",
        header: "Status",
        cell: ({ row }) => {
          const lead = row.original;
          return <StatusPill value={lead.marketing_status} />;
        },
      },
      {
        accessorKey: "sales_status",
        header: "Tindak lanjut",
        cell: ({ row }) => {
          const lead = row.original;
          return <SalesProgressCell lead={lead} />;
        },
      },
      {
        id: "assigned-sales",
        header: "Sales PIC",
        cell: ({ row }) => (
          <span className="text-sm">
            {row.original.assignment?.sales_username || "Belum ditugaskan"}
          </span>
        ),
      },
      // {
      //   id: "post",
      //   header: "Tautan & Jadwal",
      //   cell: ({ row }) => {
      //     const lead = row.original;
      //     const isSpse = lead.source === "spse";
      //     return (
      //       <div className="flex flex-col gap-1.5 whitespace-nowrap">
      //         <div className="flex items-center gap-1.5">
      //           <a
      //             className="inline-flex items-center gap-1 text-primary hover:underline"
      //             href={lead.source_url}
      //             target="_blank"
      //             rel="noreferrer"
      //           >
      //             {isSpse ? "Pengumuman" : "Buka"}{" "}
      //             <ExternalLink className="size-3.5" />
      //           </a>
      //         </div>
      //         {lead.source_url && (
      //           <button
      //             type="button"
      //             onClick={() => setSelectedQrLead(lead)}
      //             className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-slate-600 hover:text-[#9D0A0E] hover:underline dark:text-slate-400 dark:hover:text-red-400"
      //             title="Generate QR code untuk buka di HP"
      //           >
      //             <QrCode className="size-3.5 text-[#9D0A0E]" />
      //             <span>Generate QR</span>
      //           </button>
      //         )}
      //         {isSpse && (
      //           <button
      //             type="button"
      //             onClick={() => setSelectedSpseLead(lead)}
      //             className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
      //           >
      //             <Clock className="size-3" /> Jadwal Lelang
      //           </button>
      //         )}
      //       </div>
      //     );
      //   },
      // },
      {
        id: "actions",
        header: "Aksi",
        cell: ({ row }) => {
          const lead = row.original;
          return (
            <div className="flex items-center gap-1 whitespace-nowrap">
              {/* {lead.source_url && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Generate QR Code"
                  title="Generate QR Code"
                  className="text-slate-600 hover:text-[#9D0A0E] hover:bg-[#9D0A0E]/10"
                  onClick={() => setSelectedQrLead(lead)}
                >
                  <QrCode className="size-4" />
                </Button>
              )} */}
              <Button
                type="button"
                variant={isMarketing ? "outline" : "ghost"}
                size={isMarketing ? "sm" : "icon-sm"}
                aria-label={
                  isMarketing ? "Review dan assign lead" : "Lihat detail lead"
                }
                title={isMarketing ? "Review & assign" : "Detail"}
                className="text-slate-700 hover:text-slate-950"
                onClick={() => {
                  setSelectedLead(lead);
                }}
              >
                <Eye className="size-4" />
                {isMarketing && <span>Review & assign</span>}
              </Button>
              {isMarketing && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Hapus lead"
                  title="Hapus"
                  className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => setPendingDelete(lead)}
                >
                  <Trash2 className="size-4" />
                </Button>
              )}
            </div>
          );
        },
      },
    ],
    [isMarketing],
  );

  const data = leads.data?.items ?? [];
  const total = leads.data?.pagination.total ?? 0;
  const pageCount = Math.ceil(total / pagination.pageSize);
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount,
    onPaginationChange: setPagination,
    state: { pagination },
  });

  return (
    <div className="w-full min-w-0 max-w-full space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">
          {sourcePreset === "social_media"
            ? "Leads Sosial Media"
            : sourcePreset === "spse"
              ? "Leads SPSE"
              : "Leads"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {isMarketing
            ? "Tinjau dan validasi prospek yang ditemukan."
            : "Kelola tindak lanjut untuk prospek yang sudah valid."}
        </p>
      </div>

      {leads.isError && (
        <p
          role="alert"
          className="rounded-[5px] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
        >
          {leads.error.message}
        </p>
      )}

      {/* Indikator Discovery Background Process */}
      {(searchMutation.isPending || analyzeUrlMutation.isPending) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 rounded-[5px] border border-blue-500/30 bg-blue-500/10 p-3.5 text-xs text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/40 dark:text-blue-200">
          <div className="flex items-center gap-2.5">
            <Loader2 className="size-4 shrink-0 animate-spin text-blue-600 dark:text-blue-400" />
            <div>
              <span className="font-semibold">
                Discovery prospek sedang berjalan di latar belakang...
              </span>
              <p className="mt-0.5 text-muted-foreground text-[11px]">
                {searchMutation.isPending
                  ? "Sistem sedang scraping Threads & LinkedIn serta evaluasi scoring AI."
                  : "Sistem sedang menganalisis link postingan langsung."}{" "}
                Tabel akan diperbarui secara otomatis ketika proses selesai.
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setIsDiscoveryOpen(true)}
            className="h-7 shrink-0 rounded-[5px] text-xs font-semibold"
          >
            Buka Pop-up
          </Button>
        </div>
      )}

      <section className="w-full min-w-0 max-w-full overflow-hidden rounded-[5px] border bg-card">
        <div className="border-b p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            {/* Sisi Kiri: Search Input & Filter */}
            <div className="flex flex-1 flex-wrap items-center gap-2">
              <label className="relative w-full sm:w-72 md:w-80">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="h-9 pl-9 rounded-[5px]"
                  placeholder="Cari konten, nama, kebutuhan…"
                  value={search}
                  onChange={(event) => setFilter(setSearch)(event.target.value)}
                />
              </label>

              <LeadFiltersPopover
                values={filterValues}
                onChange={(value) => {
                  setFilterValues(value);
                  setPagination((current) => ({ ...current, pageIndex: 0 }));
                }}
                isMarketing={isMarketing}
                sourcePreset={sourcePreset}
              />

              <Button
                type="button"
                variant="outline"
                className="h-9 gap-2 text-xs"
                onClick={() => void leads.refetch()}
                disabled={leads.isRefetching}
                title="Muat ulang data leads"
                aria-label="Muat ulang data leads"
              >
                <RefreshCw
                  className={`size-3.5 ${leads.isRefetching ? "animate-spin" : ""}`}
                />
              </Button>
            </div>

            {/* Sisi Kanan: Button Discovery & Refresh */}
            <div className="flex items-center gap-2 self-end md:self-auto">
              {isMarketing &&
                (sourcePreset === "spse" ? (
                  <Button
                    asChild
                    variant="outline"
                    className="h-9 shrink-0 rounded-[5px] border-[#9D0A0E] text-[#9D0A0E] shadow-none hover:bg-[#9D0A0E]/5 hover:text-[#9D0A0E]"
                  >
                    <Link href="/discovery/spse">
                      <Compass className="size-4" />
                      Discovery
                    </Link>
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDiscoveryOpen(true)}
                    className="h-9 shrink-0 gap-1.5 rounded-[5px] border-[#9D0A0E] text-[#9D0A0E] shadow-none hover:bg-[#9D0A0E]/5 hover:text-[#9D0A0E]"
                  >
                    <Compass className="size-4" />
                    Discovery
                    {(searchMutation.isPending ||
                      analyzeUrlMutation.isPending) && (
                      <span className="relative flex size-2">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#9D0A0E] opacity-75"></span>
                        <span className="relative inline-flex size-2 rounded-full bg-[#9D0A0E]"></span>
                      </span>
                    )}
                  </Button>
                ))}
            </div>
          </div>
        </div>
        <Table>
          <TableHeader className="bg-muted/50">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="px-4 py-3 text-xs uppercase text-muted-foreground"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {leads.isPending ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  Memuat leads…
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  Tidak ada leads untuk filter ini.
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className="align-top">
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="px-4 py-4">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <div className="border-t">
          <DataTablePagination table={table} />
        </div>
      </section>

      <Dialog
        open={selectedLead !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedLead(null);
        }}
      >
        <DialogContent className="max-h-[90vh] w-full max-w-[95vw] sm:max-w-3xl md:max-w-4xl lg:max-w-5xl overflow-hidden p-0 rounded-lg flex flex-col gap-0 shadow-xl border border-border/80">
          {selectedLead && (
            <>
              {/* Header Popup Dialog */}
              <div className="border-b border-border/80 bg-muted/20 px-6 py-4 pr-12 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shrink-0">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center rounded-full border border-[#9D0A0E]/30 bg-[#9D0A0E]/10 px-2.5 py-0.5 text-[11px] font-semibold text-[#9D0A0E] capitalize">
                      {selectedLead.source}
                    </span>
                    {selectedLead.matched_keyword && (
                      <span className="inline-flex items-center gap-1 rounded-full border bg-background px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                        <Tag className="size-3" />
                        {selectedLead.matched_keyword}
                      </span>
                    )}
                  </div>
                  <DialogTitle className="text-xl font-bold tracking-tight text-foreground">
                    {selectedLead.author_name || "Prospek Tanpa Nama"}
                  </DialogTitle>
                  <DialogDescription className="text-xs text-muted-foreground">
                    {selectedLead.created_at
                      ? `Ditemukan pada ${formatDate(selectedLead.created_at)}`
                      : "Detail informasi prospek penjualan"}
                  </DialogDescription>
                </div>
                <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                  {selectedLead.source_url && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-8 gap-1.5 rounded-md border-border/80 text-xs font-medium hover:bg-muted"
                      onClick={() => setSelectedQrLead(selectedLead)}
                    >
                      <QrCode className="size-3.5 text-[#9D0A0E]" />
                      <span>Generate QR</span>
                    </Button>
                  )}
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1.5 rounded-md border-border/80 text-xs font-medium hover:bg-muted"
                  >
                    <a
                      href={selectedLead.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <span>Buka Sumber</span>
                      <ExternalLink className="size-3.5 text-muted-foreground" />
                    </a>
                  </Button>
                </div>
              </div>

              {/* Body Popup Dialog */}
              <div className="flex-1 overflow-y-auto p-5 sm:p-6 min-h-0">
                {selectedLead.quality_flags?.includes(
                  "llm_analysis_failed",
                ) && (
                  <div
                    role="status"
                    className="mb-5 rounded-md border border-amber-500/40 bg-amber-500/10 p-3.5 text-xs text-amber-900 dark:text-amber-200"
                  >
                    Analisis AI belum selesai secara optimal. Periksa konten
                    sumber di bawah ini sebelum mengonfirmasi status valid.
                  </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                  {/* Kolom Kiri: Detail Informasi & Analisis Prospek (7 cols) */}
                  <div className="lg:col-span-7 space-y-5">
                    {/* Metrik Skor & Kategori */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 rounded-lg border border-border/70 bg-muted/20 p-3 text-xs">
                      <div>
                        <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider block">
                          Skor Lead
                        </span>
                        <span className="mt-1 inline-flex items-center font-bold text-sm text-[#9D0A0E]">
                          {selectedLead.quality_flags?.includes(
                            "llm_analysis_failed",
                          )
                            ? "—"
                            : `${selectedLead.lead_score}/100`}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider block">
                          Keyakinan AI
                        </span>
                        <span className="mt-1 inline-flex items-center font-bold text-sm text-foreground">
                          {selectedLead.quality_flags?.includes(
                            "llm_analysis_failed",
                          )
                            ? "—"
                            : `${Math.round(selectedLead.confidence * 100)}%`}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider block">
                          Industri
                        </span>
                        <span className="mt-1 block font-semibold text-foreground truncate capitalize">
                          {selectedLead.industry
                            ? selectedLead.industry.replace(/_/g, " ")
                            : "Umum"}
                        </span>
                      </div>
                      <div>
                        <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider block">
                          Sumber
                        </span>
                        <span className="mt-1 block font-semibold text-foreground truncate capitalize">
                          {selectedLead.source}
                        </span>
                      </div>
                    </div>

                    {/* Pantau Jadwal & Progres Lelang SPSE jika source spse */}
                    {selectedLead.source === "spse" && (
                      <SpseScheduleCard lead={selectedLead} />
                    )}

                    {/* Isi Konten */}
                    <div className="rounded-lg border border-border/80 bg-card p-4 space-y-2 shadow-xs">
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        <FileText className="size-3.5 text-slate-500" />
                        <span>Konten Postingan / Kebutuhan</span>
                      </div>
                      <p className="whitespace-pre-wrap rounded-md bg-muted/30 p-3.5 text-xs font-normal leading-relaxed text-foreground select-text border border-border/50">
                        {selectedLead.content}
                      </p>
                    </div>

                    {/* Kebutuhan (Needs) */}
                    {selectedLead.needs.length > 0 && (
                      <div className="rounded-lg border border-border/80 bg-card p-4 space-y-2 shadow-xs">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          <Target className="size-3.5 text-blue-600 dark:text-blue-400" />
                          <span>Kebutuhan Teridentifikasi</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {selectedLead.needs.map((need) => (
                            <span
                              key={need}
                              className="inline-flex items-center rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-300"
                            >
                              {need}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Kendala (Pain Points) */}
                    {selectedLead.pain_points.length > 0 && (
                      <div className="rounded-lg border border-border/80 bg-card p-4 space-y-2 shadow-xs">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          <AlertCircle className="size-3.5 text-amber-600 dark:text-amber-400" />
                          <span>Kendala / Pain Points</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {selectedLead.pain_points.map((pain) => (
                            <span
                              key={pain}
                              className="inline-flex items-center rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-700 dark:text-amber-300"
                            >
                              {pain}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Rekomendasi Layanan */}
                    {selectedLead.recommended_services.length > 0 && (
                      <div className="rounded-lg border border-border/80 bg-card p-4 space-y-3 shadow-xs">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          <Sparkles className="size-3.5 text-emerald-600 dark:text-emerald-400" />
                          <span>Rekomendasi Layanan & Solusi Fit</span>
                        </div>
                        <div className="space-y-2">
                          {selectedLead.recommended_services.map((service) => (
                            <div
                              key={service.product_id}
                              className="rounded-md border border-border/70 bg-muted/20 p-3"
                            >
                              <div className="flex items-center justify-between gap-3 text-xs font-semibold text-foreground">
                                <span>{service.product_name}</span>
                                <span className="shrink-0 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-bold text-emerald-700 dark:text-emerald-400">
                                  Match {service.match_score}%
                                </span>
                              </div>
                              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                                {service.reason}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Kolom Kanan: Review & Penugasan Sales (5 cols) */}
                  <div className="lg:col-span-5 space-y-4">
                    <LeadWorkflowPanel
                      key={selectedLead.lead_id}
                      lead={selectedLead}
                      isMarketing={isMarketing}
                      onUpdated={setSelectedLead}
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open && !deleteLead.isPending) setPendingDelete(null);
        }}
      >
        <DialogContent className="rounded-[5px] sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Hapus lead?</DialogTitle>
            <DialogDescription>
              Apakah Anda yakin ingin menghapus lead{" "}
              <span className="font-semibold text-foreground">
                {pendingDelete?.author_name || "prospek tanpa nama"}
              </span>{" "}
              ini?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              className="cursor-pointer"
              disabled={deleteLead.isPending}
              onClick={() => setPendingDelete(null)}
            >
              Batal
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="cursor-pointer"
              disabled={!pendingDelete || deleteLead.isPending}
              onClick={() => {
                if (!pendingDelete) return;
                deleteLead.mutate(pendingDelete.lead_id, {
                  onSuccess: () => {
                    setPendingDelete(null);
                    if (data.length === 1 && pagination.pageIndex > 0) {
                      setPagination((current) => ({
                        ...current,
                        pageIndex: current.pageIndex - 1,
                      }));
                    }
                  },
                });
              }}
            >
              {deleteLead.isPending ? "Menghapus…" : "Hapus"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <SpseScheduleDialog
        lead={selectedSpseLead}
        open={Boolean(selectedSpseLead)}
        onOpenChange={(open) => !open && setSelectedSpseLead(null)}
      />
      <SocialMediaDiscoveryDialog
        open={isDiscoveryOpen}
        onOpenChange={setIsDiscoveryOpen}
        searchMutation={searchMutation}
        analyzeUrlMutation={analyzeUrlMutation}
      />
      <LeadQrCodeDialog
        lead={selectedQrLead}
        open={selectedQrLead !== null}
        onOpenChange={(open) => !open && setSelectedQrLead(null)}
      />
    </div>
  );
}

function StatusPill({ value }: { value: string }) {
  return (
    <span className="inline-flex rounded-full bg-muted px-2.5 py-1 text-xs font-medium">
      {value}
    </span>
  );
}
