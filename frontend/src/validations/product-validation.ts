import z from "zod";

export const ProductSchemaForm = z.object({
  product_code: z.string().min(1, "Product code is required"),
  product_name: z.string().min(1, "Product name is required"),
  category_id: z.string().min(1, "Category is required"),
  uom_id: z.string().min(1, "Unit of measure is required"),
  is_active: z.boolean(),
});

export type ProductForm = z.infer<typeof ProductSchemaForm>;