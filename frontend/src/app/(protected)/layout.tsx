"use client";

import { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
import { useSession } from "@/hooks/auth/use-auth";
import { SalepApiError } from "@/services/salep-api";

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const session = useSession();

  useEffect(() => {
    if (session.error instanceof SalepApiError && session.error.status === 401) {
      router.replace("/login");
    }
  }, [router, session.error]);

  useEffect(() => {
    if (session.data?.role === "sales" && pathname.startsWith("/discovery")) {
      router.replace("/dashboard");
    }
  }, [pathname, router, session.data?.role]);

  if (session.isPending || (session.error instanceof SalepApiError && session.error.status === 401)) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Memeriksa sesi SALEP…</div>;
  }

  if (session.isError || !session.data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="font-medium">Tidak dapat menghubungi backend SALEP.</p>
        <p className="max-w-md text-sm text-muted-foreground">{session.error?.message}</p>
        <Button variant="outline" onClick={() => session.refetch()}>Coba lagi</Button>
      </div>
    );
  }

  if (session.data.role === "sales" && pathname.startsWith("/discovery")) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Membuka ringkasan leads…</div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <AppSidebar role={session.data.role} />
      <div className="pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-card px-6 shadow-sm">
          <div>
            <p className="text-sm font-medium">SALEP</p>
            <p className="text-xs capitalize text-muted-foreground">Sesi {session.data.role}</p>
          </div>
          <ThemeToggle />
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
