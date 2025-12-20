import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4003";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
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
  const response = await api.put(`/rates/${rateId}`, data);
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

export default api;
