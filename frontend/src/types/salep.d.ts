export type SalepRole = "marketing" | "sales" | "super_admin";

export interface SalepSession {
  role: SalepRole;
}

export interface SalesStatusLog {
  id: string;
  from_status: string;
  to_status: string;
  note: string;
  changed_by: string | null;
  changed_at: string;
}

export interface Lead {
  lead_id: string;
  source: string;
  source_url: string;
  author_name: string | null;
  author_profile_url: string | null;
  published_at: string | null;
  matched_keyword: string | null;
  content: string;
  is_potential_lead: boolean;
  intent: string;
  industry: string | null;
  needs: string[];
  pain_points: string[];
  recommended_services: Array<{
    product_id: string;
    product_name: string;
    match_score: number;
    reason: string;
  }>;
  lead_score: number;
  confidence: number;
  evidence: string[];
  analyzed_at: string;
  marketing_status: "pending" | "valid" | "invalid";
  sales_status: "Belum Dihubungi" | "Sedang Dihubungi" | "Closing" | "Batal";
  sales_status_logs?: SalesStatusLog[];
  created_at: string | null;
  notes: string | null;
  canonical_post_id?: string | null;
  deterministic_relevance_score?: number;
  deterministic_relevance_label?: string;
  deterministic_relevance_reason?: string | null;
  spam_label?: string;
  spam_score?: number;
  is_spam?: boolean;
  quality_flags?: string[];
}

export interface LeadStats {
  total: number;
  valid: number;
  pending: number;
  invalid: number;
  sales_new?: number;
  sales_in_progress?: number;
  sales_closed?: number;
}

export type FinalReason =
  | "contract_completed"
  | "contract_terminated"
  | "contract_stopped"
  | "tender_completed_no_contract"
  | "unknown_final_reason";

export interface FinalReasonSummary {
  reason: FinalReason;
  label: string;
  count: number;
  percentage: number;
  budget_amount: number;
  hps_amount: number;
}

export interface FinalAnalyticsSummary {
  fiscal_years: number[];
  total: number;
  total_budget_amount: number;
  total_hps_amount: number;
  by_reason: FinalReasonSummary[];
  by_year: Array<{ fiscal_year: number; count: number; budget_amount: number; hps_amount: number }>;
  by_track: Array<{ track: string; count: number; budget_amount: number; hps_amount: number }>;
  by_organization: Array<{ organization: string; count: number; budget_amount: number; hps_amount: number; high_priority_count: number }>;
  by_category: Array<{ category: string; label: string; count: number; budget_amount: number; hps_amount: number; high_priority_count: number; average_managed_service_fit: number }>;
  by_priority: Array<{ priority: string; count: number; budget_amount: number; hps_amount: number }>;
  recommendations: Array<{
    package_id: string;
    package_name: string;
    organization: string | null;
    service_category: string;
    service_category_label: string;
    sales_priority: string;
    sales_priority_score: number;
    sales_recommendation: string;
    source_url: string;
  }>;
}

export interface FinalPackage {
  package_id: string;
  source: "spse";
  track: string;
  external_id: string;
  package_name: string;
  organization: string | null;
  satker: string | null;
  location: string | null;
  fiscal_year: number;
  budget_amount: number | null;
  hps_amount: number | null;
  procurement_type: string | null;
  procurement_method: string | null;
  contract_type: string | null;
  current_stage_code: string | null;
  current_stage_label: string | null;
  contract_status: string | null;
  reason: FinalReason;
  reason_label: string;
  source_url: string;
  last_seen_at: string;
  service_category: string;
  service_category_label: string;
  category_evidence: string[];
  managed_service_fit: number;
  sales_priority: string;
  sales_priority_score: number;
  sales_recommendation: string;
}

export interface SchedulerStatus {
  enabled: boolean;
  is_running: boolean;
  cycle_running: boolean;
  interval_minutes: number;
  sources: string[];
  keywords: string[];
  limit_per_run: number;
  last_run_at: string | null;
  next_run_at: string | null;
  total_cycles_executed: number;
  total_leads_found: number;
  total_leads_qualified: number;
  last_error: string | null;
}

export interface SearchResult {
  query_id: string;
  total_found: number;
  total_analyzed: number;
  qualified: number;
  leads: Lead[];
}

export interface TenderStage {
  no: string;
  stage: string;
  start: string;
  end: string;
  changes?: string;
  status: "completed" | "active" | "upcoming";
}

export interface TenderScheduleResponse {
  tender_id: string;
  source_url: string;
  current_stage: string;
  stages: TenderStage[];
  title?: string;
  instansi?: string;
  note?: string;
}

export interface InaprocSyncStats {
  run_id: string;
  source: string;
  track: string;
  seen: number;
  inserted: number;
  updated: number;
  rejected: number;
  unchanged: number;
}

export interface InaprocSyncRequest {
  fiscal_years: number[];
  keyword?: string;
  limit?: number;
  fetch_details?: boolean;
  tracks?: Array<"sirup" | "tender" | "non_tender" | "pencatatan_non_tender" | "swakelola" | "darurat">;
}

export interface InaprocSyncResponse {
  results: InaprocSyncStats[];
}

export interface InaprocTracksResponse {
  sirup: string;
  spse: Record<string, string>;
}

export type SirupSort = "newest" | "oldest" | "budget_desc" | "budget_asc";

export interface SirupPackage {
  package_id: string;
  external_id: string;
  rup_id: string | null;
  package_name: string;
  description: string | null;
  organization: string | null;
  satker: string | null;
  location: string | null;
  procurement_type: string | null;
  procurement_method: string | null;
  fiscal_year: number;
  budget_amount: number | null;
  local_content_flag: boolean | null;
  small_business_flag: boolean | null;
  source_url: string;
  created_at?: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
}

export interface SirupFilters {
  fiscal_year?: number;
  search?: string;
  procurement_type?: string;
  procurement_method?: string;
  date_from?: string;
  date_to?: string;
  sort?: SirupSort;
}

export interface SirupListResponse {
  items: SirupPackage[];
  pagination: { page: number; limit: number; total: number; pages: number };
  summary: { total: number; total_budget_amount: number };
  facets: {
    fiscal_years: number[];
    procurement_types: string[];
    procurement_methods: string[];
  };
  filters: SirupFilters;
}
