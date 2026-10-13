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
import { Calendar, Clock, ExternalLink, Eye, Trash2 } from "lucide-react";
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
import type { Lead } from "@/types/salep";

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
        header: "Paket pengadaan",
        cell: ({ row }) => {
          const lead = row.original;
          return (
            <div className="max-w-xl whitespace-normal">
              <p className="font-medium">
                {lead.author_name || "Paket tanpa nama"}
              </p>
              <p className="mt-1 line-clamp-2 text-muted-foreground">
                {lead.content}
              </p>
              {lead.needs.length > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Kebutuhan: {lead.needs.join(", ")}
                </p>
              )}
            </div>
          );
        },
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
        cell: ({ row }) => <StatusPill value={row.original.marketing_status} />,
      },
      {
        accessorKey: "sales_status",
        header: "Tindak lanjut",
        cell: ({ row }) => <StatusPill value={row.original.sales_status} />,
      },
      {
        id: "links",
        header: "Tautan & jadwal",
        cell: ({ row }) => {
          const lead = row.original;
          return (
            <div className="flex flex-col gap-1.5 whitespace-nowrap">
              <a
                className="inline-flex items-center gap-1 text-primary hover:underline"
                href={lead.source_url}
                target="_blank"
                rel="noreferrer"
              >
                Pengumuman <ExternalLink className="size-3.5" />
              </a>
              <button
                type="button"
                onClick={() => onViewSchedule(lead)}
                className="inline-flex cursor-pointer items-center gap-1 text-left text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                <Calendar className="size-3" /> Pantau jadwal lelang
              </button>
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
                aria-label={`Lihat detail ${lead.author_name || lead.lead_id}`}
                title="Detail"
                className="text-slate-700 hover:text-slate-950"
                onClick={() => onViewLead(lead)}
              >
                <Eye className="size-4" />
              </Button>
              {/* <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label={`Lihat jadwal ${lead.author_name || lead.lead_id}`}
                title="Jadwal lelang"
                onClick={() => onViewSchedule(lead)}
              >
                <Clock className="size-4" />
              </Button> */}
              {isMarketing && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Hapus ${lead.author_name || lead.lead_id}`}
                  title="Hapus"
                  className="text-destructive hover:bg-destructive/10 hover:text-destructive"
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
    [isMarketing, onDeleteLead, onViewLead, onViewSchedule],
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
          {isLoading ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="h-24 text-center text-muted-foreground"
              >
                Memuat paket SPSE…
              </TableCell>
            </TableRow>
          ) : data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="h-24 text-center text-muted-foreground"
              >
                Tidak ada paket SPSE untuk filter ini.
              </TableCell>
            </TableRow>
          ) : (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} className="align-top">
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="px-4 py-4">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
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
    </>
  );
}

function StatusPill({ value }: { value: string }) {
  return (
    <span className="inline-flex rounded-full bg-muted px-2.5 py-1 text-xs font-medium">
      {value}
    </span>
  );
}
