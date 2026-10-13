import { ChartPie, LayoutDashboard, Users } from "lucide-react";

export function getNavigation() {
  return [
    { title: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
    { title: "Leads", icon: Users, path: "/leads" },
    { title: "Final", icon: ChartPie, path: "/final" },
  ];
}
