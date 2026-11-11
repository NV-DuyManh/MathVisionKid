import type { TeacherService } from './TeacherService';
import apiClient from './apiClient';
import { AuthTokenStore } from './AuthTokenStore';
import type { Assignment, Batch, Class, ClassDetail, DashboardStats, Evidence, EvidenceItem, MathType, ReviewQueueItem, Submission } from '../../types';

type RawReviewMetrics = Pick<Submission, 'maxScore' | 'confidenceBundle' | 'validation'> & {
  gradeProposal?: { suggestedScore?: number; maxScore?: number };
  evidence?: unknown;
};

function evidenceText(value: unknown): string | undefined {
  return typeof value === 'string' ? value.trim() || undefined : undefined;
}

function normalizeEvidence(value: unknown): Evidence | undefined {
  if (!value || typeof value !== 'object') return undefined;
  const evidence = value as Record<string, unknown>;
  const items = Array.isArray(evidence.items) ? evidence.items.flatMap((entry: unknown): EvidenceItem[] => {
    if (!entry || typeof entry !== 'object') return [];
    const item = entry as Record<string, unknown>;
    const description = evidenceText(item.description);
    const placeValue = evidenceText(item.placeValue);
    const observedText = evidenceText(item.observedText);
    return description || placeValue || observedText ? [{ description, placeValue, observedText }] : [];
  }) : [];
  const [first] = items;
  if (first) return { items, rule: first.description, position: first.placeValue };

  const rule = evidenceText(evidence.rule);
  const position = evidenceText(evidence.position);
  return rule || position ? { rule, position } : undefined;
}

function normalizeReviewMetrics(detail: RawReviewMetrics) {
  const score = detail.gradeProposal?.suggestedScore;
  const scale = detail.gradeProposal?.maxScore;
  const maxScore = detail.maxScore;
  // Use the same assignment scale and rounding as backend approval.
  const suggestedScore = typeof score === 'number' && typeof scale === 'number' && Number.isFinite(scale) && scale > 0
    && score >= 0 && score <= scale && typeof maxScore === 'number' && Number.isFinite(maxScore) && maxScore > 0
    ? Math.round(score / scale * maxScore) : undefined;
  const percent = (value: unknown) => typeof value === 'number' && value >= 0 && value <= 1 ? value * 100 : undefined;
  const validation = detail.validation;
  return {
    evidence: normalizeEvidence(detail.evidence),
    suggestedScore,
    recognitionConfidence: percent(detail.confidenceBundle?.recognition),
    diagnosisConfidence: percent(detail.confidenceBundle?.diagnosis),
    decision: validation?.diagnosisState === 'VALID' && validation?.isValid === true ? 'VALID'
      : validation?.diagnosisState === 'INVALID' && validation?.isValid === false ? 'INVALID'
      : 'UNCERTAIN',
  };
}

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
    const { todayTotal, processedCount, reviewRequiredCount, recentBatches } = res.data ?? {};
    if (![todayTotal, processedCount, reviewRequiredCount].every(value => Number.isSafeInteger(value) && value >= 0)
      || !Array.isArray(recentBatches)) {
      throw new Error('Dữ liệu tổng quan chưa hợp lệ. Vui lòng thử lại.');
    }
    return {
      totalToday: todayTotal,
      completed: processedCount,
      reviewRequired: reviewRequiredCount,
      recentBatches,
    };
  }

  async getClasses(): Promise<Class[]> {
    const res = await apiClient.get('/teacher/classes');
    return res.data.map((item: Class) => ({ ...item, id: item.classId }));
  }

  async getClassDetail(classId: string): Promise<ClassDetail> {
    const { data } = await apiClient.get(`/teacher/classes/${encodeURIComponent(classId)}`);
    return {
      ...data,
      id: data.classId,
      students: data.students.map((student: { userId: string; displayName: string }) => ({
        id: student.userId, name: student.displayName,
      })),
    };
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
    const classroom = await this.getClassDetail(assignment.data.classId);
    return classroom.students;
  }

  async createAssignment(classId: string, title: string, mathType: MathType, maxScore: number = 10): Promise<Assignment> {
    const res = await apiClient.post('/teacher/assignments', {
      classId,
      title,
      operationType: mathType,
      maxScore,
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

  async uploadImages(
    batchId: string,
    files: File[],
    mappings?: { fileIndex: number, studentId: string }[],
    onProgress?: (percentage: number) => void
  ): Promise<void> {
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
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && typeof progressEvent.total === 'number' && Number.isFinite(progressEvent.total)
            && progressEvent.total > 0 && Number.isFinite(progressEvent.loaded)) {
          const percent = Math.min(100, Math.max(0, Math.round((progressEvent.loaded * 100) / progressEvent.total)));
          onProgress(percent);
        }
      }
    });
  }

  async getBatchStatus(batchId: string): Promise<Batch> {
    const res = await apiClient.get(`/teacher/batches/${batchId}`);
    return res.data;
  }

  async getReviewQueue(batchId: string): Promise<ReviewQueueItem[]> {
    const res = await apiClient.get<(ReviewQueueItem & RawReviewMetrics)[]>(`/teacher/batches/${encodeURIComponent(batchId)}/review-summary`);
    return res.data.map(detail => ({ ...detail, ...normalizeReviewMetrics(detail) }));
  }

  async getSubmissionDetail(submissionId: string): Promise<Submission> {
    const res = await apiClient.get(`/teacher/submissions/${submissionId}`);
    return { ...res.data, ...normalizeReviewMetrics(res.data) };
  }

  async retakeSubmission(submissionId: string, image: Blob): Promise<void> {
    const body = new FormData();
    body.append('image', image, 'anh-chup-lai.jpg');
    await apiClient.post(`/teacher/submissions/${encodeURIComponent(submissionId)}/retake`, body);
  }

  async retrySubmissionProcessing(submissionId: string): Promise<void> {
    await apiClient.post(`/teacher/submissions/${encodeURIComponent(submissionId)}/retry-processing`);
  }

  async approveSubmission(submissionId: string): Promise<void> {
    await apiClient.post(`/teacher/submissions/${submissionId}/approve`, { acceptProposal: true });
  }

  async overrideSubmission(submissionId: string, newScore: number, reason: string, imageLegible?: boolean): Promise<void> {
    await apiClient.post(`/teacher/submissions/${submissionId}/override`, {
      score: newScore,
      reason,
      ...(imageLegible === true ? { imageLegible: true } : {}),
    });
  }

  async getMe(): Promise<any> {
    const res = await apiClient.get('/me');
    return res.data;
  }
}

export const SpringTeacherService = new SpringTeacherServiceImpl();
