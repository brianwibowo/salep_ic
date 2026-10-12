"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ExternalLink, Search, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSession } from "@/hooks/auth/use-auth";
import { useSPSEDefaults, useSPSESearch } from "@/hooks/discovery/use-discovery";

export default function SPSEDiscoveryPage() {
  const { data: session } = useSession();
  const isMarketing = session?.role === "marketing";
  const defaults = useSPSEDefaults(isMarketing);
  const search = useSPSESearch();
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordDraft, setKeywordDraft] = useState("");
  const [limit, setLimit] = useState(30);

  useEffect(() => {
    if (defaults.data) setKeywords(defaults.data.keywords);
  }, [defaults.data]);

  if (!isMarketing) {
    return (
      <p className="rounded-[5px] border p-5 text-sm text-muted-foreground">
        Discovery SPSE hanya tersedia untuk role Marketing.
      </p>
    );
  }

  const addKeyword = () => {
    const keyword = keywordDraft.trim();
    if (!keyword) return;
    if (keywords.some((item) => item.toLocaleLowerCase() === keyword.toLocaleLowerCase())) {
      toast.info("Keyword tersebut sudah ditambahkan.");
      return;
    }
    if (keywords.length >= 30) {
      toast.error("Maksimal 30 keyword untuk satu pencarian SPSE.");
      return;
    }
    setKeywords((current) => [...current, keyword]);
    setKeywordDraft("");
  };

  const runSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleaned = [...new Set(keywords.map((keyword) => keyword.trim()).filter(Boolean))];
    if (cleaned.length === 0) {
      toast.error("Masukkan minimal satu keyword untuk pencarian SPSE.");
      return;
    }

    try {
      const result = await search.mutateAsync({ keywords: cleaned, limit });
      toast.success(`Discovery selesai: ${result.matched} paket ditemukan, ${result.saved} disimpan.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Discovery SPSE gagal dijalankan.");
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Discovery</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Cari paket pengadaan di SPSE Nasional berdasarkan keyword dan masukkan hasilnya ke daftar review Leads SPSE.
        </p>
      </div>

      {defaults.isError && (
        <p role="alert" className="rounded-[5px] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {defaults.error.message}
        </p>
      )}

      <section className="rounded-[5px] border bg-card p-5">
        <h2 className="font-semibold">Pencarian SPSE</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Atur keyword dan batas hasil untuk pencarian paket pengadaan.
        </p>
        <form className="space-y-5" onSubmit={runSearch}>
          <div className="space-y-3 pt-1">
            <label htmlFor="spse-keyword" className="block text-sm font-medium">Input Keyword</label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Input
                id="spse-keyword"
                value={keywordDraft}
                onChange={(event) => setKeywordDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addKeyword();
                  }
                }}
                placeholder={defaults.isPending ? "Memuat keyword…" : "Masukkan keyword"}
                disabled={defaults.isPending || search.isPending}
                className="h-10 rounded-[5px] border-[#9D0A0E] bg-white shadow-none focus-visible:ring-[#9D0A0E]/30"
              />
              <Button
                type="button"
                onClick={addKeyword}
                disabled={!keywordDraft.trim() || defaults.isPending || search.isPending}
                className="h-10 rounded-[5px] bg-[#9D0A0E] px-6 text-white shadow-none hover:bg-[#83080C]"
              >
                Tambah
              </Button>
            </div>
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-2" aria-label="Keyword yang akan dicari">
                {keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="inline-flex h-8 items-center gap-2 rounded-[5px] bg-[#9D0A0E] px-2.5 text-sm text-white"
                  >
                    {keyword}
                    <button
                      type="button"
                      aria-label={`Hapus keyword ${keyword}`}
                      title={`Hapus ${keyword}`}
                      disabled={search.isPending}
                      onClick={() => setKeywords((current) => current.filter((item) => item !== keyword))}
                      className="rounded-sm text-white/90 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
                    >
                      <X className="size-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
          <label className="block max-w-xs space-y-2 text-sm font-medium">
            Batas paket
            <Input
              type="number"
              min={1}
              max={100}
              value={limit}
              onChange={(event) => setLimit(Math.min(100, Math.max(1, Number(event.target.value) || 1)))}
              disabled={search.isPending}
            />
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={defaults.isPending || search.isPending}>
              <Search className="size-4" />
              {search.isPending ? "Mencari paket…" : "Mulai pencarian"}
            </Button>
            <a
              href={defaults.data?.source || "https://spse.inaproc.id/nasional"}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-9 items-center gap-2 px-2 text-sm text-muted-foreground hover:text-foreground"
            >
              Buka SPSE Nasional <ExternalLink className="size-3.5" />
            </a>
          </div>
        </form>
        {search.data && (
          <div className="mt-5 border-t pt-4">
            <h3 className="font-medium">Hasil pencarian terakhir</h3>
            <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
              <Metric label="Paket ditemukan" value={search.data.matched} />
              <Metric label="Paket disimpan sebagai lead" value={search.data.saved} />
            </div>
            <Button asChild variant="outline" className="mt-4 rounded-[5px] shadow-none">
              <Link href="/leads/spse">Lihat Leads SPSE</Link>
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[5px] bg-muted/50 px-3 py-2.5">
      <p className="text-muted-foreground">{label}</p>
      <p className="font-semibold text-foreground">{value}</p>
    </div>
  );
}
