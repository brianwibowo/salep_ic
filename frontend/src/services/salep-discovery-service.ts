import { salepApi } from "@/services/salep-api";
import { SchedulerStatus, SearchResult } from "@/types/salep";

export interface DiscoveryConfig {
  keywords: string[];
  sources: Array<"threads" | "linkedin">;
  limit_per_run: number;
}

export const salepDiscoveryService = {
  status: () => salepApi<SchedulerStatus>("/api/v1/scheduler/status"),
  saveConfig: (config: DiscoveryConfig) =>
    salepApi<SchedulerStatus>("/api/v1/scheduler/config", {
      method: "PUT",
      body: JSON.stringify(config),
    }),
  trigger: () =>
    salepApi<{ status: string; message: string }>("/api/v1/scheduler/trigger", {
      method: "POST",
    }),
  start: () =>
    salepApi<{ status: string }>("/api/v1/scheduler/start", { method: "POST" }),
  stop: () =>
    salepApi<{ status: string }>("/api/v1/scheduler/stop", { method: "POST" }),
  search: (input: {
    keywords: string[];
    start_date: string;
    end_date: string;
    sources: Array<"threads" | "linkedin" | "mock">;
    limit: number;
  }) =>
    salepApi<SearchResult>("/api/v1/search", {
      method: "POST",
      body: JSON.stringify(input),
    }),
};
