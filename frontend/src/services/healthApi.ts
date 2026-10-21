import { apiClient } from '../lib/api';
import { HealthStatus } from '../types';

export const healthApi = {
  async getHealth(): Promise<HealthStatus> {
    const res = await apiClient.get<HealthStatus>('/health');
    return res.data;
  },
};
