import { apiClient } from '../lib/api';
import { Resume } from '../types';

export const resumeApi = {
  async listResumes(): Promise<Resume[]> {
    const res = await apiClient.get<Resume[]>('/api/v1/resumes');
    return res.data;
  },

  async getActiveResume(): Promise<Resume> {
    const res = await apiClient.get<Resume>('/api/v1/resumes/active');
    return res.data;
  },

  async getResume(id: number): Promise<Resume> {
    const res = await apiClient.get<Resume>(`/api/v1/resumes/${id}`);
    return res.data;
  },

  async uploadResume(file: File, setActive = true): Promise<Resume> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<Resume>(`/api/v1/upload-resume?set_active=${setActive}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async activateResume(id: number): Promise<Resume> {
    const res = await apiClient.post<Resume>(`/api/v1/resumes/${id}/activate`);
    return res.data;
  },

  async deleteResume(id: number): Promise<{ status: string; id: number }> {
    const res = await apiClient.delete<{ status: string; id: number }>(`/api/v1/resumes/${id}`);
    return res.data;
  },
};
