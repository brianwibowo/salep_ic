"use client";

import Chart from "react-apexcharts";
import { ApexOptions } from "apexcharts";
import { useTheme } from "next-themes";
import { formatCurrency } from "@/lib/utils";

const data = [
  { month: "Jan", revenue: 45000, expenses: 32000 },
  { month: "Feb", revenue: 52000, expenses: 35000 },
  { month: "Mar", revenue: 48000, expenses: 31000 },
  { month: "Apr", revenue: 61000, expenses: 38000 },
  { month: "May", revenue: 55000, expenses: 36000 },
  { month: "Jun", revenue: 67000, expenses: 42000 },
  { month: "Jul", revenue: 72000, expenses: 45000 },
];

// Warna chart — didefinisikan di satu tempat agar legend & chart selalu sinkron
const CHART_COLORS = {
  revenue: "hsl(217, 91%, 50%)",
  expenses: "hsl(38, 92%, 50%)",
};

const series = [
  { name: "Revenue", data: data.map((d) => d.revenue) },
  { name: "Expenses", data: data.map((d) => d.expenses) },
];

export function RevenueChart() {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  const options: ApexOptions = {
    chart: {
      type: "area",
      toolbar: { show: false },
      fontFamily: "inherit",
      zoom: { enabled: false },
    },
    theme: {
      mode: isDark ? "dark" : "light",
    },
    colors: [CHART_COLORS.revenue, CHART_COLORS.expenses],
    dataLabels: { enabled: false },
    stroke: { curve: "smooth", width: 2 },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.3,
        opacityTo: 0,
        stops: [0, 100],
      },
    },
    xaxis: {
      categories: data.map((d) => d.month),
      axisBorder: { show: false },
      axisTicks: { show: false },
      labels: { style: { colors: "hsl(220, 9%, 46%)", fontSize: "12px" } },
    },
    yaxis: {
      labels: {
        style: { colors: "hsl(220, 9%, 46%)", fontSize: "12px" },
        formatter: (val) => formatCurrency(val),
      },
    },
    grid: {
      borderColor: isDark ? "hsl(220, 13%, 35%)" : "hsl(220, 13%, 91%)",
      strokeDashArray: 3,
      xaxis: { lines: { show: false } },
    },
    tooltip: {
      y: { formatter: (val) => formatCurrency(val) },
    },
    legend: { show: false },
  };

  return (
    <div className="rounded-xl bg-card p-6 shadow-card">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-card-foreground">
            Revenue Overview
          </h3>
          <p className="text-sm text-muted-foreground">
            Monthly revenue vs expenses
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: CHART_COLORS.revenue }}
            />
            <span className="text-sm text-muted-foreground">Revenue</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: CHART_COLORS.expenses }}
            />
            <span className="text-sm text-muted-foreground">Expenses</span>
          </div>
        </div>
      </div>
      <div className="h-[300px]">
        <Chart options={options} series={series} type="area" height="100%" />
      </div>
    </div>
  );
}
