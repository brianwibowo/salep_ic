"use client";

import { useState } from "react";
import { ExternalLink, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useSession } from "@/hooks/auth/use-auth";
import { useLeads, useUpdateLeadStatus, useUpdateSalesStatus } from "@/hooks/leads/use-leads";
import { Lead } from "@/types/salep";

const PAGE_SIZE = 50;
const salesStatuses: Lead["sales_status"][] = ["Belum Dihubungi", "Sedang Dihubungi", "Closing", "Batal"];

export default function LeadsPage() {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [source, setSource] = useState("all");
  const [salesStatus, setSalesStatus] = useState("all");
  const [offset, setOffset] = useState(0);
  const filters = {
    search,
    status: isMarketing ? status : "all",
    source,
    sales_status: salesStatus,
    offset,
    limit: PAGE_SIZE,
  };
  const leads = useLeads(filters);
  const updateMarketing = useUpdateLeadStatus();
  const updateSales = useUpdateSalesStatus();

  const setFilter = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    setOffset(0);
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Leads</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {isMarketing ? "Tinjau dan validasi prospek yang ditemukan." : "Kelola tindak lanjut untuk prospek yang sudah valid."}
        </p>
      </div>

      <section className="rounded-xl border bg-card p-4 shadow-sm">
        <div className="grid gap-3 md:grid-cols-4">
          <label className="relative md:col-span-2">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input className="pl-9" placeholder="Cari konten, nama, kebutuhan…" value={search} onChange={(event) => setFilter(setSearch)(event.target.value)} />
          </label>
          {isMarketing && (
            <label className="text-sm">
              <span className="sr-only">Status validasi</span>
              <select className="h-9 w-full rounded-md border bg-background px-3" value={status} onChange={(event) => setFilter(setStatus)(event.target.value)}>
                <option value="all">Semua status marketing</option><option value="pending">Menunggu review</option><option value="valid">Valid</option><option value="invalid">Tidak valid</option>
              </select>
            </label>
          )}
          <label className="text-sm">
            <span className="sr-only">Sumber</span>
            <select className="h-9 w-full rounded-md border bg-background px-3" value={source} onChange={(event) => setFilter(setSource)(event.target.value)}>
              <option value="all">Semua sumber</option><option value="threads">Threads</option><option value="linkedin">LinkedIn</option><option value="spse">SPSE</option><option value="mock">Mock</option>
            </select>
          </label>
          {!isMarketing && (
            <label className="text-sm md:col-start-4">
              <span className="sr-only">Status tindak lanjut</span>
              <select className="h-9 w-full rounded-md border bg-background px-3" value={salesStatus} onChange={(event) => setFilter(setSalesStatus)(event.target.value)}>
                <option value="all">Semua tindak lanjut</option>{salesStatuses.map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
          )}
        </div>
      </section>

      {leads.isError && <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{leads.error.message}</p>}
      <section className="overflow-hidden rounded-xl border bg-card shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b bg-muted/50 text-xs uppercase text-muted-foreground">
              <tr><th className="px-4 py-3">Prospek</th><th className="px-4 py-3">Sumber</th><th className="px-4 py-3">Skor</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Tindak lanjut</th><th className="px-4 py-3">Posting</th></tr>
            </thead>
            <tbody className="divide-y">
              {leads.isPending && <tr><td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">Memuat leads…</td></tr>}
              {!leads.isPending && leads.data?.length === 0 && <tr><td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">Tidak ada leads untuk filter ini.</td></tr>}
              {leads.data?.map((lead) => (
                <tr key={lead.lead_id} className="align-top hover:bg-muted/30">
                  <td className="max-w-xl px-4 py-4">
                    <p className="font-medium">{lead.author_name || "Prospek tanpa nama"}</p>
                    <p className="mt-1 line-clamp-2 text-muted-foreground">{lead.content}</p>
                    {lead.needs?.length > 0 && <p className="mt-2 text-xs text-muted-foreground">Kebutuhan: {lead.needs.join(", ")}</p>}
                  </td>
                  <td className="px-4 py-4 capitalize">{lead.source}</td>
                  <td className="px-4 py-4"><span className="rounded-full bg-primary/10 px-2.5 py-1 font-semibold text-primary">{lead.lead_score}</span></td>
                  <td className="px-4 py-4">
                    {isMarketing ? (
                      <select aria-label={`Status marketing ${lead.author_name || lead.lead_id}`} className="h-9 rounded-md border bg-background px-2" value={lead.marketing_status} disabled={updateMarketing.isPending} onChange={(event) => updateMarketing.mutate({ leadId: lead.lead_id, status: event.target.value as Lead["marketing_status"] })}>
                        <option value="pending">Menunggu review</option><option value="valid">Valid</option><option value="invalid">Tidak valid</option>
                      </select>
                    ) : <StatusPill value={lead.marketing_status} />}
                  </td>
                  <td className="px-4 py-4">
                    {isMarketing ? <StatusPill value={lead.sales_status} /> : (
                      <select aria-label={`Status tindak lanjut ${lead.author_name || lead.lead_id}`} className="h-9 rounded-md border bg-background px-2" value={lead.sales_status} disabled={updateSales.isPending} onChange={(event) => updateSales.mutate({ leadId: lead.lead_id, status: event.target.value as Lead["sales_status"] })}>
                        {salesStatuses.map((item) => <option key={item}>{item}</option>)}
                      </select>
                    )}
                  </td>
                  <td className="px-4 py-4"><a className="inline-flex items-center gap-1 text-primary hover:underline" href={lead.source_url} target="_blank" rel="noreferrer">Buka <ExternalLink className="h-3.5 w-3.5" /></a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between border-t px-4 py-3 text-sm text-muted-foreground">
          <span>{offset + 1}–{offset + (leads.data?.length || 0)} ditampilkan</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={offset === 0 || leads.isFetching} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Sebelumnya</Button>
            <Button size="sm" variant="outline" disabled={(leads.data?.length || 0) < PAGE_SIZE || leads.isFetching} onClick={() => setOffset(offset + PAGE_SIZE)}>Berikutnya</Button>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatusPill({ value }: { value: string }) {
  return <span className="inline-flex rounded-full bg-muted px-2.5 py-1 text-xs font-medium">{value}</span>;
}
