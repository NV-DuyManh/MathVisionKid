import type { TeacherService } from './TeacherService';
import apiClient from './apiClient';
import { AuthTokenStore } from './AuthTokenStore';
import type { Assignment, Batch, Class, DashboardStats, MathType, Submission } from '../../types';

class SpringTeacherServiceImpl implements TeacherService {
  async login(email: string, password?: string): Promise<{ token: string }> {
    const res = await apiClient.post('/auth/login', { email, password });
    const { accessToken, refreshToken } = res.data;
    if (accessToken && refreshToken) {
      AuthTokenStore.setTokens(accessToken, refreshToken, true);
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
    return res.data.map((item: Class) => ({ ...item, id: item.classId }));
  }

  async getAssignments(): Promise<Assignment[]> {
    const res = await apiClient.get('/teacher/assignments');
    return res.data.map((item: Assignment & { operationType: string }) => ({
      ...item, mathType: item.operationType === 'ADDITION' ? 'VERTICAL_ADDITION'
        : item.operationType === 'SUBTRACTION' ? 'VERTICAL_SUBTRACTION' : item.operationType,
    }));
  }

  async getAssignmentRoster(assignmentId: string): Promise<{ id: string; name: string }[]> {
    const assignment = await apiClient.get(`/teacher/assignments/${encodeURIComponent(assignmentId)}`);
    const classroom = await apiClient.get(`/teacher/classes/${encodeURIComponent(assignment.data.classId)}`);
    return classroom.data.students.map((student: { userId: string; displayName: string }) => ({
      id: student.userId, name: student.displayName,
    }));
  }

  async createAssignment(classId: string, title: string, mathType: MathType): Promise<Assignment> {
    const res = await apiClient.post('/teacher/assignments', {
      classId,
      title,
      operationType: mathType,
      maxScore: 10,
    });
    return res.data;
  }

  async getBatches(): Promise<Batch[]> {
    const res = await apiClient.get('/teacher/batches');
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
      formData.append('manifest', JSON.stringify(mappings));
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
    // The backend returns owned submission IDs, not fabricated review cards.
    return Promise.all((res.data as string[]).map(id => this.getSubmissionDetail(id)));
  }

  async getSubmissionDetail(submissionId: string): Promise<Submission> {
    const res = await apiClient.get(`/teacher/submissions/${submissionId}`);
    const detail = res.data;
    const proposal = detail.gradeProposal;
    const score = proposal?.suggestedScore;
    const scale = proposal?.maxScore;
    // Use the same assignment scale and rounding as backend approval.
    const suggestedScore = Number.isFinite(score) && Number.isFinite(scale) && scale > 0
      && score >= 0 && score <= scale && Number.isFinite(detail.maxScore) && detail.maxScore > 0
      ? Math.round(score / scale * detail.maxScore) : undefined;
    const percent = (value: unknown) => typeof value === 'number' && value >= 0 && value <= 1
      ? value * 100 : undefined;
    const validation = detail.validation;
    return {
      ...detail,
      suggestedScore,
      recognitionConfidence: percent(detail.confidenceBundle?.recognition),
      diagnosisConfidence: percent(detail.confidenceBundle?.diagnosis),
      decision: validation?.diagnosisState === 'VALID' && validation?.isValid === true ? 'VALID'
        : validation?.diagnosisState === 'INVALID' && validation?.isValid === false ? 'INVALID'
        : 'UNCERTAIN',
    };
  }

  async approveSubmission(submissionId: string): Promise<Submission> {
    await apiClient.post(`/teacher/submissions/${submissionId}/approve`, { acceptProposal: true });
    return this.getSubmissionDetail(submissionId);
  }

  async overrideSubmission(submissionId: string, newScore: number, reason: string): Promise<Submission> {
    await apiClient.post(`/teacher/submissions/${submissionId}/override`, {
      score: newScore,
      reason,
    });
    return this.getSubmissionDetail(submissionId);
  }

  async getMe(): Promise<any> {
    const res = await apiClient.get('/me');
    return res.data;
  }
}

export const SpringTeacherService = new SpringTeacherServiceImpl();
