"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type OnChangeFn,
  type PaginationState,
} from "@tanstack/react-table";
import { Database, ExternalLink, Eye, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
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
import type { SirupPackage } from "@/types/salep";
import { formatCurrency, formatDate } from "@/utils/formatting/string";

interface SirupTableProps {
  data: SirupPackage[];
  total: number;
  pagination: PaginationState;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  onPaginationChange: OnChangeFn<PaginationState>;
  onViewPackage?: (item: SirupPackage) => void;
}

export function SirupTable({
  data,
  total,
  pagination,
  isLoading,
  isError,
  errorMessage,
  onPaginationChange,
  onViewPackage,
}: SirupTableProps) {
  const columns = useMemo<ColumnDef<SirupPackage>[]>(
    () => [
      {
        accessorKey: "package_name",
        header: "Paket / ID RUP",
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="max-w-[280px]">
              <p
                className="cursor-pointer truncate block font-semibold text-left text-slate-900 transition-colors hover:text-[#9D0A0E] hover:underline dark:text-white dark:hover:text-red-400"
                title={item.package_name}
                onClick={() => onViewPackage?.(item)}
              >
                {item.package_name}
              </p>
              <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
                RUP {item.rup_id || item.external_id}
              </p>
            </div>
          );
        },
      },
      {
        accessorKey: "organization",
        header: "Instansi / Satker",
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="max-w-[200px]">
              <p
                className="truncate font-medium text-slate-900 dark:text-white"
                title={item.organization || ""}
              >
                {item.organization || "—"}
              </p>
              <p
                className="truncate text-muted-foreground"
                title={item.satker || item.location || ""}
              >
                {item.satker || item.location || "—"}
              </p>
            </div>
          );
        },
      },
      {
        accessorKey: "fiscal_year",
        header: "Tahun",
        cell: ({ row }) => (
          <Badge variant="outline" className="font-medium">
            {row.original.fiscal_year}
          </Badge>
        ),
      },
      {
        accessorKey: "budget_amount",
        header: () => <div className="text-right">Pagu</div>,
        cell: ({ row }) => {
          const amount = row.original.budget_amount;
          return (
            <div className="text-right font-semibold text-slate-900 dark:text-white">
              {amount == null ? "—" : formatCurrency(amount)}
            </div>
          );
        },
      },
      {
        accessorKey: "procurement_type",
        header: "Jenis & Metode",
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="max-w-[180px]">
              <p className="truncate text-slate-900 dark:text-white">
                {item.procurement_type || "—"}
              </p>
              <p className="truncate text-muted-foreground">
                {item.procurement_method || "—"}
              </p>
            </div>
          );
        },
      },
      {
        accessorKey: "last_seen_at",
        header: "Terakhir Dilihat",
        cell: ({ row }) => {
          const date = row.original.last_seen_at;
          return (
            <span className="whitespace-nowrap text-muted-foreground">
              {date ? formatDate(date) : "—"}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-right">Aksi</div>,
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="flex items-center justify-end gap-1.5 text-right">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 gap-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800"
                onClick={() => onViewPackage?.(item)}
              >
                <Eye className="size-3.5 text-slate-500" />
                Detail
              </Button>
              {/* <Button
                asChild
                variant="ghost"
                size="sm"
                className="h-8 gap-1 px-2 text-xs text-muted-foreground hover:text-[#9D0A0E]"
                title="Buka langsung di SiRUP INAPROC"
              >
                <Link
                  href={item.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="size-3.5" />
                </Link>
              </Button> */}
            </div>
          );
        },
      },
    ],
    [onViewPackage],
  );

  const pageCount = Math.max(1, Math.ceil(total / pagination.pageSize));

  const table = useReactTable({
    data,
    columns,
    pageCount,
    state: {
      pagination,
    },
    manualPagination: true,
    onPaginationChange,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow
                key={headerGroup.id}
                className="bg-muted/40 hover:bg-muted/40"
              >
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="text-[11px] uppercase tracking-wide text-muted-foreground"
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
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="size-4 animate-spin text-[#9D0A0E]" />
                    <span>Memuat data SiRUP...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : isError ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-32 text-center text-destructive"
                >
                  Data gagal dimuat. {errorMessage}
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} className="transition hover:bg-muted/30">
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="py-3 text-xs">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-32 text-center"
                >
                  <Database className="mx-auto size-8 text-muted-foreground/50" />
                  <p className="mt-2 text-sm font-medium">
                    Belum ada data yang cocok
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Jalankan sinkronisasi atau ubah filter pencarian.
                  </p>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <DataTablePagination table={table} />
    </div>
  );
}
