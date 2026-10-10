import { z } from "zod";

export const DiscoveryConfigSchema = z.object({
  keywords: z.array(z.string().trim().min(1).max(150)).min(1).max(40),
  sources: z.array(z.enum(["threads", "linkedin"])).min(1),
  limit_per_run: z.number().int().min(1).max(50),
});

export type DiscoveryConfig = z.infer<typeof DiscoveryConfigSchema>;

export const ManualSearchSchema = z.object({
  keywords: z.array(z.string().trim().min(1)).min(1),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
  sources: z.array(z.enum(["threads", "linkedin", "mock"])).min(1),
  limit: z.number().int().min(1).max(100),
});

export type ManualSearchInput = z.infer<typeof ManualSearchSchema>;
