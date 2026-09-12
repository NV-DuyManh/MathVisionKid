export type FlowDomain = 'HANDWRITING_TEXT' | 'ARITHMETIC' | 'OCR_PILOT' | 'OCR_PILOT_MULTILINE';

export function isHandwritingDomain(mode?: string | null): boolean {
  return mode === 'HANDWRITING_TEXT' || mode === 'OCR_PILOT' || mode === 'OCR_PILOT_MULTILINE';
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
