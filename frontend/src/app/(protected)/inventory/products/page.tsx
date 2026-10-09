"use client";

import { useProducts } from "@/hooks/inventory/use-product";
import { useDebounce } from "@/hooks/use-debounce";
import { useState } from "react";
import DataTable from "./_components/data-table";
import { columns as productColumns } from "./_components/column";

export default function ProductsPage() {
  const [productSearch, setProductSearch] = useState("");
  const debouncedSearch = useDebounce(productSearch, 400);

  const { data: products = [], isLoading } = useProducts({
    search: debouncedSearch || undefined,
  });

  return (
    <>
      {/* Page Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Products</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage all your products
          </p>
        </div>
      </div>

      <DataTable
        columns={productColumns}
        data={products}
        searchValue={productSearch}
        onSearchChange={setProductSearch}
        isLoading={isLoading}
      />
    </>
  );
}
