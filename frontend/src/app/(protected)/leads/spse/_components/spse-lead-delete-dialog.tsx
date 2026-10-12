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
  return (
    <Dialog open={lead !== null} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-[5px] sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Hapus paket SPSE?</DialogTitle>
          <DialogDescription>
            Paket {lead?.author_name || "tanpa nama"} akan dihapus permanen dari database SALEP.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={isDeleting}
            onClick={() => onOpenChange(false)}
          >
            Batal
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={!lead || isDeleting}
            onClick={onConfirm}
          >
            {isDeleting ? "Menghapus…" : "Hapus paket"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
