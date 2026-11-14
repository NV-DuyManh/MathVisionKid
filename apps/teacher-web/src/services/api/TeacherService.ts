import type { Assignment, Batch, Class, ClassDetail, DashboardStats, MathType, ReviewQueueItem, Submission } from '../../types';

export type AssignmentWorkflow = Assignment & { prompt: string; instructions?: string; status: 'DRAFT' | 'PUBLISHED'; recipientCount: number; publishedAt?: string };

export interface TeacherService {
  login(email: string, password?: string): Promise<{ token: string }>;
  getDashboard(): Promise<DashboardStats>;
  getClasses(): Promise<Class[]>;
  getClassDetail(classId: string): Promise<ClassDetail>;
  getAssignments(): Promise<Assignment[]>;
  getAssignmentRoster(assignmentId: string): Promise<{ id: string; name: string }[]>;
  createAssignment(classId: string, title: string, mathType: MathType, maxScore?: number, creationRequestId?: string): Promise<Assignment>;
  listClassAssignments(classId: string): Promise<AssignmentWorkflow[]>;
  saveAssignmentDraft(input: { assignmentId?: string; classId: string; title: string; prompt: string; instructions: string; mathType: MathType; maxScore: number; creationRequestId: string }): Promise<AssignmentWorkflow>;
  publishAssignment(assignmentId: string): Promise<AssignmentWorkflow>;
  getBatches(): Promise<Batch[]>;
  createBatch(assignmentId: string, imagesCount: number, creationRequestId?: string): Promise<Batch>;
  uploadImages(batchId: string, files: File[], mappings?: { fileIndex: number, studentId: string }[], onProgress?: (percentage: number) => void): Promise<void>;
  getBatchStatus(batchId: string): Promise<Batch>;
  getReviewQueue(batchId: string): Promise<ReviewQueueItem[]>;
  getSubmissionDetail(submissionId: string): Promise<Submission>;
  retakeSubmission(submissionId: string, image: Blob): Promise<void>;
  retrySubmissionProcessing(submissionId: string): Promise<void>;
  approveSubmission(submissionId: string): Promise<void>;
  overrideSubmission(submissionId: string, newScore: number, reason: string, imageLegible?: boolean): Promise<void>;
}
