const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_URL_INVENTORY = process.env.NEXT_PUBLIC_API_URL_INVENTORY;

const apiConfig = {
  service_user: `${API_URL}`,
  service_inventory: `${API_URL_INVENTORY}/api/inventory`,
};

export { apiConfig };
