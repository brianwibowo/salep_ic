"use client";

import { useState } from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useAssignableSales } from "@/hooks/leads/use-leads";
import { createLeadFilters, leadFilterError, type LeadFilterValues, type LeadSourcePreset } from "@/lib/lead-filters";

const selectClass = "h-9 w-full rounded-md border bg-background px-2.5 text-sm font-normal";
const salesStatuses = ["Belum Dihubungi", "Sedang Dihubungi", "Closing", "Batal"];

/** Draft filters are applied together, avoiding invalid intermediate date ranges. */
export function LeadFiltersPopover({ values, onChange, isMarketing, sourcePreset = "all" }: {
  values: LeadFilterValues; onChange: (value: LeadFilterValues) => void;
  isMarketing: boolean; sourcePreset?: LeadSourcePreset;
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(values);
  const sales = useAssignableSales(isMarketing && open, true);
  const error = leadFilterError(draft);
  const timeActive = values.dateMode === "range" ? !!(values.dateFrom || values.dateTo) : values.dateMode === "month" ? !!values.month : !!values.year;
  const count = [isMarketing && values.status !== "all", values.source !== sourcePreset,
    values.salesStatus !== "all", isMarketing && values.assignment !== "all", timeActive].filter(Boolean).length;
  const change = <K extends keyof LeadFilterValues>(key: K, value: LeadFilterValues[K]) => setDraft((current) => ({...current, [key]: value}));

  return <Popover open={open} onOpenChange={(next) => { if (next) setDraft(values); setOpen(next); }}>
    <PopoverTrigger asChild>
      <Button type="button" variant="outline" className="h-9 gap-2 rounded-md text-xs" aria-label={count ? `Filter, ${count} aktif` : "Filter"}>
        <SlidersHorizontal className="size-3.5" />Filter
        {count > 0 && <span className="rounded bg-muted px-1.5 text-xs tabular-nums">{count}</span>}
        <ChevronDown className="size-3.5 text-muted-foreground" />
      </Button>
    </PopoverTrigger>
    <PopoverContent align="start" className="max-h-[min(80vh,var(--radix-popover-content-available-height))] w-[min(26rem,calc(100vw-2rem))] overflow-y-auto rounded-md p-4">
      <h3 className="text-sm font-semibold">Filter lead</h3>
      <p className="mb-4 mt-1 text-xs text-muted-foreground">Gabungkan filter untuk mempersempit hasil.</p>
      <div className="grid gap-4 min-[480px]:grid-cols-2">
        {isMarketing && <label className="space-y-1.5 text-xs font-medium"><span className="block">Status validasi</span>
          <select className={selectClass} value={draft.status} disabled={draft.assignment === "unassigned"} onChange={(event) => change("status", event.target.value)}>
            <option value="all">Semua status</option><option value="pending">Menunggu review</option><option value="valid">Valid</option><option value="invalid">Tidak valid</option>
          </select>
        </label>}
        <label className="space-y-1.5 text-xs font-medium"><span className="block">Sumber</span>
          <select className={selectClass} disabled={sourcePreset === "spse"} value={draft.source} onChange={(event) => change("source", event.target.value)}>
            {sourcePreset === "spse" ? <option value="spse">SPSE</option> : <>
              {sourcePreset === "all" && <option value="all">Semua sumber</option>}
              <option value="social_media">Semua sosial media</option><option value="threads">Threads</option><option value="linkedin">LinkedIn</option>
              {sourcePreset === "all" && <option value="spse">SPSE</option>}
            </>}
          </select>
        </label>
        <label className="space-y-1.5 text-xs font-medium"><span className="block">Progress Sales</span>
          <select className={selectClass} value={draft.salesStatus} onChange={(event) => change("salesStatus", event.target.value)}>
            <option value="all">Semua progress</option>{salesStatuses.map((status) => <option key={status}>{status}</option>)}
          </select>
        </label>
        {isMarketing && <label className="space-y-1.5 text-xs font-medium"><span className="block">Penugasan Sales</span>
          <select className={selectClass} value={draft.assignment} onChange={(event) => setDraft((current) => ({...current, assignment: event.target.value, status: event.target.value === "unassigned" ? "valid" : current.status}))}>
            <option value="all">Semua penugasan</option><option value="assigned">Sudah di-assign</option><option value="unassigned">Unassigned · valid, tanpa PIC</option>
            {(sales.data ?? []).map((user) => <option key={user.user_id} value={`user:${user.user_id}`}>{user.username}{!user.active ? " (nonaktif)" : ""}</option>)}
            {draft.assignment.startsWith("user:") && !sales.data?.some((user) => `user:${user.user_id}` === draft.assignment) && <option value={draft.assignment}>Sales terpilih</option>}
          </select>
        </label>}
      </div>
      {isMarketing && sales.isPending && <p role="status" className="mt-3 text-xs text-muted-foreground">Memuat akun Sales…</p>}
      {isMarketing && sales.isError && <p role="alert" className="mt-3 text-xs text-destructive">Daftar Sales gagal dimuat. <button type="button" className="underline" onClick={() => void sales.refetch()}>Coba lagi</button></p>}
      {draft.assignment === "unassigned" && isMarketing && <p className="mt-3 text-xs text-muted-foreground">Hanya lead valid tanpa assignment aktif. Status validasi otomatis menjadi Valid.</p>}
      <fieldset className="mt-4 space-y-3 border-t pt-4">
        <legend className="sr-only">Waktu lead masuk (WIB)</legend>
        <label className="block space-y-1.5 text-xs font-medium"><span>Waktu lead masuk (WIB)</span>
          <select className={selectClass} value={draft.dateMode} onChange={(event) => change("dateMode", event.target.value as LeadFilterValues["dateMode"])}>
            <option value="range">Rentang tanggal</option><option value="month">Bulan</option><option value="year">Tahun</option>
          </select>
        </label>
        {draft.dateMode === "range" ? <div className="grid grid-cols-2 gap-3">
          <label className="space-y-1.5 text-xs text-muted-foreground"><span>Dari tanggal</span><Input type="date" min="1900-01-01" max="9999-12-31" value={draft.dateFrom} onChange={(event) => change("dateFrom", event.target.value)} className="h-9 min-w-0 text-xs" /></label>
          <label className="space-y-1.5 text-xs text-muted-foreground"><span>Sampai tanggal</span><Input type="date" min="1900-01-01" max="9999-12-31" value={draft.dateTo} onChange={(event) => change("dateTo", event.target.value)} className="h-9 min-w-0 text-xs" /></label>
        </div> : draft.dateMode === "month" ? <label className="block space-y-1.5 text-xs text-muted-foreground"><span>Pilih bulan</span><Input type="month" min="1900-01" max="9999-12" value={draft.month} onChange={(event) => change("month", event.target.value)} className="h-9" /></label>
          : <label className="block space-y-1.5 text-xs text-muted-foreground"><span>Pilih tahun</span><Input type="number" min={1900} max={9999} placeholder="Contoh: 2026" value={draft.year} onChange={(event) => change("year", event.target.value)} className="h-9" /></label>}
      </fieldset>
      {error && <p role="alert" className="mt-3 text-xs text-destructive">{error}</p>}
      <div className="mt-4 flex items-center justify-between gap-3 border-t pt-4">
        <Button type="button" variant="ghost" size="sm" onClick={() => {const reset = createLeadFilters(sourcePreset); setDraft(reset); onChange(reset); setOpen(false);}}>Reset filter</Button>
        <Button type="button" size="sm" disabled={!!error} onClick={() => {onChange(draft); setOpen(false);}}>Terapkan filter</Button>
      </div>
    </PopoverContent>
  </Popover>;
}
