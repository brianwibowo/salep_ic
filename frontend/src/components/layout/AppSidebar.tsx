"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useLogout } from "@/hooks/auth/use-auth";
import { getNavigation } from "@/constants/menus-constant";
import { SalepRole } from "@/types/salep";

export function AppSidebar({ role }: { role: SalepRole }) {
  const pathname = usePathname();
  const logout = useLogout();
  const navigation = getNavigation(role);

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sidebar-primary font-bold text-sidebar-primary-foreground">
          S
        </div>
        <div>
          <h1 className="text-sm font-semibold text-sidebar-primary-foreground">SALEP</h1>
          <p className="text-xs capitalize text-sidebar-muted">Tim {role}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.path || pathname.startsWith(`${item.path}/`);
          return (
            <Link
              key={item.path}
              href={item.path}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50",
              )}
            >
              <Icon className="h-5 w-5" />
              {item.title}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-muted hover:text-sidebar-foreground"
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          <LogOut className="h-5 w-5" />
          Keluar
        </Button>
      </div>
    </aside>
  );
}
