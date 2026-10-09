const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
const API_URL_INVENTORY = process.env.NEXT_PUBLIC_API_URL_INVENTORY;

const apiConfig = {
  service_user: API_URL,
  service_salep: `${API_URL}/api/v1`,
  service_inventory: API_URL_INVENTORY
    ? `${API_URL_INVENTORY.replace(/\/$/, "")}/api/inventory`
    : `${API_URL}/api/inventory`,
};

export { apiConfig };
