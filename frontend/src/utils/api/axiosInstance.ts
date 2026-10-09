import axios, { AxiosError, AxiosInstance, AxiosResponse } from "axios";

export interface ApiResponse<T = unknown> {
  status: boolean;
  message: string;
  data: T | null;
}

export interface LegacyApiResponse<T = unknown> {
  success: boolean;
  statusCode: number;
  message?: string;
  result: T;
}

export type ApiResponsePayload<T> = ApiResponse<T> | LegacyApiResponse<T>;

interface ApiError {
  status: number;
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
}

const axiosInstance: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

axiosInstance.interceptors.request.use(
  (config) => {
    if (process.env.NODE_ENV === "development") {
      console.log("Request:", config.method?.toUpperCase(), config.url);
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  },
);

axiosInstance.interceptors.response.use(
  (response: AxiosResponse<ApiResponsePayload<unknown>>) => {
    if (process.env.NODE_ENV === "development") {
      console.log("Response:", response.status, response.config.url);
    }

    return response;
  },
  (error: AxiosError<ApiError>) => {
    const errorMessage =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      "Terjadi kesalahan";

    if (process.env.NODE_ENV === "development") {
      console.error("API Error:", {
        status: error.response?.status,
        message: errorMessage,
        url: error.config?.url,
      });
    }

    return Promise.reject(error);
  },
);

export default axiosInstance;
