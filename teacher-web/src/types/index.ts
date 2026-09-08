export interface Teacher {
  id: string;
  name: string;
  email: string;
}

export interface Class {
  id: string;
  classId?: string;
  name: string;
  studentCount: number;
}

export type MathType = 'VERTICAL_ADDITION' | 'VERTICAL_SUBTRACTION';
export const MathType = {
  VERTICAL_ADDITION: 'VERTICAL_ADDITION',
  VERTICAL_SUBTRACTION: 'VERTICAL_SUBTRACTION'
} as const;

export interface Assignment {
  id?: string;
  assignmentId?: string;
  classId: string;
  title: string;
  mathType: MathType;
  createdAt?: string;
  status?: string;
}

export type SubmissionStatus = 'CREATED' | 'IMAGE_UPLOADED' | 'PROCESSING' | 'NEEDS_CONFIRMATION' | 'NEEDS_RETAKE' | 'CROP_REQUIRED' | 'FEEDBACK_READY' | 'REVIEW_REQUIRED' | 'OUT_OF_SCOPE' | 'TEACHER_APPROVED' | 'TEACHER_OVERRIDDEN' | 'FAILED' | 'AI_CONFIDENT' | 'QUALITY_ISSUE' | 'OVERRIDDEN' | 'PROPOSED_GRADE';

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
  OVERRIDDEN: 'OVERRIDDEN',
  PROPOSED_GRADE: 'PROPOSED_GRADE'
} as const;

export type AssignmentStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
export const AssignmentStatus = {
  DRAFT: 'DRAFT',
  ACTIVE: 'ACTIVE',
  ARCHIVED: 'ARCHIVED'
} as const;

export type BatchStatus = 'CREATED' | 'UPLOADING' | 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'PARTIAL' | 'FAILED';
export const BatchStatus = {
  CREATED: 'CREATED',
  UPLOADING: 'UPLOADING',
  QUEUED: 'QUEUED',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  PARTIAL: 'PARTIAL',
  FAILED: 'FAILED'
} as const;

export interface Batch {
  id?: string;
  batchId?: string;
  assignmentId: string;
  className?: string;
  assignmentTitle?: string;
  totalImages?: number;
  totalCount?: number;
  processedCount: number;
  reviewRequiredCount: number;
  status: BatchStatus;
  createdAt?: string;
}

export interface Evidence {
  position: string;
  rule: string;
  highlightCoordinates?: number[];
  issueType?: string;
}

export interface Submission {
  id?: string;
  submissionId?: string;
  batchId: string;
  studentName?: string;
  studentId?: string;
  imageUrl: string;
  status: SubmissionStatus;
  recognitionConfidence?: number;
  diagnosisConfidence?: number;
  suggestedScore?: number;
  gradeProposal?: { score: number; confidence: number; metadata: any };
  teacherScore?: number;
  decision?: string; // VALID, INVALID
  evidence?: Evidence | any;
  recognizedText?: string;
}

export interface DashboardStats {
  totalToday: number;
  completed: number;
  reviewRequired: number;
  recentBatches: Batch[];
}
