"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Lead, SalesStatusLog } from "@/types/salep";

const dateTime = (value: string) => new Date(value).toLocaleString("id-ID", {dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Jakarta"});

export function SalesProgressCell({ lead }: { lead: Lead }) {
  const latest = lead.sales_status_logs?.at(-1);
  return <div className="max-w-64 whitespace-normal">
    <span className="inline-flex rounded-md bg-muted px-2 py-1 text-xs font-medium">{lead.sales_status}</span>
    {latest ? <>
      <p className="mt-2 line-clamp-2 text-xs text-muted-foreground" title={latest.note}>{latest.note}</p>
      <p className="mt-1 text-[11px] text-muted-foreground">{latest.changed_by || "Sales"} · {dateTime(latest.changed_at)}</p>
    </> : <p className="mt-2 text-xs text-muted-foreground">Belum ada catatan tindak lanjut.</p>}
  </div>;
}

export function SalesProgressHistory({ lead, onRefresh, refreshing }: {
  lead: Lead; onRefresh: () => void; refreshing: boolean;
}) {
  const logs = [...(lead.sales_status_logs ?? [])].reverse();
  const latest = logs[0];
  return <section className="space-y-3 border-t p-4 sm:p-5" aria-label="Progress Sales">
    <div className="flex items-center justify-between gap-3">
      <div><h3 className="text-sm font-semibold">Progress Sales</h3><p className="mt-1 text-xs text-muted-foreground">Status saat ini: <span className="font-medium text-foreground">{lead.sales_status}</span></p></div>
      <Button type="button" variant="ghost" size="icon-sm" disabled={refreshing} onClick={onRefresh} aria-label="Muat progress Sales terbaru" title="Muat progress Sales terbaru"><RefreshCw className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} /></Button>
    </div>
    {latest ? <div className="rounded-md border bg-muted/20 p-3"><p className="mb-2 text-xs font-medium text-muted-foreground">Catatan terbaru</p><ProgressEntry log={latest} /></div>
      : <p className="text-sm text-muted-foreground">Sales belum menambahkan catatan tindak lanjut.</p>}
    {logs.length > 1 && <details className="pt-1">
      <summary className="cursor-pointer text-xs font-medium">Lihat {logs.length - 1} catatan sebelumnya</summary>
      <ol className="mt-3 space-y-4">{logs.slice(1).map((log) => <li key={log.id} className="border-l-2 pl-3"><ProgressEntry log={log} /></li>)}</ol>
    </details>}
  </section>;
}

function ProgressEntry({ log }: { log: SalesStatusLog }) {
  return <>
    <p className="text-xs font-medium">{log.from_status} → {log.to_status}</p>
    <p className="mt-1.5 whitespace-pre-wrap break-words text-sm leading-relaxed">{log.note}</p>
    <p className="mt-2 text-xs text-muted-foreground">{log.changed_by || "Sales"} · {dateTime(log.changed_at)} WIB</p>
  </>;
}
