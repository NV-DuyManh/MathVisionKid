export interface Teacher {
  id: string;
  name: string;
  email: string;
}

export interface Class {
  id: string;
  name: string;
  studentCount: number;
}

export type MathType = 'VERTICAL_ADDITION' | 'VERTICAL_SUBTRACTION';
export const MathType = {
  VERTICAL_ADDITION: 'VERTICAL_ADDITION',
  VERTICAL_SUBTRACTION: 'VERTICAL_SUBTRACTION'
} as const;

export interface Assignment {
  id: string;
  classId: string;
  title: string;
  mathType: MathType;
  createdAt: string;
}

export type SubmissionStatus = 'CREATED' | 'IMAGE_UPLOADED' | 'PROCESSING' | 'NEEDS_CONFIRMATION' | 'NEEDS_RETAKE' | 'CROP_REQUIRED' | 'FEEDBACK_READY' | 'REVIEW_REQUIRED' | 'OUT_OF_SCOPE' | 'TEACHER_APPROVED' | 'TEACHER_OVERRIDDEN' | 'FAILED' | 'AI_CONFIDENT' | 'QUALITY_ISSUE' | 'OVERRIDDEN';

export const SubmissionStatus = {
  CREATED: 'CREATED',
  IMAGE_UPLOADED: 'IMAGE_UPLOADED',
  PROCESSING: 'PROCESSING',
  NEEDS_CONFIRMATION: 'NEEDS_CONFIRMATION',
  NEEDS_RETAKE: 'NEEDS_RETAKE',
  CROP_REQUIRED: 'CROP_REQUIRED',
  FEEDBACK_READY: 'FEEDBACK_READY',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  OUT_OF_SCOPE: 'OUT_OF_SCOPE',
  TEACHER_APPROVED: 'TEACHER_APPROVED',
  TEACHER_OVERRIDDEN: 'TEACHER_OVERRIDDEN',
  FAILED: 'FAILED',
  AI_CONFIDENT: 'AI_CONFIDENT',
  QUALITY_ISSUE: 'QUALITY_ISSUE',
  OVERRIDDEN: 'OVERRIDDEN'
} as const;

export type AssignmentStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
export const AssignmentStatus = {
  DRAFT: 'DRAFT',
  ACTIVE: 'ACTIVE',
  ARCHIVED: 'ARCHIVED'
} as const;

export type BatchStatus = 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'REVIEW_REQUIRED' | 'FAILED';
export const BatchStatus = {
  UPLOADING: 'UPLOADING',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  FAILED: 'FAILED'
} as const;

export interface Batch {
  id: string;
  assignmentId: string;
  className: string;
  assignmentTitle: string;
  totalImages: number;
  processedCount: number;
  reviewRequiredCount: number;
  status: BatchStatus;
  createdAt: string;
}

export interface Evidence {
  position: string;
  rule: string;
  highlightCoordinates?: number[];
  issueType?: string;
}

export interface Submission {
  id: string;
  batchId: string;
  studentName: string;
  imageUrl: string;
  status: SubmissionStatus;
  recognitionConfidence: number;
  diagnosisConfidence: number;
  suggestedScore: number;
  teacherScore?: number;
  decision?: string; // VALID, INVALID
  evidence?: Evidence;
  recognizedText?: string;
}

export interface DashboardStats {
  totalToday: number;
  completed: number;
  reviewRequired: number;
  recentBatches: Batch[];
}
