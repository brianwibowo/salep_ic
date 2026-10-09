import {
  LayoutDashboard,
  DollarSign,
  Package,
  ShoppingCart,
  Users,
} from "lucide-react";

interface NavItem {
  title: string;
  icon: React.ElementType;
  path?: string;
  children?: { title: string; path: string }[];
}

export const navigation: NavItem[] = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/dashboard",
  },
  {
    title: "Finance",
    icon: DollarSign,
    children: [
      { title: "Transactions", path: "/finance/transactions" },
      { title: "Expenses", path: "/finance/expenses" },
      { title: "Reports", path: "/finance/reports" },
    ],
  },
  {
    title: "Inventory",
    icon: Package,
    children: [
      { title: "Products", path: "/inventory/products" },
      { title: "Raw Materials", path: "/inventory/raw-materials" },
      { title: "Stock Alerts", path: "/inventory/alerts" },
    ],
  },
  {
    title: "POS Master Data",
    icon: ShoppingCart,
    children: [
      { title: "Categories", path: "/pos/categories" },
      { title: "Pricing", path: "/pos/pricing" },
      { title: "Recipes", path: "/pos/recipes" },
    ],
  },
  {
    title: "Employees",
    icon: Users,
    children: [
      { title: "User Management", path: "/employees/users" },
      { title: "Roles & Permissions", path: "/employees/roles" },
    ],
  },
];
