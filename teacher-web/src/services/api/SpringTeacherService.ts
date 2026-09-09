import type { TeacherService } from './TeacherService';
import apiClient from './apiClient';
import { AuthTokenStore } from './AuthTokenStore';
import type { Assignment, Batch, Class, DashboardStats, MathType, Submission } from '../../types';

class SpringTeacherServiceImpl implements TeacherService {
  async login(email: string, password?: string): Promise<{ token: string }> {
    const res = await apiClient.post('/auth/login', { email, password });
    const { accessToken, refreshToken } = res.data;
    if (accessToken && refreshToken) {
      AuthTokenStore.setTokens(accessToken, refreshToken);
    }
    return { token: accessToken };
  }

  async getDashboard(): Promise<DashboardStats> {
    const res = await apiClient.get('/teacher/dashboard');
    const { metrics, recentBatches } = res.data;
    return {
      totalToday: metrics.totalToday || 0,
      completed: metrics.completed || 0,
      reviewRequired: metrics.reviewRequired || 0,
      recentBatches: recentBatches || [],
    };
  }

  async getClasses(): Promise<Class[]> {
    const res = await apiClient.get('/teacher/classes');
    return res.data;
  }

  async createAssignment(classId: string, title: string, mathType: MathType): Promise<Assignment> {
    const res = await apiClient.post('/teacher/assignments', { classId, title, mathType, status: 'ACTIVE' });
    return res.data;
  }

  async createBatch(assignmentId: string, imagesCount: number): Promise<Batch> {
    const res = await apiClient.post('/teacher/batches', { assignmentId, totalCount: imagesCount });
    return res.data;
  }

  async uploadImages(batchId: string, files: File[], mappings?: { fileIndex: number, studentId: string }[]): Promise<void> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('images', file);
    });
    if (mappings) {
      formData.append('association_metadata', JSON.stringify(mappings));
    }
    await apiClient.post(`/teacher/batches/${batchId}/submissions`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }

  async getBatchStatus(batchId: string): Promise<Batch> {
    const res = await apiClient.get(`/teacher/batches/${batchId}`);
    return res.data;
  }

  async getReviewQueue(batchId: string): Promise<Submission[]> {
    const res = await apiClient.get(`/teacher/batches/${batchId}/review`);
    return res.data;
  }

  async getSubmissionDetail(submissionId: string): Promise<Submission> {
    const res = await apiClient.get(`/teacher/submissions/${submissionId}`);
    return res.data;
  }

  async approveSubmission(submissionId: string): Promise<Submission> {
    const res = await apiClient.post(`/teacher/submissions/${submissionId}/approve`, { acceptProposal: true });
    return res.data;
  }

  async overrideSubmission(submissionId: string, newScore: number): Promise<Submission> {
    const res = await apiClient.post(`/teacher/submissions/${submissionId}/override`, { score: newScore, reason: "Teacher override" });
    return res.data;
  }

  async getMe(): Promise<any> {
    const res = await apiClient.get('/me');
    return res.data;
  }
}

export const SpringTeacherService = new SpringTeacherServiceImpl();
