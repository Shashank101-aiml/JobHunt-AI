import { apiClient } from '../lib/api';
import {
  Application,
  PaginatedApplications,
  ApplicationEvent,
  DashboardStats,
} from '../types';

export const applicationsApi = {
  async getDashboardStats(): Promise<DashboardStats> {
    const res = await apiClient.get<DashboardStats>('/api/v1/dashboard/stats');
    return res.data;
  },

  async listApplications(params?: {
    status?: string;
    company?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedApplications> {
    const res = await apiClient.get<PaginatedApplications>('/api/v1/applications', { params });
    return res.data;
  },

  async getApplication(id: number): Promise<Application> {
    const res = await apiClient.get<Application>(`/api/v1/applications/${id}`);
    return res.data;
  },

  async createApplication(data: {
    job_id?: number;
    job_url?: string;
    job_text?: string;
    resume_id?: number;
    sync_execution?: boolean;
  }): Promise<Application> {
    const sync = data.sync_execution ?? true;
    const res = await apiClient.post<Application>(`/api/v1/apply?sync_execution=${sync}`, data);
    return res.data;
  },

  async updateApplicationStatus(id: number, status?: string, notes?: string): Promise<Application> {
    const params: Record<string, string> = {};
    if (status) params.status = status;
    if (notes !== undefined) params.notes = notes;
    const res = await apiClient.patch<Application>(`/api/v1/applications/${id}`, null, { params });
    return res.data;
  },

  async saveApplicationReview(
    id: number,
    data: { tailored_resume_text?: string; cover_letter?: string; notes?: string }
  ): Promise<Application> {
    const res = await apiClient.post<Application>(`/api/v1/applications/${id}/review`, data);
    return res.data;
  },

  async submitApplication(
    id: number,
    data: { submission_type: string; candidate_confirmed: boolean; notes?: string }
  ): Promise<Application> {
    const res = await apiClient.post<Application>(`/api/v1/applications/${id}/submit`, data);
    return res.data;
  },

  async getApplicationEvents(id: number): Promise<ApplicationEvent[]> {
    const res = await apiClient.get<ApplicationEvent[]>(`/api/v1/applications/${id}/events`);
    return res.data;
  },

  async downloadTailoredDocx(id: number, filename = `tailored_resume_app_${id}.docx`): Promise<void> {
    const res = await apiClient.get(`/api/v1/applications/${id}/download-docx`, {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
