export type PaymentStatus =
  | "UNPAID"
  | "PENDING"
  | "PAID"
  | "REFUNDED"
  | "FAILED";
export type TransactionStatus = "COMPLETED" | "CANCELLED";

export interface Transaction {
  id: string;
  header_transaction_id: number;
  invoice_number: string;
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  payment_method: string;
  payment_status: PaymentStatus;
  cash_received: number;
  change_amount: number;
  status: Status;
  transaction_date: Date;
  details: Detail[];
}

export interface Detail {
  detail_transaction_id: number;
  line_number: number;
  product_id: number;
  product_code: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  subtotal: number;
}
