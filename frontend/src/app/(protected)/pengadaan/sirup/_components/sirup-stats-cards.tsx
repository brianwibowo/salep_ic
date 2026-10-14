import { formatNumber } from "@/utils/formatting/string";

interface AggregateStats {
  seen: number;
  inserted: number;
  updated: number;
  unchanged: number;
  rejected: number;
}

interface SirupStatsCardsProps {
  stats: AggregateStats | null;
}

interface StatCardProps {
  title: string;
  value: number;
  description: string;
  tone?: "default" | "success" | "info" | "warning";
}

function StatCard({
  title,
  value,
  description,
  tone = "default",
}: StatCardProps) {
  const colors = {
    default: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    info: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
    warning: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  };

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          {title}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${colors[tone]}`}
        >
          {formatNumber(value)}
        </span>
      </div>
      <p className="mt-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
        {formatNumber(value)}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

export function SirupStatsCards({ stats }: SirupStatsCardsProps) {
  if (!stats) return null;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      <StatCard
        title="Diproses"
        value={stats.seen}
        description="Paket ditemukan"
      />
      <StatCard
        title="Paket baru"
        value={stats.inserted}
        description="Disimpan ke DB"
        tone="success"
      />
      <StatCard
        title="Diperbarui"
        value={stats.updated}
        description="Data berubah"
        tone="info"
      />
      <StatCard
        title="Tidak berubah"
        value={stats.unchanged}
        description="Sudah mutakhir"
      />
      <StatCard
        title="Ditolak"
        value={stats.rejected}
        description="Format tidak sesuai"
        tone="warning"
      />
    </div>
  );
}
