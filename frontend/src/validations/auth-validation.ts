import { z } from "zod";

export const LoginSchemaForm = z.object({
  role: z.enum(["marketing", "sales"]),
});

export type LoginForm = z.infer<typeof LoginSchemaForm>;
