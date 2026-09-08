import type { Assignment, Batch, Class, DashboardStats, Submission } from '../../types';
import { SubmissionStatus, BatchStatus, MathType } from '../../types';
import type { TeacherService } from './TeacherService';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock Data
const MOCK_CLASSES: Class[] = [
  { id: 'c1', name: '4A', studentCount: 30 },
  { id: 'c2', name: '4B', studentCount: 28 },
];

const MOCK_BATCHES: Batch[] = [
  { id: 'b1', assignmentId: 'a1', className: '4A', assignmentTitle: 'Phép cộng có nhớ', totalImages: 25, processedCount: 25, reviewRequiredCount: 4, status: BatchStatus.COMPLETED, createdAt: new Date().toISOString() },
  { id: 'b2', assignmentId: 'a2', className: '4B', assignmentTitle: 'Phép trừ có mượn', totalImages: 28, processedCount: 28, reviewRequiredCount: 0, status: BatchStatus.COMPLETED, createdAt: new Date().toISOString() },
];

const MOCK_SUBMISSIONS: Record<string, Submission[]> = {
  'b1': [
    { id: 's1', batchId: 'b1', studentName: 'Học sinh A', imageUrl: 'https://placehold.co/400x600?text=Student+Image', status: SubmissionStatus.REVIEW_REQUIRED, recognitionConfidence: 96, diagnosisConfidence: 65, suggestedScore: 8, decision: 'INVALID', evidence: { position: 'Hàng chục', rule: 'Có nhớ khi cộng' }, recognizedText: '458\n+276\n----\n724' },
    { id: 's2', batchId: 'b1', studentName: 'Học sinh B', imageUrl: 'https://placehold.co/400x600?text=Ambiguous', status: SubmissionStatus.REVIEW_REQUIRED, recognitionConfidence: 45, diagnosisConfidence: 0, suggestedScore: 0, decision: 'UNCERTAIN', evidence: { position: 'Hàng trăm', rule: 'Không nhận diện được số' } },
    { id: 's3', batchId: 'b1', studentName: 'Học sinh C', imageUrl: 'https://placehold.co/400x600?text=Blurry', status: SubmissionStatus.QUALITY_ISSUE, recognitionConfidence: 10, diagnosisConfidence: 0, suggestedScore: 0, decision: 'INVALID', evidence: { position: 'Toàn bộ', rule: 'Ảnh quá mờ' } },
    { id: 's4', batchId: 'b1', studentName: 'Học sinh D', imageUrl: 'https://placehold.co/400x600?text=Student+Image', status: SubmissionStatus.REVIEW_REQUIRED, recognitionConfidence: 98, diagnosisConfidence: 85, suggestedScore: 9, decision: 'VALID', evidence: { position: 'Hàng đơn vị', rule: 'Kiểm tra lại nét chữ' }, recognizedText: '123\n+456\n----\n579' },
  ],
  'b2': []
};

class MockTeacherServiceImpl implements TeacherService {
  async login(_email: string, _password?: string): Promise<{ token: string }> {
    await delay(800);
    return { token: 'mock-jwt-token' };
  }

  async getDashboard(): Promise<DashboardStats> {
    await delay(500);
    return {
      totalToday: 53,
      completed: 49,
      reviewRequired: 4,
      recentBatches: MOCK_BATCHES,
    };
  }

  async getClasses(): Promise<Class[]> {
    await delay(300);
    return MOCK_CLASSES;
  }

  async createAssignment(classId: string, title: string, mathType: MathType): Promise<Assignment> {
    await delay(500);
    return {
      id: `a_${Date.now()}`,
      classId,
      title,
      mathType,
      createdAt: new Date().toISOString(),
    };
  }

