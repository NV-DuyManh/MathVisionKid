import { OperationType, BatchStatus } from './enums';

export interface Assignment {
  assignmentId: string;
  classId: string;
  teacherId: string;
  title: string;
  operationType: OperationType;
  maxScore: number;
  createdAt: string;
  status: string;
}

export interface Batch {
  batchId: string;
  assignmentId: string;
  teacherId: string;
  status: BatchStatus;
  totalCount: number;
  processedCount: number;
  reviewRequiredCount: number;
  failedCount: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}
