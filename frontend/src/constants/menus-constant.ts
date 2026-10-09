import { Compass, LayoutDashboard, Users } from "lucide-react";
import { SalepRole } from "@/types/salep";

export function getNavigation(role: SalepRole) {
  return [
    { title: "Ringkasan", icon: LayoutDashboard, path: "/dashboard" },
    { title: "Leads", icon: Users, path: "/leads" },
    ...(role === "marketing"
      ? [{ title: "Discovery", icon: Compass, path: "/discovery" }]
      : []),
  ];
}
