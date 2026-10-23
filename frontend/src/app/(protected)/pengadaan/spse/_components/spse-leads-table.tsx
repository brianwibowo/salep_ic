"use client";

import { useMemo } from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type OnChangeFn,
  type PaginationState,
} from "@tanstack/react-table";
import {
  Building2,
  Calendar,
  Clock,
  Coins,
  ExternalLink,
  Eye,
  FileText,
  Loader2,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DataTablePagination } from "@/components/ui/data-table-pagination";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { parseSpseLeadContent } from "@/lib/spse-parser";
import type { Lead } from "@/types/salep";
import { formatDate } from "@/utils/formatting/string";
import { SalesProgressCell } from "@/components/leads/lead-sales-progress";

interface SpseLeadsTableProps {
  data: Lead[];
  total: number;
  pagination: PaginationState;
  isLoading: boolean;
  isMarketing: boolean;
  onPaginationChange: OnChangeFn<PaginationState>;
  onViewLead: (lead: Lead) => void;
  onViewSchedule: (lead: Lead) => void;
  onDeleteLead: (lead: Lead) => void;

}

export function SpseLeadsTable({
  data,
  total,
  pagination,
  isLoading,
  isMarketing,
  onPaginationChange,
  onViewLead,
  onViewSchedule,
  onDeleteLead,
}: SpseLeadsTableProps) {
  const columns = useMemo<ColumnDef<Lead>[]>(
    () => [
      {
        accessorKey: "author_name",
        header: "Paket Pengadaan",
        cell: ({ row }) => {
          const lead = row.original;
          const parsed = parseSpseLeadContent(lead.content, lead.author_name);

          return (
            <div className="flex max-w-xl flex-col gap-1.5 py-0.5">
              {/* Institution / Agency */}
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Building2 className="size-3.5 shrink-0 text-slate-400 dark:text-slate-500" />
                <span className="truncate font-medium text-slate-600 dark:text-slate-300">
                  {parsed.agency || lead.author_name || "Instansi Pemerintah"}
                </span>
              </div>

              {/* Package Title + Status Badge */}
              <div className="flex flex-wrap items-baseline gap-2">
                <h4 className="text-sm font-semibold leading-snug text-slate-900 dark:text-slate-100">
                  {parsed.title}
                </h4>
                {parsed.badge && (
                  <span
                    className={`inline-flex items-center rounded-[4px] px-2 py-0.5 text-[11px] font-semibold leading-none shadow-xs ${
                      parsed.badge.variant === "destructive"
                        ? "border border-rose-200/80 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300"
                        : parsed.badge.variant === "warning"
                          ? "border border-amber-200/80 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                          : "border border-blue-200/80 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
                    }`}
                  >
                    {parsed.badge.text}
                  </span>
                )}
              </div>

              {/* Metadata: Stage, HPS, and Need tags */}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 pt-0.5 text-xs text-muted-foreground">
                {parsed.stage && (
                  <div className="inline-flex items-center gap-1 text-slate-600 dark:text-slate-300">
                    <Clock className="size-3 text-slate-400" />
                    <span>Tahap:</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">
                      {parsed.stage}
                    </span>
                  </div>
                )}

                {parsed.hps && parsed.hps !== "Rp 0" && parsed.hps !== "Rp 0,00" && (
                  <div className="inline-flex items-center gap-1 text-slate-600 dark:text-slate-300">
                    <Coins className="size-3 text-slate-400" />
                    <span>HPS:</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">
                      {parsed.hps}
                    </span>
                  </div>
                )}

                {lead.needs && lead.needs.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1">
                    {lead.needs.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center rounded-[4px] bg-[#9D0A0E]/8 px-2 py-0.5 text-[11px] font-medium text-[#9D0A0E] dark:bg-[#9D0A0E]/20 dark:text-red-300"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "marketing_status",
        header: "Status",
        cell: ({ row }) => {
          const lead = row.original;
          return <MarketingStatusBadge value={lead.marketing_status} />;
        },
      },
      {
        id: "assigned-sales",
        header: "Sales PIC",
        cell: ({ row }) => <span className="text-xs">{row.original.assignment?.sales_username || "Belum ditugaskan"}</span>,
      },
      {
        accessorKey: "created_at",
        header: "Dibuat",
        cell: ({ row }) =>
          row.original.created_at ? formatDate(row.original.created_at) : "—",
      },
      {
        accessorKey: "sales_status",
        header: "Tindak Lanjut",
        cell: ({ row }) => {
          const lead = row.original;
          return <SalesProgressCell lead={lead} />;
        },
      },
      {
        id: "links",
        header: "Tautan & Jadwal",
        cell: ({ row }) => {
          const lead = row.original;
          return (
            <div className="flex flex-col gap-1.5 whitespace-nowrap">
              <a
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#9D0A0E] hover:text-[#7A080B] hover:underline dark:text-red-400"
                href={lead.source_url}
                target="_blank"
                rel="noreferrer"
              >
                Pengumuman <ExternalLink className="size-3.5" />
              </a>
              <button
                type="button"
                onClick={() => onViewSchedule(lead)}
                className="inline-flex cursor-pointer items-center gap-1.5 text-left text-xs font-medium text-slate-600 hover:text-slate-900 hover:underline dark:text-slate-400 dark:hover:text-slate-200"
              >
                <Calendar className="size-3.5 text-slate-400" /> Pantau jadwal lelang
              </button>
            </div>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-right">Aksi</div>,
        cell: ({ row }) => {
          const lead = row.original;
          return (
            <div className="flex items-center justify-end gap-1 whitespace-nowrap">
              <Button
                type="button"
                variant={isMarketing ? "outline" : "ghost"}
                size={isMarketing ? "sm" : "icon-sm"}
                aria-label={`Lihat detail ${lead.author_name || lead.lead_id}`}
                title="Detail Paket"
                className="rounded-[5px] text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                onClick={() => onViewLead(lead)}
              >
                <Eye className="size-4" />
                {isMarketing && <span>Review & assign</span>}
              </Button>
              {isMarketing && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Hapus ${lead.author_name || lead.lead_id}`}
                  title="Hapus Paket"
                  className="rounded-[5px] text-slate-400 hover:bg-destructive/10 hover:text-destructive dark:hover:bg-destructive/20"
                  onClick={() => onDeleteLead(lead)}
                >
                  <Trash2 className="size-4" />
                </Button>
              )}
            </div>
          );
        },
      },
    ],
    [
      isMarketing,
      onDeleteLead,
      onViewLead,
      onViewSchedule,
    ],
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: Math.max(1, Math.ceil(total / pagination.pageSize)),
    onPaginationChange,
    state: { pagination },
  });

  return (
    <>
      <div className="w-full min-w-0 max-w-full">
        <Table>
          <TableHeader className="bg-muted/40">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
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
            {isLoading ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-32 text-center text-muted-foreground"
                >
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="size-5 animate-spin text-[#9D0A0E]" />
                    <span className="text-sm">Memuat paket SPSE…</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-32 text-center text-muted-foreground"
                >
                  <div className="flex flex-col items-center justify-center gap-1.5 py-6">
                    <FileText className="size-8 text-slate-300 dark:text-slate-600" />
                    <p className="font-medium text-slate-700 dark:text-slate-300">
                      Tidak ada paket SPSE
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Coba sesuaikan kata kunci pencarian atau filter status.
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className="align-top transition-colors hover:bg-muted/30"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="px-4 py-3.5">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <div className="border-t">
        <DataTablePagination table={table} />
      </div>
    </>
  );
}

function MarketingStatusBadge({ value }: { value: string }) {
  if (value === "valid") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-[5px] border border-emerald-200/80 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
        <span className="size-1.5 rounded-full bg-emerald-500" />
        Valid
      </span>
    );
  }

  if (value === "invalid") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-[5px] border border-slate-200 bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">
        <span className="size-1.5 rounded-full bg-slate-400" />
        Tidak Valid
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-[5px] border border-amber-200/80 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
      <span className="size-1.5 rounded-full bg-amber-500" />
      Review
    </span>
  );
}
