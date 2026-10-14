// export const numberFormatter = new Intl.NumberFormat("id-ID");

export function formatNumber(value: number | string, locale = "id-ID"): string {
  const num = typeof value === "string" ? Number(value) : value;
  return new Intl.NumberFormat(locale).format(num);
}

export function formatCurrency(
  amount: number,
  currency = "IDR",
  locale = "id-ID",
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString("id-ID", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