  async createBatch(assignmentId: string, imagesCount: number): Promise<Batch> {
    await delay(600);
    const newBatch: Batch = {
      id: `b_${Date.now()}`,
      assignmentId,
      className: 'Lớp mới', // Simplification
      assignmentTitle: 'Bài tập mới',
      totalImages: imagesCount,
      processedCount: 0,
      reviewRequiredCount: 0,
      status: BatchStatus.PROCESSING,
      createdAt: new Date().toISOString(),
    };
    MOCK_BATCHES.unshift(newBatch);
    return newBatch;
  }

  async uploadImages(batchId: string, _files: File[], _mappings?: { fileIndex: number, studentId: string }[]): Promise<void> {
    await delay(1500); // simulate upload
    // In background, we simulate processing
    setTimeout(() => {
      const b = MOCK_BATCHES.find(x => x.id === batchId);
      if (b) {
        const total = b.totalImages || 0;
        b.status = BatchStatus.COMPLETED;
        b.processedCount = total;
        b.reviewRequiredCount = Math.min(2, total); // Mock some reviews
        MOCK_SUBMISSIONS[batchId] = [
          { id: `s_${Date.now()}_1`, batchId, studentName: 'Học sinh Mới 1', imageUrl: 'https://placehold.co/400x600', status: SubmissionStatus.REVIEW_REQUIRED, recognitionConfidence: 75, diagnosisConfidence: 60, suggestedScore: 7, decision: 'INVALID', evidence: { position: 'Tổng quát', rule: 'Nghi ngờ lỗi nhận dạng' } }
        ];
      }
    }, 4000);
  }

  async getBatchStatus(batchId: string): Promise<Batch> {
    await delay(300);
    const b = MOCK_BATCHES.find(x => x.id === batchId);
    if (!b) throw new Error("Not found");
    const total = b.totalImages || 0;
    // Simulate progression if processing
    if (b.status === BatchStatus.PROCESSING) {
      if (b.processedCount < total) {
        b.processedCount += Math.ceil(total / 4);
        if (b.processedCount >= total) {
          b.processedCount = total;
          b.status = BatchStatus.COMPLETED;
        }
      }
    }
    return { ...b };
  }

  async getReviewQueue(batchId: string): Promise<Submission[]> {
    await delay(600);
    const subs = MOCK_SUBMISSIONS[batchId] || [];
    return subs.filter(s => s.status === SubmissionStatus.REVIEW_REQUIRED || s.status === SubmissionStatus.QUALITY_ISSUE);
  }

  async getSubmissionDetail(submissionId: string): Promise<Submission> {
    await delay(400);
    for (const batch in MOCK_SUBMISSIONS) {
      const found = MOCK_SUBMISSIONS[batch].find(s => s.id === submissionId);
      if (found) return { ...found };
    }
    throw new Error("Not found");
  }

  async approveSubmission(submissionId: string): Promise<Submission> {
    await delay(500);
    return this.updateSubmissionStatus(submissionId, SubmissionStatus.AI_CONFIDENT);
  }

  async overrideSubmission(submissionId: string, newScore: number): Promise<Submission> {
    await delay(500);
    const sub = await this.updateSubmissionStatus(submissionId, SubmissionStatus.OVERRIDDEN);
    sub.teacherScore = newScore;
    return sub;
  }

  private async updateSubmissionStatus(id: string, newStatus: SubmissionStatus): Promise<Submission> {
    for (const batchId in MOCK_SUBMISSIONS) {
      const idx = MOCK_SUBMISSIONS[batchId].findIndex(s => s.id === id);
      if (idx !== -1) {
        MOCK_SUBMISSIONS[batchId][idx].status = newStatus;
        // update batch counters
        const batch = MOCK_BATCHES.find(b => b.id === batchId);
        if (batch && batch.reviewRequiredCount > 0) {
          batch.reviewRequiredCount--;
          if (batch.reviewRequiredCount === 0) {
            batch.status = BatchStatus.COMPLETED;
          }
        }
        return { ...MOCK_SUBMISSIONS[batchId][idx] };
      }
    }
    throw new Error("Not found");
  }
}

export const MockTeacherService = new MockTeacherServiceImpl();
