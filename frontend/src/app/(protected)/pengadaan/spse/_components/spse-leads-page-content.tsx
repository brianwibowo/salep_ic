"use client";

import { useCallback, useMemo, useState } from "react";
import type { PaginationState } from "@tanstack/react-table";
import { SpseScheduleDialog } from "@/components/leads/spse-schedule-dialog";
import { useSession } from "@/hooks/auth/use-auth";
import {
  useDeleteLead,
  useLeads,
  useUpdateLeadStatus,
  useUpdateSalesStatus,
} from "@/hooks/leads/use-leads";
import { useDebounce } from "@/hooks/use-debounce";
import type { LeadFilters } from "@/services/salep-leads-service";
import type { Lead } from "@/types/salep";
import { SpseLeadDeleteDialog } from "./spse-lead-delete-dialog";
import { SpseLeadDetailsDialog } from "./spse-lead-details-dialog";
import { SpseLeadsTable } from "./spse-leads-table";
import { SpseLeadsToolbar } from "./spse-leads-toolbar";
import { SpseSyncDialog } from "./spse-sync-dialog";

export function SpseLeadsPageContent() {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [salesStatus, setSalesStatus] = useState("all");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedScheduleLead, setSelectedScheduleLead] = useState<Lead | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Lead | null>(null);
  const [isSyncOpen, setIsSyncOpen] = useState(false);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 50,
  });
  const debouncedSearch = useDebounce(search, 300);

  const filters = useMemo<LeadFilters>(
    () => ({
      source: "spse",
      search: debouncedSearch,
      status: isMarketing ? status : "all",
      sales_status: isMarketing ? "all" : salesStatus,
      page: pagination.pageIndex + 1,
      limit: pagination.pageSize,
    }),
    [debouncedSearch, isMarketing, pagination.pageIndex, pagination.pageSize, salesStatus, status],
  );
  const leads = useLeads(filters);
  const updateMarketing = useUpdateLeadStatus();
  const updateSales = useUpdateSalesStatus();
  const deleteLead = useDeleteLead();

  const resetPage = useCallback(() => {
    setPagination((current) => ({ ...current, pageIndex: 0 }));
  }, []);

  const handleSearchChange = useCallback(
    (value: string) => {
      setSearch(value);
      resetPage();
    },
    [resetPage],
  );

  const handleStatusChange = useCallback(
    (value: string) => {
      setStatus(value);
      resetPage();
    },
    [resetPage],
  );

  const handleSalesStatusChange = useCallback(
    (value: string) => {
      setSalesStatus(value);
      resetPage();
    },
    [resetPage],
  );

  const handleMarketingStatusUpdate = useCallback(
    (leadId: string, status: Lead["marketing_status"]) => {
      updateMarketing.mutate(
        { leadId, status },
        {
          onSuccess: (updatedLead) => {
            setSelectedLead((current) =>
              current?.lead_id === updatedLead.lead_id ? updatedLead : current,
            );
          },
        },
      );
    },
    [updateMarketing],
  );

  const handleSalesStatusUpdate = useCallback(
    (leadId: string, status: Lead["sales_status"]) => {
      updateSales.mutate(
        { leadId, status },
        {
          onSuccess: (updatedLead) => {
            setSelectedLead((current) =>
              current?.lead_id === updatedLead.lead_id ? updatedLead : current,
            );
          },
        },
      );
    },
    [updateSales],
  );

  const data = leads.data?.items ?? [];
  const total = leads.data?.pagination.total ?? 0;

  const handleDelete = useCallback(() => {
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
  }, [data.length, deleteLead, pagination.pageIndex, pendingDelete]);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span>INAPROC</span>
            <span>•</span>
            <span className="text-[#9D0A0E]">Sistem Pengadaan Secara Elektronik</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Leads SPSE — Prospek Pengadaan
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {isMarketing
              ? "Tinjau dan validasi prospek tender/lelang dari SPSE Nasional untuk identifikasi peluang IT."
              : "Kelola tindak lanjut penjualan untuk prospek pengadaan SPSE yang telah tervalidasi."}
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-2 rounded-[5px] border bg-card px-3 py-1.5 text-xs shadow-xs">
            <span className="text-muted-foreground">Total Paket:</span>
            <span className="font-semibold text-foreground">
              {total.toLocaleString("id-ID")}
            </span>
          </div>
        </div>
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
        <SpseLeadsToolbar
          isMarketing={isMarketing}
          search={search}
          status={status}
          salesStatus={salesStatus}
          isRefreshing={leads.isRefetching}
          onSearchChange={handleSearchChange}
          onStatusChange={handleStatusChange}
          onSalesStatusChange={handleSalesStatusChange}
          onRefresh={() => void leads.refetch()}
          onOpenSync={() => setIsSyncOpen(true)}
        />
        <SpseLeadsTable
          data={data}
          total={total}
          pagination={pagination}
          isLoading={leads.isPending}
          isMarketing={isMarketing}
          onPaginationChange={setPagination}
          onViewLead={setSelectedLead}
          onViewSchedule={setSelectedScheduleLead}
          onDeleteLead={setPendingDelete}
          onMarketingStatusChange={handleMarketingStatusUpdate}
          onSalesStatusChange={handleSalesStatusUpdate}
          isUpdatingMarketing={updateMarketing.isPending}
          isUpdatingSales={updateSales.isPending}
        />
      </section>

      <SpseLeadDetailsDialog
        lead={selectedLead}
        isMarketing={isMarketing}
        isUpdatingMarketing={updateMarketing.isPending}
        isUpdatingSales={updateSales.isPending}
        onOpenChange={(open) => !open && setSelectedLead(null)}
        onMarketingStatusChange={(status) => {
          if (selectedLead) {
            handleMarketingStatusUpdate(selectedLead.lead_id, status);
          }
        }}
        onSalesStatusChange={(status) => {
          if (selectedLead) {
            handleSalesStatusUpdate(selectedLead.lead_id, status);
          }
        }}
      />

      <SpseLeadDeleteDialog
        lead={pendingDelete}
        isDeleting={deleteLead.isPending}
        onOpenChange={(open) => {
          if (!open && !deleteLead.isPending) setPendingDelete(null);
        }}
        onConfirm={handleDelete}
      />

      <SpseScheduleDialog
        lead={selectedScheduleLead}
        open={selectedScheduleLead !== null}
        onOpenChange={(open) => !open && setSelectedScheduleLead(null)}
      />

      <SpseSyncDialog
        open={isSyncOpen}
        onOpenChange={setIsSyncOpen}
        onSuccess={() => void leads.refetch()}
      />
    </div>
  );
}
