import {
  CalendarClock,
  ChartPie,
  ClipboardList,
  Compass,
  FileText,
  Gavel,
  LayoutDashboard,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  title: string;
  icon: LucideIcon;
  path: string;
  children?: { title: string; path: string }[];
  /** When set, only users with this role see the item. */
  role?: "marketing" | "sales";
}

export function getNavigation(): NavItem[] {
  return [
    { title: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
    { title: "Leads", icon: Users, path: "/leads/social-media" },
    {
      title: "Pengadaan",
      icon: Gavel,
      path: "/pengadaan",
      children: [
        { title: "SiRUP", path: "/pengadaan/sirup" },
        { title: "SPSE", path: "/pengadaan/spse" },
        { title: "Final", path: "/pengadaan/final" },
      ],
    },
    { title: "Scheduler", icon: CalendarClock, path: "/scheduler", role: "marketing" },
  ];
}
