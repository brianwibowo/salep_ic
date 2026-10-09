"use client";

import { CheckCircle2, Clock3, Users } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { useLeadStats } from "@/hooks/leads/use-leads";
import { useSession } from "@/hooks/auth/use-auth";

const number = new Intl.NumberFormat("id-ID");

export default function DashboardPage() {
  const { data: session } = useSession();
  const stats = useLeadStats();
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

  const chartData = isSales
    ? [
        { stage: "Leads valid", count: stats.data?.valid ?? 0, fill: "var(--color-valid)" },
        { stage: "Belum dihubungi", count: stats.data?.sales_new ?? 0, fill: "var(--color-new)" },
        { stage: "Ditindaklanjuti", count: stats.data?.sales_in_progress ?? 0, fill: "var(--color-progress)" },
        { stage: "Closing", count: stats.data?.sales_closed ?? 0, fill: "var(--color-closed)" },
      ]
    : [
        { stage: "Menunggu validasi", count: stats.data?.pending ?? 0, fill: "var(--color-pending)" },
        { stage: "Valid", count: stats.data?.valid ?? 0, fill: "var(--color-valid)" },
        { stage: "Tidak valid", count: stats.data?.invalid ?? 0, fill: "var(--color-invalid)" },
      ];

  const chartConfig = {
    count: { label: "Jumlah leads", color: "#9D0A0E" },
    pending: { label: "Menunggu validasi", color: "#D97706" },
    valid: { label: "Valid", color: "#16A34A" },
    invalid: { label: "Tidak valid", color: "#64748B" },
    new: { label: "Belum dihubungi", color: "#9D0A0E" },
    progress: { label: "Ditindaklanjuti", color: "#D97706" },
    closed: { label: "Closing", color: "#16A34A" },
  } satisfies ChartConfig;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
        </div>
      </div>

      {stats.isError && <ApiNotice message={stats.error.message} />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ label, value, icon: Icon }) => (
          <section key={label} className="rounded-[5px] border bg-card p-5">
            <div className="flex items-center justify-between text-sm text-muted-foreground">{label}<Icon className="h-4 w-4" /></div>
            <p className="mt-3 text-3xl font-semibold">{value === undefined ? "—" : number.format(value)}</p>
          </section>
        ))}
      </div>

      <section className="rounded-[5px] border bg-card p-5">
        <div className="mb-4">
          <h2 className="font-semibold">Distribusi status leads</h2>
          <p className="text-sm text-muted-foreground">
            {isSales ? "Status tindak lanjut prospek." : "Status validasi prospek."}
          </p>
        </div>
        {stats.isPending ? (
          <div className="flex h-[280px] items-center justify-center text-sm text-muted-foreground">
            Memuat grafik…
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="h-[280px]">
            <BarChart
              accessibilityLayer
              data={chartData}
              layout="vertical"
              margin={{ left: 4, right: 16 }}
            >
              <CartesianGrid horizontal={false} />
              <XAxis type="number" allowDecimals={false} axisLine={false} tickLine={false} />
              <YAxis
                type="category"
                dataKey="stage"
                width={132}
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12 }}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="count" radius={5} maxBarSize={28}>
                {chartData.map((item) => (
                  <Cell key={item.stage} fill={item.fill} />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
        )}
      </section>

    </div>
  );
}

function ApiNotice({ message }: { message: string }) {
  return <p role="alert" className="rounded-[5px] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{message}</p>;
}
