"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, Clock3, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLeads, useLeadStats } from "@/hooks/leads/use-leads";
import { useSession } from "@/hooks/auth/use-auth";

const number = new Intl.NumberFormat("id-ID");

export default function DashboardPage() {
  const { data: session } = useSession();
  const stats = useLeadStats();
  const recent = useLeads({ limit: 5, offset: 0 });
  const isSales = session?.role === "sales";

  const cards = isSales
    ? [
        { label: "Leads valid", value: stats.data?.valid, icon: Users },
        { label: "Belum dihubungi", value: stats.data?.sales_new, icon: Clock3 },
        { label: "Sedang ditindaklanjuti", value: stats.data?.sales_in_progress, icon: Clock3 },
        { label: "Closing", value: stats.data?.sales_closed, icon: CheckCircle2 },
      ]
    : [
        { label: "Total leads", value: stats.data?.total, icon: Users },
        { label: "Menunggu validasi", value: stats.data?.pending, icon: Clock3 },
        { label: "Valid", value: stats.data?.valid, icon: CheckCircle2 },
        { label: "Tidak valid", value: stats.data?.invalid, icon: Users },
      ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Ringkasan leads</h1>
          <p className="mt-1 text-sm text-muted-foreground">Angka dan aktivitas terbaru dari backend SALEP.</p>
        </div>
        <Button asChild variant="outline"><Link href="/leads">Lihat semua leads <ArrowRight className="ml-2 h-4 w-4" /></Link></Button>
      </div>

      {stats.isError && <ApiNotice message={stats.error.message} />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ label, value, icon: Icon }) => (
          <section key={label} className="rounded-xl border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between text-sm text-muted-foreground">{label}<Icon className="h-4 w-4" /></div>
            <p className="mt-3 text-3xl font-semibold">{value === undefined ? "—" : number.format(value)}</p>
          </section>
        ))}
      </div>

      <section className="rounded-xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div><h2 className="font-semibold">Leads terbaru</h2><p className="text-sm text-muted-foreground">Data terbaru yang tersimpan.</p></div>
          <Button asChild variant="ghost" size="sm"><Link href="/leads">Buka daftar</Link></Button>
        </div>
        {recent.isPending ? <p className="p-5 text-sm text-muted-foreground">Memuat leads…</p> : null}
        {recent.isError ? <ApiNotice message={recent.error.message} /> : null}
        {recent.data?.length === 0 ? <p className="p-5 text-sm text-muted-foreground">Belum ada data leads.</p> : null}
        {recent.data && recent.data.length > 0 ? (
          <div className="divide-y">
            {recent.data.map((lead) => (
              <div key={lead.lead_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{lead.author_name || "Prospek tanpa nama"}</p>
                  <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">{lead.content}</p>
                </div>
                <div className="flex shrink-0 items-center gap-3 text-sm">
                  <span className="capitalize text-muted-foreground">{lead.source}</span>
                  <span className="rounded-full bg-primary/10 px-2.5 py-1 font-medium text-primary">Skor {lead.lead_score}</span>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function ApiNotice({ message }: { message: string }) {
  return <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{message}</p>;
}
