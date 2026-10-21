import { apiClient } from '../lib/api';
import { Job, PaginatedJobs } from '../types';

export const jobsApi = {
  async listJobs(params?: {
    search?: string;
    location?: string;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedJobs> {
    const res = await apiClient.get<PaginatedJobs>('/api/v1/jobs', { params });
    return res.data;
  },

  async getJob(id: number): Promise<Job> {
    const res = await apiClient.get<Job>(`/api/v1/jobs/${id}`);
    return res.data;
  },

  async createManualJob(data: {
    title?: string;
    company?: string;
    location?: string;
    employment_type?: string;
    description_text: string;
    source_url?: string;
  }): Promise<Job> {
    const res = await apiClient.post<Job>('/api/v1/jobs/manual', data);
    return res.data;
  },

  async scrapeJob(url: string): Promise<Job> {
    const res = await apiClient.post<Job>('/api/v1/jobs/scrape', { url });
    return res.data;
  },
};
