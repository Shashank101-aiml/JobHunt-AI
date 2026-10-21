import { apiClient } from '../lib/api';
import { MatchEvaluationResponse } from '../types';

export const matchingApi = {
  async evaluateMatch(data: {
    resume_id?: number;
    job_id?: number;
    job_url?: string;
    job_text?: string;
  }): Promise<MatchEvaluationResponse> {
    const res = await apiClient.post<MatchEvaluationResponse>('/api/v1/match/evaluate', data);
    return res.data;
  },
};
