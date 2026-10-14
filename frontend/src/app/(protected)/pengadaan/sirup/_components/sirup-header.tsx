import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SirupHeaderProps {
  portalUrl: string;
}

export function SirupHeader({ portalUrl }: SirupHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <span>INAPROC</span>
          <span>•</span>
          <span className="text-[#9D0A0E]">
            Sistem Informasi Rencana Umum Pengadaan
          </span>
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          SiRUP — Rencana Umum Pengadaan
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
          Cari, saring, dan pantau paket SiRUP yang telah tersimpan di database SALEP.
        </p>
      </div>
      <Button
        asChild
        variant="outline"
        className="h-9 gap-2 rounded-md shadow-none"
      >
        <Link href={portalUrl} target="_blank" rel="noopener noreferrer">
          Buka Portal SiRUP <ExternalLink className="size-3.5" />
        </Link>
      </Button>
    </div>
  );
}
