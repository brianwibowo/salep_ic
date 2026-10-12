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
  ChevronDown,
  Compass,
  Eye,
  ExternalLink,
  Search,
  SlidersHorizontal,
  Trash2,
  Calendar,
  Clock,
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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SpseScheduleDialog } from "@/components/leads/spse-schedule-dialog";
import { useSession } from "@/hooks/auth/use-auth";
import {
  useDeleteLead,
  useLeads,
  useUpdateLeadStatus,
  useUpdateSalesStatus,
} from "@/hooks/leads/use-leads";
import { Lead } from "@/types/salep";

const salesStatuses: Lead["sales_status"][] = [
  "Belum Dihubungi",
  "Sedang Dihubungi",
  "Closing",
  "Batal",
];

export function LeadsPageContent({
  sourcePreset = "all",
}: {
  sourcePreset?: "all" | "social_media" | "spse";
}) {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const [selectedSpseLead, setSelectedSpseLead] = useState<Lead | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [source, setSource] = useState<string>(sourcePreset);
  const [salesStatus, setSalesStatus] = useState("all");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Lead | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 50,
  });
  const page = pagination.pageIndex + 1;
  const filters = {
    search,
    status: isMarketing ? status : "all",
    source,
    sales_status: salesStatus,
    page,
    limit: pagination.pageSize,
  };
  const leads = useLeads(filters);
  const updateMarketing = useUpdateLeadStatus();
  const updateSales = useUpdateSalesStatus();
  const deleteLead = useDeleteLead();

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
        accessorKey: "lead_score",
        header: "Skor",
        cell: ({ row }) => (
          <span className="rounded-full bg-primary/10 px-2.5 py-1 font-semibold text-primary">
            {row.original.lead_score}
          </span>
        ),
      },
      {
        accessorKey: "marketing_status",
        header: "Status",
        cell: ({ row }) => {
          const lead = row.original;
          return isMarketing && sourcePreset === "all" ? (
            <select
              aria-label={`Status marketing ${lead.author_name || lead.lead_id}`}
              className="h-9 rounded-md border bg-background px-2"
              value={lead.marketing_status}
              disabled={updateMarketing.isPending}
              onChange={(event) =>
                updateMarketing.mutate({
                  leadId: lead.lead_id,
                  status: event.target.value as Lead["marketing_status"],
                })
              }
            >
              <option value="pending">Menunggu review</option>
              <option value="valid">Valid</option>
              <option value="invalid">Tidak valid</option>
            </select>
          ) : (
            <StatusPill value={lead.marketing_status} />
          );
        },
      },
      {
        accessorKey: "sales_status",
        header: "Tindak lanjut",
        cell: ({ row }) => {
          const lead = row.original;
          return isMarketing || sourcePreset !== "all" ? (
            <StatusPill value={lead.sales_status} />
          ) : (
            <select
              aria-label={`Status tindak lanjut ${lead.author_name || lead.lead_id}`}
              className="h-9 rounded-md border bg-background px-2"
              value={lead.sales_status}
              disabled={updateSales.isPending}
              onChange={(event) =>
                updateSales.mutate({
                  leadId: lead.lead_id,
                  status: event.target.value as Lead["sales_status"],
                })
              }
            >
              {salesStatuses.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          );
        },
      },
      {
        id: "post",
        header: "Tautan & Jadwal",
        cell: ({ row }) => {
          const lead = row.original;
          const isSpse = lead.source === "spse";
          return (
            <div className="flex flex-col gap-1.5 whitespace-nowrap">
              <a
                className="inline-flex items-center gap-1 text-primary hover:underline"
                href={lead.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {isSpse ? "Pengumuman" : "Buka"}{" "}
                <ExternalLink className="size-3.5" />
              </a>
              {isSpse && (
                <button
                  type="button"
                  onClick={() => setSelectedSpseLead(lead)}
                  className="inline-flex cursor-pointer items-center gap-1 text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  <Clock className="size-3" /> Jadwal Lelang
                </button>
              )}
            </div>
          );
        },
      },
      {
        id: "actions",
        header: "Aksi",
        cell: ({ row }) => {
          const lead = row.original;
          return (
            <div className="flex items-center gap-1 whitespace-nowrap">
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label="Lihat detail lead"
                title="Detail"
                className="text-slate-700 hover:text-slate-950"
                onClick={() => setSelectedLead(lead)}
              >
                <Eye className="size-4" />
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
    [isMarketing, updateMarketing, updateSales],
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
    <div className="space-y-5">
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

      <section className="overflow-hidden rounded-[5px] border bg-card">
        <div className="border-b p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant="outline"
                    className="h-9 rounded-[5px] shadow-none"
                  >
                    <SlidersHorizontal className="size-4" />
                    Filter
                    <ChevronDown className="size-4 text-muted-foreground" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  align="start"
                  className="w-72 space-y-4 rounded-[5px]"
                >
                  {isMarketing && (
                    <label className="block space-y-1.5 text-sm font-medium">
                      Status validasi
                      <select
                        className="h-9 w-full rounded-[5px] border bg-background px-3 font-normal"
                        value={status}
                        onChange={(event) =>
                          setFilter(setStatus)(event.target.value)
                        }
                      >
                        <option value="all">Semua status marketing</option>
                        <option value="pending">Menunggu review</option>
                        <option value="valid">Valid</option>
                        <option value="invalid">Tidak valid</option>
                      </select>
                    </label>
                  )}
                  {sourcePreset !== "spse" && (
                    <label className="block space-y-1.5 text-sm font-medium">
                      Sumber
                      <select
                        className="h-9 w-full rounded-[5px] border bg-background px-3 font-normal"
                        value={source}
                        onChange={(event) =>
                          setFilter(setSource)(event.target.value)
                        }
                      >
                        {sourcePreset === "social_media" ? (
                          <>
                            <option value="social_media">
                              Semua sosial media
                            </option>
                            <option value="threads">Threads</option>
                            <option value="linkedin">LinkedIn</option>
                          </>
                        ) : (
                          <>
                            <option value="all">Semua sumber</option>
                            <option value="social_media">Sosial Media</option>
                            <option value="threads">Threads</option>
                            <option value="linkedin">LinkedIn</option>
                            <option value="spse">SPSE</option>
                            <option value="mock">Mock</option>
                          </>
                        )}
                      </select>
                    </label>
                  )}
                  {!isMarketing && (
                    <label className="block space-y-1.5 text-sm font-medium">
                      Status tindak lanjut
                      <select
                        className="h-9 w-full rounded-[5px] border bg-background px-3 font-normal"
                        value={salesStatus}
                        onChange={(event) =>
                          setFilter(setSalesStatus)(event.target.value)
                        }
                      >
                        <option value="all">Semua tindak lanjut</option>
                        {salesStatuses.map((item) => (
                          <option key={item}>{item}</option>
                        ))}
                      </select>
                    </label>
                  )}
                </PopoverContent>
              </Popover>
              {(sourcePreset === "spse" || sourcePreset === "social_media") &&
                isMarketing && (
                  <Button
                    asChild
                    variant="outline"
                    className="h-9 shrink-0 rounded-[5px] border-[#9D0A0E] text-[#9D0A0E] shadow-none hover:bg-[#9D0A0E]/5 hover:text-[#9D0A0E]"
                  >
                    <Link
                      href={
                        sourcePreset === "spse"
                          ? "/discovery/spse"
                          : "/discovery"
                      }
                    >
                      <Compass className="size-4" />
                      Discovery
                    </Link>
                  </Button>
                )}
            </div>
            <label className="relative w-full md:max-w-sm md:flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Cari konten, nama, kebutuhan…"
                value={search}
                onChange={(event) => setFilter(setSearch)(event.target.value)}
              />
            </label>
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
        <DialogContent className="max-h-[85vh] overflow-y-auto rounded-[5px] sm:max-w-2xl">
          {selectedLead && (
            <>
              <DialogHeader>
                <DialogTitle>Detail Lead</DialogTitle>
                <DialogDescription>
                  {selectedLead.author_name || "Prospek tanpa nama"} ·{" "}
                  {selectedLead.source}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-5">
                <dl className="grid gap-4 rounded-[5px] border p-4 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-muted-foreground">Skor lead</dt>
                    <dd className="mt-1 font-semibold">
                      {selectedLead.lead_score}/100
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Keyakinan analisis
                    </dt>
                    <dd className="mt-1 font-semibold">
                      {Math.round(selectedLead.confidence * 100)}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Status marketing
                    </dt>
                    <dd className="mt-1 font-medium capitalize">
                      {selectedLead.marketing_status}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Tindak lanjut
                    </dt>
                    <dd className="mt-1 font-medium">
                      {selectedLead.sales_status}
                    </dd>
                  </div>
                  {selectedLead.industry && (
                    <div>
                      <dt className="text-xs text-muted-foreground">
                        Industri
                      </dt>
                      <dd className="mt-1 font-medium">
                        {selectedLead.industry.replace(/_/g, " ")}
                      </dd>
                    </div>
                  )}
                  {selectedLead.matched_keyword && (
                    <div>
                      <dt className="text-xs text-muted-foreground">Keyword</dt>
                      <dd className="mt-1 font-medium">
                        {selectedLead.matched_keyword}
                      </dd>
                    </div>
                  )}
                </dl>
                {sourcePreset !== "all" && (
                  <label className="block max-w-sm space-y-2 text-sm font-medium">
                    {isMarketing
                      ? "Ubah status marketing"
                      : "Ubah status tindak lanjut"}
                    {isMarketing ? (
                      <select
                        className="h-10 w-full rounded-[5px] border bg-background px-3"
                        value={selectedLead.marketing_status}
                        disabled={updateMarketing.isPending}
                        onChange={(event) =>
                          updateMarketing.mutate(
                            {
                              leadId: selectedLead.lead_id,
                              status: event.target
                                .value as Lead["marketing_status"],
                            },
                            { onSuccess: setSelectedLead },
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
                        value={selectedLead.sales_status}
                        disabled={updateSales.isPending}
                        onChange={(event) =>
                          updateSales.mutate(
                            {
                              leadId: selectedLead.lead_id,
                              status: event.target
                                .value as Lead["sales_status"],
                            },
                            { onSuccess: setSelectedLead },
                          )
                        }
                      >
                        {salesStatuses.map((item) => (
                          <option key={item}>{item}</option>
                        ))}
                      </select>
                    )}
                  </label>
                )}
                <div>
                  <h3 className="mb-2 text-sm font-semibold">Konten</h3>
                  <p className="whitespace-pre-wrap rounded-[5px] bg-muted/50 p-4 text-sm leading-6">
                    {selectedLead.content}
                  </p>
                </div>
                {selectedLead.needs.length > 0 && (
                  <div>
                    <h3 className="mb-2 text-sm font-semibold">Kebutuhan</h3>
                    <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                      {selectedLead.needs.map((need) => (
                        <li key={need}>{need}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {selectedLead.pain_points.length > 0 && (
                  <div>
                    <h3 className="mb-2 text-sm font-semibold">Kendala</h3>
                    <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                      {selectedLead.pain_points.map((pain) => (
                        <li key={pain}>{pain}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {selectedLead.recommended_services.length > 0 && (
                  <div>
                    <h3 className="mb-2 text-sm font-semibold">
                      Rekomendasi layanan
                    </h3>
                    <div className="space-y-2">
                      {selectedLead.recommended_services.map((service) => (
                        <div
                          key={service.product_id}
                          className="rounded-[5px] border p-3"
                        >
                          <div className="flex items-center justify-between gap-3 text-sm font-medium">
                            <span>{service.product_name}</span>
                            <span className="shrink-0 text-primary">
                              {service.match_score}%
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {service.reason}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <a
                  href={selectedLead.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
                >
                  Buka posting sumber <ExternalLink className="size-4" />
                </a>
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
              Lead dari {pendingDelete?.author_name || "prospek tanpa nama"}{" "}
              akan dihapus permanen dari database SALEP.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              disabled={deleteLead.isPending}
              onClick={() => setPendingDelete(null)}
            >
              Batal
            </Button>
            <Button
              type="button"
              variant="destructive"
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
              {deleteLead.isPending ? "Menghapus…" : "Hapus lead"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <SpseScheduleDialog
        lead={selectedSpseLead}
        open={Boolean(selectedSpseLead)}
        onOpenChange={(open) => !open && setSelectedSpseLead(null)}
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

export default function LeadsPage() {
  return <LeadsPageContent />;
}
