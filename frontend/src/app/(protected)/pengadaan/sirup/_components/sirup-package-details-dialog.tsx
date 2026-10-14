"use client";

import {
  Building2,
  Calendar,
  CheckCircle2,
  CircleDollarSign,
  Clock,
  Coins,
  ExternalLink,
  FileText,
  Layers,
  MapPin,
  Tag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { SirupPackage } from "@/types/salep";
import { formatCurrency, formatDate } from "@/utils/formatting/string";

interface SirupPackageDetailsDialogProps {
  packageData: SirupPackage | null;
  onOpenChange: (open: boolean) => void;
}

export function SirupPackageDetailsDialog({
  packageData,
  onOpenChange,
}: SirupPackageDetailsDialogProps) {
  if (!packageData) return null;

  return (
    <Dialog open={packageData !== null} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
              <Building2 className="size-3.5 text-[#9D0A0E]" />
              {packageData.organization || "Instansi Pemerintah"}
            </span>
            {packageData.satker && (
              <>
                <span>•</span>
                <span
                  className="truncate max-w-[280px]"
                  title={packageData.satker}
                >
                  {packageData.satker}
                </span>
              </>
            )}
            <span>•</span>
            <span className="font-semibold text-[#9D0A0E]">SiRUP INAPROC</span>
          </div>

          <DialogTitle className="text-lg font-bold leading-snug text-slate-900 dark:text-white">
            {packageData.package_name}
          </DialogTitle>

          <DialogDescription className="sr-only">
            Rincian paket pengadaan SiRUP {packageData.package_name}
          </DialogDescription>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Badge variant="outline" className="font-semibold">
              <Calendar className="mr-1 size-3 text-slate-500" />
              TA {packageData.fiscal_year}
            </Badge>

            <Badge variant="secondary" className="font-mono text-xs">
              Kode RUP: {packageData.external_id || packageData.rup_id || "—"}
            </Badge>

            {packageData.local_content_flag && (
              <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                <CheckCircle2 className="mr-1 size-3" />
                PDN (Produk Dalam Negeri)
              </Badge>
            )}

            {packageData.small_business_flag && (
              <Badge className="border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
                <CheckCircle2 className="mr-1 size-3" />
                UMK (Usaha Mikro & Kecil)
              </Badge>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Pagu Anggaran Card */}
          <div className="flex items-center justify-between rounded-lg border border-red-100 bg-red-50/50 p-4 dark:border-red-950 dark:bg-red-950/20">
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Total Pagu Anggaran
              </span>
              <p className="mt-0.5 text-2xl font-bold tracking-tight text-[#9D0A0E] dark:text-red-400">
                {packageData.budget_amount != null
                  ? formatCurrency(packageData.budget_amount)
                  : "—"}
              </p>
            </div>
            <div className="flex size-11 items-center justify-center rounded-full bg-red-100 text-[#9D0A0E] dark:bg-red-900/40 dark:text-red-300">
              <CircleDollarSign className="size-6" />
            </div>
          </div>

          {/* Rincian Parameter Pengadaan */}
          <dl className="grid gap-3 rounded-lg border bg-muted/20 p-4 text-xs sm:grid-cols-2">
            <DetailItem
              label="Jenis Pengadaan"
              value={packageData.procurement_type || "—"}
              icon={<Tag className="size-3 text-slate-400" />}
            />
            <DetailItem
              label="Metode Pemilihan"
              value={packageData.procurement_method || "—"}
              icon={<Layers className="size-3 text-slate-400" />}
            />
            <DetailItem
              label="Lokasi Pekerjaan"
              value={packageData.location || "—"}
              icon={<MapPin className="size-3 text-slate-400" />}
            />
            <DetailItem
              label="Satuan Kerja"
              value={packageData.satker || "—"}
              icon={<Building2 className="size-3 text-slate-400" />}
            />
            <DetailItem
              label="Terakhir Diperbarui / Terlihat"
              value={
                packageData.last_seen_at
                  ? formatDate(packageData.last_seen_at)
                  : "—"
              }
              icon={<Clock className="size-3 text-slate-400" />}
            />
            {packageData.first_seen_at && (
              <DetailItem
                label="Pertama Kali Disinkronkan"
                value={formatDate(packageData.first_seen_at)}
                icon={<Clock className="size-3 text-slate-400" />}
              />
            )}
          </dl>

          {/* Uraian Pekerjaan / Deskripsi jika ada */}
          {packageData.description && (
            <div className="space-y-1.5 rounded-lg border bg-muted/20 p-4 text-xs">
              <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
                <FileText className="size-3.5 text-slate-400" />
                Uraian / Deskripsi Pekerjaan
              </span>
              <p className="whitespace-pre-line text-muted-foreground leading-relaxed">
                {packageData.description}
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="flex flex-col gap-2 pt-2 sm:flex-row sm:justify-between sm:space-x-0">
          <Button
            type="button"
            variant="outline"
            className="text-xs"
            onClick={() => onOpenChange(false)}
          >
            Tutup
          </Button>

          <Button
            asChild
            className="gap-2 bg-[#9D0A0E] text-xs font-semibold text-white shadow hover:bg-[#7A080B]"
          >
            <a
              href={packageData.source_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Lihat di Portal SiRUP INAPROC
              <ExternalLink className="size-3.5" />
            </a>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DetailItem({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div>
      <dt className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
        {icon}
        {label}
      </dt>
      <dd className="mt-0.5 font-semibold text-slate-900 dark:text-slate-100">
        {value}
      </dd>
    </div>
  );
}
