"use client";

import { ColumnDef } from "@tanstack/react-table";
import {
  PaymentStatus,
  TransactionStatus,
  Transaction,
} from "@/types/transaction";
import { Button } from "@/components/ui/button";
import { MoreHorizontal } from "lucide-react";
import { formatCurrency, formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";

// ─── Badge Config ────────────────────────────────────────────────────────────

const paymentStatusConfig: Record<
  PaymentStatus,
  { label: string; className: string }
> = {
  // Hijau Emerald
  PAID: {
    label: "Paid",
    className:
      "bg-emerald-50 text-emerald-700 ring-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-400 dark:ring-emerald-700",
  },
  // Amber
  UNPAID: {
    label: "Unpaid",
    className:
      "bg-amber-50 text-amber-700 ring-amber-300 dark:bg-amber-900/30 dark:text-amber-400 dark:ring-amber-700",
  },
  // Biru
  PENDING: {
    label: "Pending",
    className:
      "bg-blue-50 text-blue-700 ring-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:ring-blue-700",
  },
  // Ungu
  REFUNDED: {
    label: "Refunded",
    className:
      "bg-purple-50 text-purple-700 ring-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:ring-purple-700",
  },
  // Merah
  FAILED: {
    label: "Failed",
    className:
      "bg-red-50 text-red-700 ring-red-300 dark:bg-red-900/30 dark:text-red-400 dark:ring-red-700",
  },
};

const statusConfig: Record<
  TransactionStatus,
  { label: string; className: string }
> = {
  COMPLETED: {
    label: "Completed",
    className:
      "bg-emerald-50 text-emerald-700 ring-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-400 dark:ring-emerald-700",
  },
  CANCELLED: {
    label: "Cancelled",
    className:
      "bg-zinc-100 text-zinc-600 ring-zinc-300 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-600",
  },
};

export const columns: ColumnDef<Transaction>[] = [
  {
    accessorKey: "invoice_number",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Invoice Number" />
    ),
  },
  {
    accessorKey: "transaction_date",
    header: "Transaction Date",
    cell: ({ row }) => {
      const date = row.getValue("transaction_date") as Date;
      return <span>{formatDate(date)}</span>;
    },
  },
  {
    accessorKey: "total_amount",
    header: "Total Amount",
    cell: ({ row }) => {
      const amount = row.getValue("total_amount") as number;
      return <span className="font-medium">{formatCurrency(amount)}</span>;
    },
  },
  {
    accessorKey: "payment_method",
    header: "Payment Method",
    cell: ({ row }) => (
      <span className="capitalize">{row.getValue("payment_method")}</span>
    ),
  },
  {
    accessorKey: "payment_status",
    header: "Payment Status",
    cell: ({ row }) => {
      const status = row.getValue("payment_status") as PaymentStatus;
      return <StatusBadge {...paymentStatusConfig[status]} />;
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as TransactionStatus;
      return <StatusBadge {...statusConfig[status]} />;
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const transaction = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => console.log(transaction)}
            >
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Edit</DropdownMenuItem>
            <DropdownMenuItem>Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
