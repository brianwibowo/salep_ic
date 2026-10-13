"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { parseSpseLeadContent } from "@/lib/spse-parser";
import type { Lead } from "@/types/salep";

interface SpseLeadDeleteDialogProps {
  lead: Lead | null;
  isDeleting: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function SpseLeadDeleteDialog({
  lead,
  isDeleting,
  onOpenChange,
  onConfirm,
}: SpseLeadDeleteDialogProps) {
  const parsed = lead ? parseSpseLeadContent(lead.content, lead.author_name) : null;
  const displayName = parsed?.title || lead?.author_name || "tanpa nama";

  return (
    <Dialog open={lead !== null} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-[5px] sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Hapus paket SPSE?</DialogTitle>
          <DialogDescription>
            Paket <span className="font-semibold text-foreground">“{displayName}”</span> akan dihapus permanen dari daftar prospek SPSE.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            className="rounded-[5px]"
            disabled={isDeleting}
            onClick={() => onOpenChange(false)}
          >
            Batal
          </Button>
          <Button
            type="button"
            variant="destructive"
            className="rounded-[5px]"
            disabled={!lead || isDeleting}
            onClick={onConfirm}
          >
            {isDeleting ? "Menghapus…" : "Hapus"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
