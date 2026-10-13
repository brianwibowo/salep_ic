import { apiConfig } from "@/configs/api-config";
import { Get, Post, unwrapResponse } from "@/utils/api/apiService";
import type {
  InaprocSyncRequest,
  InaprocSyncResponse,
  InaprocTracksResponse,
} from "@/types/salep";

const BASE_URL = `${apiConfig.service_salep}/inaproc`;

export const sirupService = {
  sync: async (request: InaprocSyncRequest): Promise<InaprocSyncResponse> => {
    const res = await Post<InaprocSyncResponse, InaprocSyncRequest>(
      `${BASE_URL}/sync`,
      request,
    );
    return unwrapResponse(res);
  },

  tracks: async (): Promise<InaprocTracksResponse> => {
    const res = await Get<InaprocTracksResponse>(`${BASE_URL}/tracks`);
    return unwrapResponse(res);
  },
};
