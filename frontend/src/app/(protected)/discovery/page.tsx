"use client";

import { FormEvent, useState } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSession } from "@/hooks/auth/use-auth";
import {
  useManualSearch,
  useSaveDiscoveryConfig,
  useSchedulerAction,
  useSchedulerStatus,
} from "@/hooks/discovery/use-discovery";

function localDate(date: Date) {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10);
}

export default function DiscoveryPage() {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const scheduler = useSchedulerStatus(isMarketing);
  const saveConfig = useSaveDiscoveryConfig();
  const start = useSchedulerAction("start");
  const stop = useSchedulerAction("stop");
  const trigger = useSchedulerAction("trigger");
  const search = useManualSearch();

  const [keywordListDraft, setKeywordListDraft] = useState<string[] | null>(null);
  const [sourceDraft, setSourceDraft] = useState<Array<"threads" | "linkedin"> | null>(null);
  const [limitDraft, setLimitDraft] = useState<number | null>(null);
  const keywords = keywordListDraft ?? scheduler.data?.keywords ?? [];
  const sources: Array<"threads" | "linkedin"> = sourceDraft ?? scheduler.data?.sources.filter((item): item is "threads" | "linkedin" => item === "threads" || item === "linkedin") ?? ["threads"];
  const limit = limitDraft ?? scheduler.data?.limit_per_run ?? 5;
  const [manualKeywords, setManualKeywords] = useState<string[]>([]);
  const [manualSources, setManualSources] = useState<Array<"threads" | "linkedin" | "mock">>(["mock"]);
  const [startDate, setStartDate] = useState(() => localDate(new Date(Date.now() - 6 * 86_400_000)));
  const [endDate, setEndDate] = useState(() => localDate(new Date()));

  if (!isMarketing) {
    return <p className="rounded-[5px] border p-5 text-sm text-muted-foreground">Discovery hanya tersedia untuk role Marketing.</p>;
  }

  const toggleSource = <T extends string>(current: T[], value: T, set: (items: T[]) => void) => {
    set(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    try {
      if (keywords.length === 0) {
        toast.error("Tambahkan minimal satu keyword untuk scheduler.");
        return;
      }
      const result = await saveConfig.mutateAsync({ keywords, sources, limit_per_run: limit });
      toast.success(`Pengaturan tersimpan. Scheduler ${result.is_running ? "aktif" : "siap"}.`);
      setKeywordListDraft(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Gagal menyimpan pengaturan");
    }
  };

  const runSearch = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const cleaned = [...new Set(manualKeywords)];
      if (cleaned.length === 0) {
        toast.error("Tambahkan minimal satu keyword untuk pencarian.");
        return;
      }
      const result = await search.mutateAsync({
        keywords: cleaned,
        start_date: startDate,
        end_date: endDate,
        sources: manualSources,
        limit,
      });
      toast.success(`Pencarian selesai: ${result.total_found} ditemukan, ${result.qualified} memenuhi kriteria.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Pencarian gagal");
    }
  };

  const runAction = async (action: "start" | "stop" | "trigger") => {
    const mutation = action === "start" ? start : action === "stop" ? stop : trigger;
    try {
      await mutation.mutateAsync();
      toast.success(action === "trigger" ? "Siklus discovery dimulai." : `Scheduler ${action === "start" ? "dijalankan" : "dihentikan"}.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Aksi scheduler gagal");
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Discovery</h1>
        <p className="mt-1 text-sm text-muted-foreground">Atur pencarian leads dan jalankan pipeline SALEP.</p>
      </div>

      {scheduler.isError && <ApiNotice message={scheduler.error.message} />}
      <section className="rounded-[5px] border bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-semibold">Scheduler otomatis</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {scheduler.data?.is_running ? "Berjalan" : scheduler.data?.enabled ? "Aktif saat server dimulai" : "Dinonaktifkan di konfigurasi server"}
              {scheduler.data?.last_run_at ? ` · Terakhir berjalan ${new Date(scheduler.data.last_run_at).toLocaleString("id-ID")}` : " · Belum ada siklus"}
            </p>
            {scheduler.data?.last_error && <p className="mt-2 text-sm text-destructive">{scheduler.data.last_error}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled={start.isPending || !scheduler.data?.enabled} onClick={() => runAction("start")}>Mulai</Button>
            <Button variant="outline" disabled={stop.isPending || !scheduler.data?.is_running} onClick={() => runAction("stop")}>Berhenti</Button>
            <Button disabled={trigger.isPending || !scheduler.data?.enabled} onClick={() => runAction("trigger")}>Jalankan sekali</Button>
          </div>
        </div>
        <div className="mt-4 grid gap-3 border-t pt-4 text-sm sm:grid-cols-3">
          <Metric label="Siklus selesai" value={scheduler.data?.total_cycles_executed} />
          <Metric label="Leads ditemukan" value={scheduler.data?.total_leads_found} />
          <Metric label="Leads qualified" value={scheduler.data?.total_leads_qualified} />
        </div>
      </section>

      <section className="rounded-[5px] border bg-card p-5">
        <h2 className="font-semibold">Pengaturan scheduler</h2>
        <p className="mt-1 text-sm text-muted-foreground">Pengaturan disimpan di backend dan digunakan scheduler berikutnya.</p>
        <form className="mt-4 space-y-4" onSubmit={save}>
          <KeywordChipEditor
            keywords={keywords}
            onChange={setKeywordListDraft}
            maxKeywords={40}
            disabled={scheduler.isPending || saveConfig.isPending}
          />
          <div className="flex flex-wrap gap-5 text-sm">
            {(["threads", "linkedin"] as const).map((source) => <label key={source} className="flex items-center gap-2"><input type="checkbox" checked={sources.includes(source)} onChange={() => toggleSource(sources, source, setSourceDraft)} />{source === "threads" ? "Threads" : "LinkedIn"}</label>)}
            <label className="flex items-center gap-2">Batas hasil per sumber <Input className="w-20" type="number" min={1} max={50} value={limit} onChange={(event) => setLimitDraft(Number(event.target.value))} /></label>
          </div>
          <Button type="submit" disabled={saveConfig.isPending || scheduler.isPending}>{saveConfig.isPending ? "Menyimpan…" : "Simpan pengaturan"}</Button>
        </form>
      </section>

      <section className="rounded-[5px] border bg-card p-5">
        <h2 className="font-semibold">Pencarian manual</h2>
        <p className="mt-1 text-sm text-muted-foreground">Pencarian memakai keyword yang dimasukkan di sini dan menjalankan analisis AI.</p>
        <form className="mt-4 space-y-4" onSubmit={runSearch}>
          <KeywordChipEditor
            keywords={manualKeywords}
            onChange={setManualKeywords}
            maxKeywords={10}
            disabled={search.isPending}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1.5 text-sm">Dari tanggal<Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
            <label className="space-y-1.5 text-sm">Sampai tanggal<Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
          </div>
          <div className="flex flex-wrap gap-5 text-sm">
            {(["threads", "linkedin", "mock"] as const).map((source) => <label key={source} className="flex items-center gap-2"><input type="checkbox" checked={manualSources.includes(source)} onChange={() => toggleSource(manualSources, source, setManualSources)} />{source === "mock" ? "Mock (demo)" : source === "threads" ? "Threads" : "LinkedIn"}</label>)}
          </div>
          <Button type="submit" disabled={search.isPending}>{search.isPending ? "Mencari dan menganalisis…" : "Mulai pencarian"}</Button>
          {search.data && <p className="text-sm text-muted-foreground">Pencarian terakhir: {search.data.total_found} ditemukan, {search.data.total_analyzed} dianalisis, {search.data.qualified} qualified.</p>}
        </form>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: number }) {
  return <p className="flex justify-between gap-3 text-muted-foreground">{label}<strong className="text-foreground">{value ?? "—"}</strong></p>;
}

function KeywordChipEditor({
  keywords,
  onChange,
  maxKeywords,
  disabled,
}: {
  keywords: string[];
  onChange: (keywords: string[]) => void;
  maxKeywords: number;
  disabled: boolean;
}) {
  const [draft, setDraft] = useState("");

  const addKeyword = () => {
    const keyword = draft.trim();
    if (!keyword) return;
    if (keywords.some((item) => item.toLowerCase() === keyword.toLowerCase())) {
      toast.info("Keyword tersebut sudah ditambahkan.");
      return;
    }
    if (keywords.length >= maxKeywords) {
      toast.error(`Maksimal ${maxKeywords} keyword.`);
      return;
    }
    onChange([...keywords, keyword]);
    setDraft("");
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium">Input Keyword</label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addKeyword();
            }
          }}
          placeholder="Masukkan keyword"
          disabled={disabled}
          className="h-10 rounded-[5px] border-[#9D0A0E] bg-white shadow-none focus-visible:ring-[#9D0A0E]/30"
        />
        <Button
          type="button"
          onClick={addKeyword}
          disabled={!draft.trim() || disabled}
          className="h-10 rounded-[5px] bg-[#9D0A0E] px-6 text-white shadow-none hover:bg-[#83080C]"
        >
          Tambah
        </Button>
      </div>
      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-2" aria-label="Keyword yang akan digunakan">
          {keywords.map((keyword) => (
            <span key={keyword} className="inline-flex h-8 items-center gap-2 rounded-[5px] bg-[#9D0A0E] px-2.5 text-sm text-white">
              {keyword}
              <button
                type="button"
                aria-label={`Hapus keyword ${keyword}`}
                title={`Hapus ${keyword}`}
                disabled={disabled}
                onClick={() => onChange(keywords.filter((item) => item !== keyword))}
                className="rounded-sm text-white/90 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
              >
                <X className="size-4" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ApiNotice({ message }: { message: string }) {
  return <p role="alert" className="rounded-[5px] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{message}</p>;
}
