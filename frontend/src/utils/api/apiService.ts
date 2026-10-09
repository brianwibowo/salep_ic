import { AxiosError, AxiosRequestConfig } from "axios";
import axiosInstance, { ApiResponse } from "./axiosInstance";

export type ClientResponse<T> = {
  status: boolean;
  message: string;
  data: T | undefined;
  statusCode?: number;
};

export class ApiServiceError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiServiceError";
    this.status = status;
  }
}

export function unwrapResponse<T>(response: ClientResponse<T>): T {
  if (!response.status || response.data === undefined) {
    throw new ApiServiceError(response.message, response.statusCode || 0);
  }

  return response.data;
}

const handleResponse = <T>(result: ApiResponse<T>): ClientResponse<T> => {
  // The existing services use the standard { success, statusCode, result }
  // envelope, while SALEP's FastAPI endpoints return the result directly.
  if (
    "success" in result &&
    "statusCode" in result &&
    "result" in result
  ) {
    if (result.success && result.statusCode >= 200 && result.statusCode < 300) {
      return {
        status: true,
        message: result.message || "Success",
        data: result.result,
        statusCode: result.statusCode,
      };
    }

    return {
      status: false,
      message: result.message || "Request failed",
      data: undefined,
      statusCode: result.statusCode,
    };
  }

  return {
    status: true,
    message: "Success",
    data: result as T,
  };
};

// Helper function untuk handle error
const handleError = (error: unknown): ClientResponse<never> => {
  if (error instanceof AxiosError) {
    const apiError = error.response?.data as
      | (ApiResponse & { detail?: string })
      | undefined;

    return {
      status: false,
      message:
        apiError?.message ||
        apiError?.detail ||
        error.message ||
        "Network error occurred",
      data: undefined,
      statusCode: error.response?.status,
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
