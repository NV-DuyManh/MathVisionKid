export type FlowDomain = 'HANDWRITING_TEXT' | 'ARITHMETIC' | 'OCR_PILOT' | 'OCR_PILOT_MULTILINE';

export enum SubmissionStatus {
  PROCESSING = 'PROCESSING',
  FEEDBACK_READY = 'FEEDBACK_READY',
  NEEDS_CONFIRMATION = 'NEEDS_CONFIRMATION',
  NEEDS_RETAKE = 'NEEDS_RETAKE',
  CROP_REQUIRED = 'CROP_REQUIRED',
  OUT_OF_SCOPE = 'OUT_OF_SCOPE',
  REVIEW_REQUIRED = 'REVIEW_REQUIRED',
}

export enum Decision {
  VALID = 'VALID',
  INVALID = 'INVALID',
  UNCERTAIN = 'UNCERTAIN',
}

export enum ErrorType {
  COMPUTATION_ERROR = 'COMPUTATION_ERROR',
  CARRY_BORROW_ERROR = 'CARRY_BORROW_ERROR',
  PLACE_VALUE_ALIGNMENT_ERROR = 'PLACE_VALUE_ALIGNMENT_ERROR',
  NOTATION_ISSUE = 'NOTATION_ISSUE',
}

export enum ImageQualityIssue {
  BLUR = 'BLUR',
  DARK = 'DARK',
  GLARE = 'GLARE',
  SKEW = 'SKEW',
  INCOMPLETE_CROP = 'INCOMPLETE_CROP',
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface RecognizedToken {
  value: string;
  tokenId?: string;
  tokenClass?: string;
  boundingBox?: [number, number, number, number];
  row?: number;
  column?: number;
  ambiguity?: boolean;
  alternatives?: string[];
  box?: BoundingBox;
  confidence?: number;
  isAmbiguous?: boolean;
}

export interface RecognizedExercise {
  expression?: string;
  rawExpression?: string;
  tokens?: RecognizedToken[];
  rawTokens?: RecognizedToken[];
  corrections?: unknown[];
  operator?: string;
  operands?: RecognizedToken[] | string[];
  observedResult?: RecognizedToken[] | string;
  carryMarks?: RecognizedToken[];
}

export interface ColumnValidation {
  columnIndex: number;
  expectedValue: string;
  actualValue: string;
  isValid: boolean;
  errorType?: ErrorType;
}

export interface Validation {
  decision?: Decision;
  isValid?: boolean | null;
  diagnosisState?: string;
  columns?: ColumnValidation[];
  firstInvalidIndex?: number;
  errorType?: ErrorType;
}

export interface StudentFeedback {
  title: string;
  hint: string;
  revealAnswer: boolean;
  focusEvidenceId?: string;
}

export interface RecognitionAttemptDiagnostics {
  detectorInvoked?: boolean;
  detectorTokenCount?: number;
  ocrInvoked?: boolean;
  ocrTextLength?: number;
  parserInvoked?: boolean;
  parserStatus?: string;
  validatorInvoked?: boolean;
  validatorStatus?: string;
  qualityFlags?: string[];
  reasonCode?: string;
}

export interface SubmissionResult {
  id: string;
  jobId?: string;
  status: SubmissionStatus;
  recognizedExercise?: RecognizedExercise;
  validation?: Validation;
  studentFeedback?: StudentFeedback;
  imageQualityIssue?: ImageQualityIssue;
  ambiguousToken?: RecognizedToken;
  reasonCode?: string;
  diagnostics?: RecognitionAttemptDiagnostics;
  flowDomain?: FlowDomain;
  uncertainTokenIds?: string[];
  evidence?: { items?: { evidenceId?: string; columnIndex?: number; description?: string }[] };
  modelVersion?: string;
  createdAt?: string;
}

export interface TokenCorrection {
  jobId: string;
  tokenId: string;
  newClass: string;
}

export interface SubmissionService {
  uploadImage(uri: string, signal?: AbortSignal): Promise<SubmissionResult>;
  getSubmission(id: string, scenarioHint?: string, signal?: AbortSignal): Promise<SubmissionResult>;
  confirmToken(id: string, correction: TokenCorrection, signal?: AbortSignal): Promise<SubmissionResult>;
  retrySubmission(id: string, uri: string, signal?: AbortSignal): Promise<SubmissionResult>;
}
