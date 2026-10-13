"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import { ExternalLink, RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useFinalPackages, useFinalSummary } from "@/hooks/use-final-analytics";
import type { FinalReason } from "@/types/salep";

const COLORS: Record<string, string> = {
  contract_completed: "#16a34a",
  contract_terminated: "#dc2626",
  contract_stopped: "#ea580c",
  tender_completed_no_contract: "#2563eb",
  unknown_final_reason: "#64748b",
};

const REASONS: Array<{ value: FinalReason; label: string }> = [
  { value: "contract_completed", label: "Kontrak selesai" },
  { value: "contract_terminated", label: "Pemutusan kontrak" },
  { value: "contract_stopped", label: "Penghentian kontrak" },
  { value: "tender_completed_no_contract", label: "Tender selesai tanpa kontrak" },
  { value: "unknown_final_reason", label: "Alasan belum diketahui" },
];

const currency = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0, notation: "compact" });
const number = new Intl.NumberFormat("id-ID");

export default function FinalPage() {
  const activeYear = new Date().getFullYear();
  const [years, setYears] = useState<number[]>([activeYear - 1, activeYear]);
  const [reason, setReason] = useState<FinalReason | "all">("all");
  const [track, setTrack] = useState("all");
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const filters = useMemo(() => ({
    fiscal_years: years,
    reasons: reason === "all" ? undefined : [reason],
    tracks: track === "all" ? undefined : [track],
    categories: category === "all" ? undefined : [category],
    search: search.trim() || undefined,
  }), [category, reason, search, track, years]);
  const summary = useFinalSummary(filters);
  const packages = useFinalPackages({ ...filters, page: 1, limit: 12 });
  const chartData = (summary.data?.by_reason ?? []).filter((item) => item.count > 0);

  function toggleYear(year: number) {
    setYears((current) => current.includes(year)
      ? current.length === 1 ? current : current.filter((value) => value !== year)
      : [...current, year].sort());
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">INAPROC / SPSE</p>
          <h1 className="text-2xl font-semibold">Final procurement intelligence</h1>
          <p className="mt-1 text-sm text-muted-foreground">Mengapa paket berakhir dan di mana peluang managed service muncul.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-muted" onClick={() => summary.refetch()}>
          <RefreshCw className="size-4" /> Refresh
        </button>
      </div>

      <section className="flex flex-wrap items-center gap-3 rounded-md border bg-card p-4">
        <span className="text-sm font-medium">Tahun anggaran</span>
        {[activeYear - 1, activeYear].map((year) => (
          <button key={year} onClick={() => toggleYear(year)} className={`rounded-md px-3 py-1.5 text-sm ${years.includes(year) ? "bg-[#9D0A0E] text-white" : "border text-muted-foreground"}`}>
            {year}
          </button>
        ))}
        <label className="ml-auto flex items-center gap-2 text-sm text-muted-foreground">
          Reason
          <select value={reason} onChange={(event) => setReason(event.target.value as FinalReason | "all")} className="rounded-md border bg-background px-2 py-1.5 text-foreground">
            <option value="all">Semua reason</option>
            {REASONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          Track
          <select value={track} onChange={(event) => setTrack(event.target.value)} className="rounded-md border bg-background px-2 py-1.5 text-foreground">
            <option value="all">Semua track</option>
            {(summary.data?.by_track ?? []).map((item) => <option key={item.track} value={item.track}>{item.track}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          Kategori
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="max-w-52 rounded-md border bg-background px-2 py-1.5 text-foreground">
            <option value="all">Semua kategori</option>
            {(summary.data?.by_category ?? []).map((item) => <option key={item.category} value={item.category}>{item.label}</option>)}
          </select>
        </label>
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari paket / instansi" className="w-full rounded-md border bg-background px-3 py-1.5 text-sm sm:w-56" />
      </section>

      {summary.isError && <p className="rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{summary.error.message}</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Paket final" value={number.format(summary.data?.total ?? 0)} />
        <Metric label="Total pagu" value={currency.format(summary.data?.total_budget_amount ?? 0)} />
        <Metric label="Total HPS" value={currency.format(summary.data?.total_hps_amount ?? 0)} />
        <Metric label="Prioritas high" value={number.format(summary.data?.by_priority.find((item) => item.priority === "high")?.count ?? 0)} />
      </div>

      <section className="grid gap-6 rounded-md border bg-card p-5 lg:grid-cols-[minmax(280px,380px)_1fr]">
        <div>
          <h2 className="font-semibold">Alasan paket berakhir</h2>
          <p className="mt-1 text-sm text-muted-foreground">Satu paket dihitung sekali berdasarkan reason paling spesifik yang tersedia.</p>
          <div className="mt-4 h-64">
            {chartData.length ? <ResponsiveContainer width="100%" height="100%"><PieChart>
              <Pie data={chartData} dataKey="count" nameKey="label" innerRadius={68} outerRadius={100} paddingAngle={2} strokeWidth={2} stroke="hsl(var(--background))">
                {chartData.map((item) => <Cell key={item.reason} fill={COLORS[item.reason] ?? "#64748b"} />)}
              </Pie>
              <Tooltip formatter={(value) => [number.format(Number(value)), "Paket"]} />
            </PieChart></ResponsiveContainer> : <div className="flex h-full items-center justify-center text-sm text-muted-foreground">Belum ada data Final.</div>}
          </div>
        </div>
        <div className="space-y-3 self-center">
          {(summary.data?.by_reason ?? []).map((item) => (
            <div key={item.reason} className="flex items-center justify-between gap-4 rounded-md border p-3">
              <div className="flex min-w-0 items-center gap-3"><span className="size-3 shrink-0 rounded-full" style={{ backgroundColor: COLORS[item.reason] ?? "#64748b" }} /><span className="truncate text-sm">{item.label}</span></div>
              <div className="text-right"><p className="font-semibold tabular-nums">{number.format(item.count)}</p><p className="text-xs text-muted-foreground">{item.percentage.toFixed(1)}%</p></div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-md border bg-card p-5">
          <h2 className="font-semibold">Kategori peluang IT</h2>
          <p className="mt-1 text-sm text-muted-foreground">Klasifikasi berbasis bukti keyword paket, bukan klaim vendor.</p>
          <div className="mt-4 h-72">
            {(summary.data?.by_category ?? []).length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={summary.data?.by_category ?? []} layout="vertical" margin={{ left: 12, right: 20 }}>
              <CartesianGrid horizontal={false} strokeDasharray="3 3" />
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="label" width={150} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(value) => [number.format(Number(value)), "Paket"]} />
              <Bar dataKey="count" fill="#9D0A0E" radius={[0, 4, 4, 0]} />
            </BarChart></ResponsiveContainer> : <Empty />}
          </div>
        </section>

        <section className="rounded-md border bg-card p-5">
          <h2 className="font-semibold">Prioritas sales</h2>
          <p className="mt-1 text-sm text-muted-foreground">Prioritas menggabungkan kategori IT, nilai paket, track, dan reason.</p>
          <div className="mt-4 space-y-3">
            {(summary.data?.by_priority ?? []).map((item) => <div key={item.priority} className="flex items-center justify-between rounded-md border p-3"><div className="flex items-center gap-3"><PriorityBadge priority={item.priority} /><span className="text-sm">{number.format(item.count)} paket</span></div><span className="text-sm font-medium">{currency.format(item.hps_amount)}</span></div>)}
            {!summary.data?.by_priority?.length && <Empty />}
          </div>
          <div className="mt-5 border-t pt-4">
            <h3 className="text-sm font-semibold">Rekomendasi tindakan teratas</h3>
            <div className="mt-3 space-y-3">
              {(summary.data?.recommendations ?? []).slice(0, 4).map((item) => <div key={item.package_id} className="rounded-md bg-muted/40 p-3"><div className="flex items-start justify-between gap-3"><p className="line-clamp-2 text-sm font-medium">{item.package_name}</p><PriorityBadge priority={item.sales_priority} /></div><p className="mt-1 text-xs text-muted-foreground">{item.organization ?? "Instansi tidak diketahui"} · {item.service_category_label}</p><p className="mt-2 text-xs leading-5 text-muted-foreground">{item.sales_recommendation}</p></div>)}
            </div>
          </div>
        </section>
      </div>

      <section className="grid gap-6 xl:grid-cols-2">
        <BreakdownTable title="Instansi dengan peluang terbesar" headers={["Instansi", "Paket", "High", "HPS"]} rows={(summary.data?.by_organization ?? []).slice(0, 8).map((item) => [<button key={item.organization} onClick={() => setSearch(item.organization)} className="max-w-[260px] truncate text-left text-[#9D0A0E] hover:underline">{item.organization}</button>, number.format(item.count), number.format(item.high_priority_count), currency.format(item.hps_amount)])} empty="Belum ada instansi." />
        <BreakdownTable title="Track yang perlu dimonitor" headers={["Track", "Paket", "HPS"]} rows={(summary.data?.by_track ?? []).map((item) => [<button key={item.track} onClick={() => setTrack(item.track)} className="text-left text-[#9D0A0E] hover:underline">{item.track}</button>, number.format(item.count), currency.format(item.hps_amount)])} empty="Belum ada track." />
      </section>

      <section className="rounded-md border bg-card">
        <div className="border-b p-5"><h2 className="font-semibold">Paket yang masuk Final</h2><p className="mt-1 text-sm text-muted-foreground">Klik sumber untuk membuka bukti publik di SPSE.</p></div>
        <div className="divide-y">
          {(packages.data?.items ?? []).map((item) => <article key={item.package_id} className="grid gap-2 p-5 md:grid-cols-[1fr_auto]">
            <div><div className="flex flex-wrap items-center gap-2"><span className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ backgroundColor: `${COLORS[item.reason]}20`, color: COLORS[item.reason] }}>{item.reason_label}</span><PriorityBadge priority={item.sales_priority} /><span className="text-xs text-muted-foreground">{item.fiscal_year} · {item.track} · {item.service_category_label}</span></div><h3 className="mt-2 font-medium">{item.package_name}</h3><p className="text-sm text-muted-foreground">{item.organization ?? "Instansi tidak tersedia"}{item.satker ? ` · ${item.satker}` : ""}</p><p className="mt-1 text-xs text-muted-foreground">Managed service fit {item.managed_service_fit}/100 · {item.sales_recommendation}</p></div>
            <Link href={item.source_url} target="_blank" className="inline-flex items-center gap-1 self-center text-sm text-[#9D0A0E] hover:underline">Buka sumber <ExternalLink className="size-3.5" /></Link>
          </article>)}
          {!packages.isPending && !packages.data?.items.length && <p className="p-8 text-center text-sm text-muted-foreground">Tidak ada paket untuk filter ini.</p>}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <section className="rounded-md border bg-card p-5"><p className="text-sm text-muted-foreground">{label}</p><p className="mt-2 text-2xl font-semibold">{value}</p></section>;
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors = priority === "high" ? "bg-red-100 text-red-700" : priority === "medium" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600";
  return <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase ${colors}`}>{priority}</span>;
}

function BreakdownTable({ title, headers, rows, empty }: { title: string; headers: string[]; rows: ReactNode[][]; empty: string }) {
  return <section className="rounded-md border bg-card p-5"><h2 className="font-semibold">{title}</h2><div className="mt-4 overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left text-xs text-muted-foreground">{headers.map((header) => <th key={header} className="pb-2 pr-3 font-medium">{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index} className="border-b last:border-0"><td className="max-w-[280px] truncate py-3 pr-3">{row[0]}</td>{row.slice(1).map((cell, cellIndex) => <td key={cellIndex} className="whitespace-nowrap py-3 pr-3">{cell}</td>)}</tr>)}</tbody></table>{!rows.length && <p className="py-5 text-center text-sm text-muted-foreground">{empty}</p>}</div></section>;
}

function Empty() {
  return <div className="flex h-full items-center justify-center text-sm text-muted-foreground">Belum ada data.</div>;
}
