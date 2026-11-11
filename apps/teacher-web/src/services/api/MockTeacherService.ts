import type { Assignment, Batch, Class, DashboardStats, Submission } from '../../types';
import { SubmissionStatus, BatchStatus, MathType } from '../../types';
import type { TeacherService } from './TeacherService';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const pendingReview = new Set(['REVIEW_REQUIRED', 'NEEDS_RETAKE', 'NEEDS_CONFIRMATION', 'PROPOSED_GRADE', 'FEEDBACK_READY']);

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
    { id: 's3', batchId: 'b1', studentName: 'Học sinh C', imageUrl: 'https://placehold.co/400x600?text=Blurry', status: SubmissionStatus.NEEDS_RETAKE, recognitionConfidence: 10, diagnosisConfidence: 0, suggestedScore: 0, decision: 'INVALID', evidence: { position: 'Toàn bộ', rule: 'Ảnh quá mờ' } },
    { id: 's4', batchId: 'b1', studentName: 'Học sinh D', imageUrl: 'https://placehold.co/400x600?text=Student+Image', status: SubmissionStatus.REVIEW_REQUIRED, recognitionConfidence: 98, diagnosisConfidence: 85, suggestedScore: 9, decision: 'VALID', evidence: { position: 'Hàng đơn vị', rule: 'Kiểm tra lại nét chữ' }, recognizedText: '123\n+456\n----\n579' },
  ],
  'b2': []
};

const MOCK_ASSIGNMENTS: Assignment[] = [
  { id: 'a1', assignmentId: 'a1', classId: 'c1', title: 'Phép cộng có nhớ trong phạm vi 1000', mathType: MathType.VERTICAL_ADDITION, createdAt: new Date().toISOString(), status: 'ACTIVE' },
  { id: 'a2', assignmentId: 'a2', classId: 'c2', title: 'Phép trừ có mượn chữ số hàng chục', mathType: MathType.VERTICAL_SUBTRACTION, createdAt: new Date().toISOString(), status: 'ACTIVE' },
];

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

  async getClassDetail(classId: string) {
    const classroom = MOCK_CLASSES.find(item => item.id === classId);
    if (!classroom) throw new Error('Không tìm thấy lớp học');
    const students = Array.from({ length: classroom.studentCount }, (_, index) => ({
      id: `st_${index + 1}`, name: `Học sinh ${index + 1} (${classroom.name})`,
    }));
    return { ...classroom, students };
  }

  async getAssignments(): Promise<Assignment[]> {
    await delay(300);
    return MOCK_ASSIGNMENTS;
  }

  async getAssignmentRoster(assignmentId: string): Promise<{ id: string; name: string }[]> {
    const assignment = MOCK_ASSIGNMENTS.find(item => (item.assignmentId || item.id) === assignmentId);
    return assignment ? (await this.getClassDetail(assignment.classId)).students : [];
  }

  async createAssignment(classId: string, title: string, mathType: MathType, maxScore = 10): Promise<Assignment> {
    await delay(500);
    const newAssignment: Assignment = {
      id: `a_${Date.now()}`,
      assignmentId: `a_${Date.now()}`,
      classId,
      title,
      mathType,
      maxScore,
      createdAt: new Date().toISOString(),
      status: 'ACTIVE',
    };
    MOCK_ASSIGNMENTS.unshift(newAssignment);
    return newAssignment;
  }

  async getBatches(): Promise<Batch[]> {
    await delay(300);
    return MOCK_BATCHES;
  }

  async createBatch(assignmentId: string): Promise<Batch> {
    await delay(600);
    const newBatch: Batch = {
      id: `b_${Date.now()}`,
      assignmentId,
      className: 'Lớp mới', // Simplification
      assignmentTitle: 'Bài tập mới',
      totalImages: 0,
      processedCount: 0,
      reviewRequiredCount: 0,
      status: BatchStatus.CREATED,
      createdAt: new Date().toISOString(),
    };
    MOCK_BATCHES.unshift(newBatch);
    return newBatch;
  }

  async uploadImages(batchId: string, files: File[], _mappings?: { fileIndex: number, studentId: string }[], onProgress?: (percentage: number) => void): Promise<void> {
    if (onProgress) {
      onProgress(30);
      await delay(400);
      onProgress(70);
      await delay(500);
      onProgress(100);
    }
    await delay(600); // simulate upload
    const batch = MOCK_BATCHES.find(item => item.id === batchId);
    if (batch) {
      batch.totalImages = files.length;
      batch.status = BatchStatus.PROCESSING;
    }
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
    const submissions = (MOCK_SUBMISSIONS[batchId] || []).flatMap(submission =>
      submission.id ? [{ submissionId: submission.id, studentName: submission.studentName, status: submission.status }] : []);
    return {
      ...b, submissions,
      pendingReviewCount: submissions.filter(s => pendingReview.has(s.status)).length,
      finalizedCount: submissions.filter(s => s.status === 'TEACHER_APPROVED' || s.status === 'TEACHER_OVERRIDDEN').length,
    };
  }

  async getReviewQueue(batchId: string): Promise<Submission[]> {
    await delay(600);
    const subs = MOCK_SUBMISSIONS[batchId] || [];
    return subs.filter(s => pendingReview.has(s.status));
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
    return this.updateSubmissionStatus(submissionId, SubmissionStatus.TEACHER_APPROVED);
  }

  async overrideSubmission(submissionId: string, newScore: number, reason: string): Promise<Submission> {
    await delay(500);
    return this.updateSubmissionStatus(submissionId, SubmissionStatus.TEACHER_OVERRIDDEN, newScore, reason);
  }

  private async updateSubmissionStatus(id: string, newStatus: SubmissionStatus, score?: number, reason?: string): Promise<Submission> {
    for (const [batchId, submissions] of Object.entries(MOCK_SUBMISSIONS)) {
      const submission = submissions.find(item => item.id === id);
      if (!submission) continue;
      submission.status = newStatus;
      submission.teacherScore = score ?? submission.suggestedScore;
      submission.teacherReason = reason;
      const batch = MOCK_BATCHES.find(item => item.id === batchId);
      if (batch) batch.pendingReviewCount = submissions.filter(item => pendingReview.has(item.status)).length;
      return { ...submission };
    }
    throw new Error("Not found");
  }
}

export const MockTeacherService = new MockTeacherServiceImpl();
