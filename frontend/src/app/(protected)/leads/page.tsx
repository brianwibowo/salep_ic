"use client";

import { useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type PaginationState,
} from "@tanstack/react-table";
import { ExternalLink, Search } from "lucide-react";
import { DataTablePagination } from "@/components/ui/data-table-pagination";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSession } from "@/hooks/auth/use-auth";
import {
  useLeads,
  useUpdateLeadStatus,
  useUpdateSalesStatus,
} from "@/hooks/leads/use-leads";
import { Lead } from "@/types/salep";

const PAGE_SIZE = 50;
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
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [source, setSource] = useState<string>(sourcePreset);
  const [salesStatus, setSalesStatus] = useState("all");
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: PAGE_SIZE,
  });

  const leads = useLeads({
    search,
    status: isMarketing ? status : "all",
    source,
    sales_status: salesStatus,
    offset: pagination.pageIndex * pagination.pageSize,
    limit: pagination.pageSize,
  });
  const updateMarketing = useUpdateLeadStatus();
  const updateSales = useUpdateSalesStatus();

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
          return (
            <div className="max-w-xl whitespace-normal">
              <p className="font-medium">{lead.author_name || "Prospek tanpa nama"}</p>
              <p className="mt-1 line-clamp-2 text-muted-foreground">{lead.content}</p>
              {lead.needs?.length > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Kebutuhan: {lead.needs.join(", ")}
                </p>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: "source",
        header: "Sumber",
        cell: ({ row }) => <span className="capitalize">{row.original.source}</span>,
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
          return isMarketing ? (
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
          return isMarketing ? (
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
        header: "Posting",
        cell: ({ row }) => (
          <a
            className="inline-flex items-center gap-1 text-primary hover:underline"
            href={row.original.source_url}
            target="_blank"
            rel="noreferrer"
          >
            Buka <ExternalLink className="size-3.5" />
          </a>
        ),
      },
    ],
    [isMarketing, updateMarketing, updateSales],
  );

  const data = leads.data ?? [];
  const pageCount =
    data.length < pagination.pageSize
      ? pagination.pageIndex + 1
      : pagination.pageIndex + 2;
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

      <section className="rounded-[5px] border bg-card p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <label className="relative md:col-span-2">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Cari konten, nama, kebutuhan…"
              value={search}
              onChange={(event) => setFilter(setSearch)(event.target.value)}
            />
          </label>
          {isMarketing && (
            <label className="text-sm">
              <span className="sr-only">Status validasi</span>
              <select
                className="h-9 w-full rounded-md border bg-background px-3"
                value={status}
                onChange={(event) => setFilter(setStatus)(event.target.value)}
              >
                <option value="all">Semua status marketing</option>
                <option value="pending">Menunggu review</option>
                <option value="valid">Valid</option>
                <option value="invalid">Tidak valid</option>
              </select>
            </label>
          )}
          <label className="text-sm">
            <span className="sr-only">Sumber</span>
            <select
              className="h-9 w-full rounded-md border bg-background px-3"
              value={source}
              onChange={(event) => setFilter(setSource)(event.target.value)}
            >
              <option value="all">Semua sumber</option>
              <option value="social_media">Sosial Media</option>
              <option value="threads">Threads</option>
              <option value="linkedin">LinkedIn</option>
              <option value="spse">SPSE</option>
              <option value="mock">Mock</option>
            </select>
          </label>
          {!isMarketing && (
            <label className="text-sm md:col-start-4">
              <span className="sr-only">Status tindak lanjut</span>
              <select
                className="h-9 w-full rounded-md border bg-background px-3"
                value={salesStatus}
                onChange={(event) => setFilter(setSalesStatus)(event.target.value)}
              >
                <option value="all">Semua tindak lanjut</option>
                {salesStatuses.map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </section>

      {leads.isError && (
        <p
          role="alert"
          className="rounded-[5px] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
        >
          {leads.error.message}
        </p>
      )}

      <section className="overflow-hidden rounded-[5px] border bg-card">
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
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {leads.isPending ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  Memuat leads…
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  Tidak ada leads untuk filter ini.
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
          <DataTablePagination table={table} pageCountUnknown />
        </div>
      </section>
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
