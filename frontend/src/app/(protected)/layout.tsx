"use client";

import { ReactNode, useEffect, type CSSProperties } from "react";
import { usePathname, useRouter } from "next/navigation";
import { UserRound } from "lucide-react";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { useSession } from "@/hooks/auth/use-auth";
import { ApiServiceError } from "@/utils/api/apiService";

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const session = useSession();

  useEffect(() => {
    if (
      session.error instanceof ApiServiceError &&
      session.error.status === 401
    ) {
      router.replace("/login");
    }
  }, [router, session.error]);

  useEffect(() => {
    if (session.data?.role === "sales" && pathname.startsWith("/discovery")) {
      router.replace("/dashboard");
    }
  }, [pathname, router, session.data?.role]);

  useEffect(() => {
    if (session.data?.role === "super_admin" && pathname !== "/admin/users") {
      router.replace("/admin/users");
    }
  }, [pathname, router, session.data?.role]);

  if (
    session.isPending ||
    (session.error instanceof ApiServiceError && session.error.status === 401)
  ) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Memeriksa sesi SALEP…
      </div>
    );
  }

  if (session.isError || !session.data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="font-medium">Tidak dapat menghubungi backend SALEP.</p>
        <p className="max-w-md text-sm text-muted-foreground">
          {session.error?.message}
        </p>
        <Button variant="outline" onClick={() => session.refetch()}>
          Coba lagi
        </Button>
      </div>
    );
  }

  if (session.data.role === "sales" && pathname.startsWith("/discovery")) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Membuka ringkasan leads…
      </div>
    );
  }

  if (session.data.role === "super_admin" && pathname !== "/admin/users") {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Membuka halaman Kelola Akun…
      </div>
    );
  }

  return (
    <SidebarProvider
      defaultOpen={false}
      style={{ "--sidebar-width-icon": "4.5rem" } as CSSProperties}
    >
      <AppSidebar role={session.data.role} />
      <SidebarInset className="min-w-0 max-w-full">
        <header className="sticky top-0 z-30 flex h-16 w-full shrink-0 items-center justify-between border-b border-border bg-card px-5">
          <div className="flex items-center">
            <SidebarTrigger className="size-8 [&>svg]:size-6" />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium">
              {session.data.role === "super_admin"
                ? "Super Admin"
                : session.data.role === "marketing"
                  ? "Marketing"
                  : "Sales"}
            </span>
            <Avatar className="size-8 border-2 border-amber-400 bg-amber-400">
              <AvatarFallback className="bg-amber-400 text-slate-900">
                <UserRound className="size-5" />
              </AvatarFallback>
            </Avatar>
            <ThemeToggle />
          </div>
        </header>
        <div className="w-full min-w-0 max-w-full flex-1 p-4 md:p-6">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
