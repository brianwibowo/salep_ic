import type { LeadFilters } from "@/services/salep-leads-service";

export type LeadSourcePreset = "all" | "social_media" | "spse";
export interface LeadFilterValues {
  status: string;
  source: string;
  salesStatus: string;
  assignment: string;
  dateMode: "range" | "month" | "year";
  dateFrom: string;
  dateTo: string;
  month: string;
  year: string;
}

export const createLeadFilters = (source: LeadSourcePreset = "all"): LeadFilterValues => ({
  status: "all", source, salesStatus: "all", assignment: "all",
  dateMode: "range", dateFrom: "", dateTo: "", month: "", year: "",
});

function validCalendarDate(value: string): boolean {
  if (!/^(19|[2-9]\d)\d{2}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  return parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month - 1 && parsed.getUTCDate() === day;
}

export function leadFilterError(value: LeadFilterValues): string | null {
  if (value.dateMode === "range") {
    if (value.dateFrom && value.dateTo && value.dateFrom > value.dateTo) return "Tanggal mulai tidak boleh melewati tanggal akhir.";
    if ([value.dateFrom, value.dateTo].some((date) => date && !validCalendarDate(date))) return "Gunakan tanggal yang valid dengan tahun minimal 1900.";
  }
  if (value.dateMode === "month" && value.month && !/^(19|[2-9]\d)\d{2}-(0[1-9]|1[0-2])$/.test(value.month)) return "Pilih bulan dan tahun yang valid (minimal 1900).";
  if (value.dateMode === "year" && value.year && !/^(19|[2-9]\d)\d{2}$/.test(value.year)) return "Masukkan tahun antara 1900 dan 9999.";
  return null;
}

export function leadQueryFilters(value: LeadFilterValues, isMarketing: boolean): LeadFilters {
  const filters: LeadFilters = {status: isMarketing ? value.status : "all", source: value.source, sales_status: value.salesStatus};
  if (isMarketing) {
    if (value.assignment.startsWith("user:")) filters.sales_user_id = value.assignment.slice(5);
    else if (value.assignment === "assigned" || value.assignment === "unassigned") filters.assignment_status = value.assignment;
    if (value.assignment === "unassigned") filters.status = "valid";
  }
  if (leadFilterError(value)) return filters;
  if (value.dateMode === "range") {
    filters.date_from = value.dateFrom || undefined;
    filters.date_to = value.dateTo || undefined;
  } else if (value.dateMode === "month" && value.month) {
    const [year, month] = value.month.split("-").map(Number);
    const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
    filters.date_from = `${value.month}-01`;
    filters.date_to = `${value.month}-${lastDay}`;
  } else if (value.dateMode === "year" && value.year) {
    filters.date_from = `${value.year}-01-01`;
    filters.date_to = `${value.year}-12-31`;
  }
  return filters;
}
