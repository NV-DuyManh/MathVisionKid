import { SubmissionStatus, Decision, OperationType, ErrorType, ImageQualityIssue, ReviewReason, TeacherDecisionType } from './enums';
import { ConfidenceBundle, Evidence, BoundingBox } from './evidence';

export interface RecognizedToken {
  tokenId: string;
  text: string;
  confidence: number;
  boundingBox: BoundingBox;
  rowIndex?: number;
  columnIndex?: number;
  semanticRole?: string;
}

export interface RecognizedExercise {
  operationType: OperationType;
  operand1: string;
  operand2: string;
  observedResult: string;
  tokens?: RecognizedToken[];
  layout?: string;
  carryBorrowMarks?: RecognizedToken[];
}

export interface ColumnValidation {
  index: number;
  placeValue: string;
  expectedRelation: string;
  observedRelation: string;
  decision: Decision;
  ruleId: string;
  evidenceIds: string[];
}

export interface ValidationResult {
  decision: Decision;
  firstInvalidIndex?: number;
  errorType?: ErrorType;
  columnResults?: ColumnValidation[];
}

export interface StudentFeedback {
  title: string;
  hint: string;
  focusEvidenceId?: string;
  revealAnswer: boolean;
  answer?: string;
}

export interface ConfirmationCandidate {
  tokenId: string;
  candidate: string;
  alternatives: string[];
  boundingBox: BoundingBox;
}

export interface GradeProposal {
  suggestedScore: number;
  maxScore: number;
  reason?: string;
  confidence: number;
  isOfficial: boolean;
}

export interface TeacherDecision {
  type: TeacherDecisionType;
  finalScore: number;
  reason?: string;
  decidedAt: string;
  teacherId: string;
}

export interface Submission {
  submissionId: string;
  batchId?: string;
  studentId?: string;
  imageUrl?: string;
  status: SubmissionStatus;
  
  recognizedExercise?: RecognizedExercise;
  validation?: ValidationResult;
  confidence?: ConfidenceBundle;
  evidence?: Evidence[];
  
  studentFeedback?: StudentFeedback;
  
  confirmation?: ConfirmationCandidate;
  
  imageQuality?: {
    issues: ImageQualityIssue[];
  };
  message?: string;

  reviewReasons?: ReviewReason[];
  gradeProposal?: GradeProposal;
  teacherDecision?: TeacherDecision;

  createdAt: string;
}
