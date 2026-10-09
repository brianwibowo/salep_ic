import { apiConfig } from "@/configs/api-config";
import { PaginationFilter } from "@/types/pagination";
import { Product } from "@/types/product";
import { Delete, Get, Post, Put } from "@/utils/api/apiService";
import { ProductForm } from "@/validations/product-validation";

const BASE_URL = apiConfig.service_inventory;

export interface ProductFilter extends PaginationFilter {
  // product_code?: string;
  // product_name?: string;
  // category_id?: string;
  // uom_id?: string;
  // is_active?: boolean;
  search?: string;
}

export const inventoryService = {
  getProducts: async (filters?: ProductFilter): Promise<Product[]> => {
    const params = new URLSearchParams();
    if (filters?.search) params.set("search", filters.search);
    if (filters?.page) params.set("page", String(filters.page));
    if (filters?.limit) params.set("limit", String(filters.limit));

    const query = params.toString();
    const res = await Get<{ data: Product[] }>(
      `${BASE_URL}/products${query ? `?${query}` : ""}`,
    );
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data.data;
  },

  getProductById: async (id: string): Promise<Product> => {
    const res = await Get<Product>(`${BASE_URL}/products/${id}`);
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  createProduct: async (data: ProductForm): Promise<Product> => {
    const res = await Post<Product, ProductForm>(`${BASE_URL}/products`, data);
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  updateProduct: async (
    id: string,
    data: Partial<ProductForm>,
  ): Promise<Product> => {
    const res = await Put<Product, Partial<ProductForm>>(
      `${BASE_URL}/products/${id}`,
      data,
    );
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  deleteProduct: async (id: string): Promise<void> => {
    const res = await Delete(`${BASE_URL}/products/${id}`);
    if (!res.status) throw new Error(res.message);
  },
};
