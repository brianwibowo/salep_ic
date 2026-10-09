export type ProductStatus = "ACTIVE" | "INACTIVE";

export interface Product {
  product_id: number;
  category_id: number;
  uom_id: number;
  product_code: string;
  product_name: string;
  description: string;
  price: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  category: Category;
  uom: Uom;
  boms: Boms;
}

export interface Boms {
  boms_id: number;
  product_id: number;
  created_at: Date;
  updated_at: Date;
  bomItems: BOMItem[];
}

export interface BOMItem {
  bom_item_id: number;
  boms_id: number;
  raw_material_id: number;
  quantity: number;
  created_at: Date;
  updated_at: Date;
}

export interface Category {
  category_id: number;
  category_name: string;
  created_at: Date;
  updated_at: Date;
}

export interface Uom {
  uom_id: number;
  uom_code: string;
  created_at: Date;
  updated_at: Date;
}
