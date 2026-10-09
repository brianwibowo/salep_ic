import { AxiosRequestConfig, AxiosError } from "axios";
import axiosInstance, { ApiResponse } from "./axiosInstance";

type ClientResponse<T> = {
  status: boolean;
  message: string;
  data: T | undefined;
};

const handleResponse = <T>(result: ApiResponse<T>): ClientResponse<T> => {
  // Success jika success true DAN statusCode 2xx
  if (result.success && result.statusCode >= 200 && result.statusCode < 300) {
    return {
      status: true,
      message: result.message || "Success",
      data: result.result,
    };
  }

  // Jika bukan 2xx, dianggap error
  return {
    status: false,
    message: result.message || "Request failed",
    data: undefined,
  };
};

// Helper function untuk handle error
const handleError = (error: unknown): ClientResponse<never> => {
  if (error instanceof AxiosError) {
    const apiError = error.response?.data as ApiResponse | undefined;

    return {
      status: false,
      message: apiError?.message || error.message || "Network error occurred",
      data: undefined,
    };
  }

  return {
    status: false,
    message: error instanceof Error ? error.message : "Unknown error occurred",
    data: undefined,
  };
};

export const Get = async <T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<ClientResponse<T>> => {
  try {
    const response = await axiosInstance.get<ApiResponse<T>>(url, config);
    return handleResponse(response.data);
  } catch (error) {
    return handleError(error);
  }
};

export const Post = async <T, D = any>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig,
): Promise<ClientResponse<T>> => {
  try {
    const response = await axiosInstance.post<ApiResponse<T>>(
      url,
      data,
      config,
    );
    return handleResponse(response.data);
  } catch (error) {
    return handleError(error);
  }
};

export const Put = async <T, D = any>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig,
): Promise<ClientResponse<T>> => {
  try {
    const response = await axiosInstance.put<ApiResponse<T>>(url, data, config);
    return handleResponse(response.data);
  } catch (error) {
    return handleError(error);
  }
};

export const Delete = async <T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<ClientResponse<T>> => {
  try {
    const response = await axiosInstance.delete<ApiResponse<T>>(url, config);
    return handleResponse(response.data);
  } catch (error) {
    return handleError(error);
  }
};

export const Patch = async <T, D = any>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig,
): Promise<ClientResponse<T>> => {
  try {
    const response = await axiosInstance.patch<ApiResponse<T>>(
      url,
      data,
      config,
    );
    return handleResponse(response.data);
  } catch (error) {
    return handleError(error);
  }
};
