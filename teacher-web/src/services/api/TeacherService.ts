import type { Assignment, Batch, Class, DashboardStats, MathType, Submission } from '../../types';

export interface TeacherService {
  login(email: string, password?: string): Promise<{ token: string }>;
  getDashboard(): Promise<DashboardStats>;
  getClasses(): Promise<Class[]>;
  createAssignment(classId: string, title: string, mathType: MathType): Promise<Assignment>;
  createBatch(assignmentId: string, imagesCount: number): Promise<Batch>;
  uploadImages(batchId: string, files: File[]): Promise<void>;
  getBatchStatus(batchId: string): Promise<Batch>;
  getReviewQueue(batchId: string): Promise<Submission[]>;
  getSubmissionDetail(submissionId: string): Promise<Submission>;
  approveSubmission(submissionId: string): Promise<Submission>;
  overrideSubmission(submissionId: string, newScore: number): Promise<Submission>;
}
