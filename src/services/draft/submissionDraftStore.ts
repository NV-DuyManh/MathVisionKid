export type FlowDomain = 'HANDWRITING_TEXT' | 'ARITHMETIC' | 'OCR_PILOT' | 'OCR_PILOT_MULTILINE';

export function isHandwritingDomain(mode?: string | null): boolean {
  return mode === 'HANDWRITING_TEXT' || mode === 'OCR_PILOT' || mode === 'OCR_PILOT_MULTILINE';
}

export function isValidFlowDomain(mode: any): mode is FlowDomain {
  return mode === 'HANDWRITING_TEXT' || mode === 'ARITHMETIC' || mode === 'OCR_PILOT' || mode === 'OCR_PILOT_MULTILINE';
}

/**
 * Single source of truth for flow domain resolution.
 * Rules:
 * 1. Explicit valid mode wins.
 * 2. Persisted valid draft mode next.
 * 3. Generic Student flow default = HANDWRITING_TEXT.
 * 4. Never default to ARITHMETIC.
 */
export function resolveFlowDomain(explicitMode?: string | null, draftMode?: string | null): FlowDomain {
  if (explicitMode && isValidFlowDomain(explicitMode)) {
    return explicitMode;
  }
  if (draftMode && isValidFlowDomain(draftMode)) {
    return draftMode;
  }
  if (explicitMode || draftMode) {
    if (__DEV__) {
      console.warn(`[FLOW_DOMAIN][FALLBACK] Invalid/missing mode (explicit=${explicitMode}, draft=${draftMode}). Failing closed to HANDWRITING_TEXT.`);
    }
  }
  return 'HANDWRITING_TEXT';
}

export function logFlowDomain(stage: 'ACQUIRE' | 'PRIVACY' | 'POST_PRIVACY' | 'RESULT' | string, domain: FlowDomain): void {
  console.log(`[FLOW_DOMAIN][${stage}] ${domain}`);
}

export interface ImageDraft {
  rawUri: string;
  uri: string;
  width: number;
  height: number;
  mimeType: string;
  filename: string;
  source?: 'CAMERA' | 'GALLERY';
  mode?: FlowDomain;
  masks?: { id: number; x: number; y: number; width: number; height: number }[];
  isMasked?: boolean;
  originalUri?: string;
  retrySubmissionId?: string;
  createdAt?: number;
}

class SubmissionDraftStore {
  private currentDraft: ImageDraft | null = null;

  setDraft(draft: Omit<ImageDraft, 'createdAt'>): ImageDraft {
    this.currentDraft = {
      ...draft,
      createdAt: Date.now(),
    };
    return this.currentDraft;
  }

  getDraft(): ImageDraft | null {
    return this.currentDraft;
  }

  updateDraft(patch: Partial<ImageDraft>): ImageDraft | null {
    if (!this.currentDraft) return null;
    this.currentDraft = {
      ...this.currentDraft,
      ...patch,
    };
    return this.currentDraft;
  }

  clearDraft(): void {
    this.currentDraft = null;
  }
}

export const submissionDraftStore = new SubmissionDraftStore();
