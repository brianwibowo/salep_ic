export type SalepRole = "marketing" | "sales";

export interface SalepSession {
  role: SalepRole;
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
  notes: string | null;
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
