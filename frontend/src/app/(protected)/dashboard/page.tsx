import { KPICard } from "./_components/KPICard";
import { RevenueChart } from "./_components/RevenueChart";
import { RecentActivity } from "./_components/RecentActivity";
import { LowStockAlerts } from "./_components/LowStockAlerts";
import { DollarSign, TrendingUp, Package, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  return (
    <>
      {/* Page Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Welcome back! Here&apos;s what&apos;s happening with your business.
          </p>
        </div>
        <Button variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          Export Report
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Revenue"
          value="Rp 72.450.000"
          change={12.5}
          changeLabel="vs last month"
          icon={DollarSign}
          variant="success"
        />
        <KPICard
          title="Total Expenses"
          value="Rp 45.230.000"
          change={-3.2}
          changeLabel="vs last month"
          icon={TrendingUp}
          variant="warning"
        />
        <KPICard
          title="Net Profit"
          value="Rp 27.220.000"
          change={8.1}
          changeLabel="vs last month"
          icon={DollarSign}
          variant="default"
        />
        <KPICard
          title="Active Products"
          value="156"
          change={5}
          changeLabel="new this month"
          icon={Package}
          variant="default"
        />
      </div>

      {/* Charts and Activity */}
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RevenueChart />
        </div>
        <div>
          <RecentActivity />
        </div>
      </div>

      {/* Alerts */}
      <div className="mt-6">
        <LowStockAlerts />
      </div>
    </>
  );
}
