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

export function SpseLeadsPageContent() {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [salesStatus, setSalesStatus] = useState("all");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedScheduleLead, setSelectedScheduleLead] = useState<Lead | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Lead | null>(null);
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
      <div>
        <h1 className="text-2xl font-semibold">Leads SPSE</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {isMarketing
            ? "Tinjau dan validasi prospek pengadaan dari SPSE."
            : "Kelola tindak lanjut untuk prospek pengadaan yang sudah valid."}
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
    </div>
  );
}
