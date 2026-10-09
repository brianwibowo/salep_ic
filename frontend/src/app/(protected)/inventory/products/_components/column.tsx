import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Product, ProductStatus } from "@/types/product";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";
import { size } from "zod";

const statusConfig: Record<
  ProductStatus,
  { label: string; className: string }
> = {
  // Hijau Emerald
  ACTIVE: {
    label: "Active",
    className:
      "bg-emerald-50 text-emerald-700 ring-emerald-300 dark:bg-emerald-900/30 dark:text-emerald-400 dark:ring-emerald-700",
  },
  // Merah
  INACTIVE: {
    label: "Inactive",
    className:
      "bg-red-50 text-red-700 ring-red-300 dark:bg-red-900/30 dark:text-red-400 dark:ring-red-700",
  },
};

export const columns: ColumnDef<Product>[] = [
  {
    accessorKey: "product_code",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="cursor-pointer"
      >
        Product Code
        <ArrowUpDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
    ),
  },
  {
    accessorKey: "product_name",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="cursor-pointer"
      >
        Product Name
        <ArrowUpDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
    ),
  },
  {
    accessorKey: "category.category_name",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="cursor-pointer"
      >
        Category
        <ArrowUpDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
    ),
  },
  {
    accessorKey: "uom.uom_code",
    header: "UOM",
  },
  {
    accessorKey: "price",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="cursor-pointer"
      >
        Price
        <ArrowUpDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
    ),
    cell: ({ row }) => {
      const price = row.getValue("price") as number;
      return <span>{formatCurrency(price)}</span>;
    },
  },
  {
    accessorKey: "is_active",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="cursor-pointer"
      >
        Active
        <ArrowUpDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
    ),
    cell: ({ row }) => {
      const isActive = row.getValue("is_active") as boolean;
      return (
        <StatusBadge {...statusConfig[isActive ? "ACTIVE" : "INACTIVE"]} />
      );
    },
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="cursor-pointer"
      >
        Created At
        <ArrowUpDown className="ml-2 h-4 w-4 shrink-0" />
      </Button>
    ),
    cell: ({ row }) => {
      const date = row.getValue("created_at") as Date;
      return <span>{formatDate(date)}</span>;
    },
  },
];
