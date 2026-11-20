import type { FlowDomain, ImageDraft } from './recognitionDraftStore';

export type DraftIssue = 'none' | 'missing' | 'expired' | 'corrupt' | 'unavailable' | 'unauthorized';
export type DraftRecovery = { restoring: boolean; issue: DraftIssue; returnMode?: FlowDomain };
const ready: DraftRecovery = { restoring: false, issue: 'none' };
// Native keeps its existing in-memory photo lifecycle. Browser APIs live in .web.
export const imageDraftPersistence = {
  subscribe: (_listener: () => void) => () => {},
  getSnapshot: () => ready,
  activate: async (_owner?: string | null, _restoreDraft?: boolean) => {},
  confirm: async (_draft: ImageDraft, _step: string) => true,
  savePrivacy: async (_draft: ImageDraft) => {},
  savePrivacyMasks: (_id: string, _masks: NonNullable<ImageDraft['masks']>) => {},
  saveCrop: (_draft: ImageDraft, _edit: NonNullable<ImageDraft['cropEdit']>) => {},
  beginProcessing: async (_draft: ImageDraft) => {},
  checkpoint: async (_draft: ImageDraft, _step: string) => {},
  complete: async () => {},
  identity: () => '',
  ownUrl: (uri: string) => uri,
  releaseUrl: (_uri: string) => {},
};
