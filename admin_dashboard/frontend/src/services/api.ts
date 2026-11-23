import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4005";

// Optional: must match ADMIN_API_KEY on the backend. NEXT_PUBLIC_* values are
// embedded in the browser bundle, so this guards a local/demo deployment only.
const API_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  },
});

export const getStats = async () => {
  const response = await api.get("/stats");
  return response.data;
};

export const getRates = async (hotel?: string) => {
  const response = await api.get("/rates", { params: { hotel } });
  return response.data;
};

export const getPriceItems = async (hotel?: string) => {
  const response = await api.get("/price-items", { params: { hotel } });
  return response.data;
};

export const updateRate = async (rateId: string, data: any) => {
  const response = await api.put(`/rates/${encodeURIComponent(rateId)}`, data);
  return response.data;
};

export const getAnalytics = async () => {
  const response = await api.get("/analytics");
  return response.data;
};

export const getContacts = async () => {
  const response = await api.get("/contacts");
  return response.data;
};

export const sendMessage = async (message: string) => {
  const response = await api.post("/chat", { message });
  return response.data;
};

export const getAuditLog = async (limit: number = 50) => {
  const response = await api.get("/audit-log", { params: { limit } });
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await api.get("/system-status");
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export default api;

