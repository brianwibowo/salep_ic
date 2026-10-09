"use client";

import { useState } from "react";
import { useTransactions } from "@/hooks/finance/use-finance";
import { useDebounce } from "@/hooks/use-debounce";
import DataTable from "./_components/data-table";
import { columns as transactionColumns } from "./_components/columns";

export default function TransactionsPage() {
  const [invoiceSearch, setInvoiceSearch] = useState("");
  const debouncedSearch = useDebounce(invoiceSearch, 400);

  const { data: transactions = [], isLoading } = useTransactions({
    invoice_number: debouncedSearch || undefined,
  });

  return (
    <>
      {/* Page Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            Transactions
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage all your financial transactions
          </p>
        </div>
      </div>

      <DataTable
        columns={transactionColumns}
        data={transactions}
        searchValue={invoiceSearch}
        onSearchChange={setInvoiceSearch}
        isLoading={isLoading}
      />
    </>
  );
}
