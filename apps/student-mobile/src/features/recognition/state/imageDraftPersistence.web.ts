import { recognitionDraftStore, isValidFlowDomain, type ImageDraft } from './recognitionDraftStore';
import { tokenStorage } from '../../../services/auth/tokenStorage.web';
import type { DraftIssue, DraftRecovery } from './imageDraftPersistence';

const DB = 'mathvision-private-photo-v1', JOURNAL = 'mathvision-photo-edit-v1';
const TTL = 30 * 60 * 1000, MAX_LIFE = 24 * 60 * 60 * 1000, MAX_BYTES = 20 * 1024 * 1024;
type Edit = NonNullable<ImageDraft['cropEdit']>;
type Metadata = Pick<ImageDraft, 'width' | 'height' | 'source' | 'mode' | 'isMasked' | 'problemText' |
  'retrySubmissionId' | 'arithmeticSubmissionId' | 'lessonContext' | 'cropEdit' | 'processingStarted'>;
type Record = { version: 1; scope: string; owner: string; session: string; id: string; imageRevision: string; createdAt: number;
  updatedAt: number; expiresAt: number; step: string; meta: Metadata };
type Images = { privacy?: Blob; cropped?: Blob; original?: Blob };
type Masks = NonNullable<ImageDraft['masks']>;
const PRIVACY_JOURNAL = 'mathvision-photo-privacy-v1', PRIVACY_TTL = 30000;
let returnMode: ImageDraft['mode'];
let privacyExpiry: ReturnType<typeof setTimeout> | undefined;
let state: DraftRecovery = { restoring: false, issue: 'none' };
let owner = '', session = '', scope = '', revision = 0;
let saved: Record | null = null, privacyUri = '', croppedUri = '', restoring = false;
let database: Promise<IDBDatabase> | undefined;
const listeners = new Set<() => void>(), urls = new Set<string>();
function publish(issue: DraftIssue, loading = false) {
  state = { restoring: loading, issue, returnMode }; listeners.forEach(listener => listener());
}
function open(): Promise<IDBDatabase> {
  if (!database) database = new Promise<IDBDatabase>((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => { settled = true; reject(new Error('Storage unavailable')); }, 5000);
    const request = indexedDB.open(DB, 1);
    request.onupgradeneeded = () => { request.result.createObjectStore('drafts'); request.result.createObjectStore('images'); };
    request.onerror = request.onblocked = () => { clearTimeout(timer); settled = true; reject(new Error('Storage unavailable')); };
    request.onsuccess = () => {
      clearTimeout(timer);
      if (settled) { request.result.close(); return; }
      request.result.onversionchange = () => { request.result.close(); database = undefined; };
      resolve(request.result);
    };
  }).catch(error => { database = undefined; throw error; });
  return database;
}
async function transaction(mode: IDBTransactionMode, action: (tx: IDBTransaction) => void) {
  const db = await open();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(['drafts', 'images'], mode);
    const timer = setTimeout(() => { tx.abort(); }, 5000);
    tx.oncomplete = () => { clearTimeout(timer); resolve(); };
    tx.onerror = tx.onabort = () => { clearTimeout(timer); reject(new Error('Storage unavailable')); };
    try { action(tx); } catch (error) { tx.abort(); reject(error); }
  });
}
function forgetJournal(key: string) {
  try { if (JSON.parse(localStorage.getItem(JOURNAL) || 'null')?.scope === key) localStorage.removeItem(JOURNAL); } catch {}
}
async function remove(key: string) {
  if (!key) return;
  forgetJournal(key);
  await transaction('readwrite', tx => { tx.objectStore('drafts').delete(key); tx.objectStore('images').delete(key); });
}
function privacyJournal() {
  try { return JSON.parse(window.sessionStorage.getItem(PRIVACY_JOURNAL) || 'null'); } catch { return null; }
}
function forgetPrivacyJournal(key: string, id?: string) {
  const entry = privacyJournal();
  if (entry?.scope === key && (!id || entry.id === id)) {
    try { window.sessionStorage.removeItem(PRIVACY_JOURNAL); } catch {}
  }
}
function expirePrivacyMasks(key: string, id: string) {
  const entry = privacyJournal();
  if (entry?.scope !== key || entry.id !== id || !entry.masks?.length) return;
  try {
    window.sessionStorage.setItem(PRIVACY_JOURNAL, JSON.stringify({ scope: key, id, mode: entry.mode, masks: [] }));
  } catch {}
}
function validMask(mask: Masks[number]) {
  return !!mask && Number.isSafeInteger(mask.id)
    && [mask.x, mask.y, mask.width, mask.height].every(value => Number.isFinite(value) && value >= 0 && value <= 1)
    && mask.width > 0 && mask.height > 0 && mask.x + mask.width <= 1.00001 && mask.y + mask.height <= 1.00001;
}
function schedulePrivacyExpiry(record: Record) {
  clearTimeout(privacyExpiry);
  privacyExpiry = setTimeout(() => {
    expirePrivacyMasks(record.scope, record.id);
    void transaction('readwrite', tx => {
      const store = tx.objectStore('drafts');
      const request = store.get(record.scope);
      request.onsuccess = () => {
        const row = request.result as Record | undefined;
        if (row?.step === 'privacy' && row.id === record.id && row.expiresAt <= Date.now()) {
          store.delete(record.scope);
          tx.objectStore('images').delete(record.scope);
        }
      };
    }).catch(() => {});
  }, Math.max(0, record.expiresAt - Date.now()));
}
function ownUrl(uri: string) { urls.add(uri); return uri; }
function revoke(uri: string) { if (urls.delete(uri)) URL.revokeObjectURL(uri); }
function references(draft: ImageDraft | null) {
  return [draft?.uri, draft?.rawUri, draft?.originalImageUri, draft?.sourceImageUri, draft?.privacyImageUri,
    draft?.croppedImageUri, draft?.lessonContext?.workImageUri, draft?.lessonContext?.problemImageUri];
}
let previous: ImageDraft | null = null;
recognitionDraftStore.subscribe(() => {
  const draft = recognitionDraftStore.getDraft();
  const next = references(draft);
  for (const uri of references(previous)) if (uri && !next.includes(uri)) revoke(uri);
  previous = draft;
  if (restoring) return;
  if (!draft || (saved && draft.imageSessionId !== saved.id)) {
    const key = scope, generation = revision; saved = null; privacyUri = croppedUri = '';
    forgetPrivacyJournal(key);
    void remove(key).catch(() => { if (generation === revision) publish('unavailable'); });
  }
});
function validEdit(value: unknown): value is Edit {
  const edit = value as Edit;
  const s = edit?.selection;
  return !!s && Object.values(s).length === 4 && Object.values(s).every(n => Number.isFinite(n) && n >= 0 && n <= 1)
    && s.w > 0 && s.h > 0 && s.x + s.w <= 1.00001 && s.y + s.h <= 1.00001
    && Number.isInteger(edit.turns) && edit.turns >= 0 && edit.turns <= 3 && Number.isFinite(edit.fine) && Math.abs(edit.fine) <= 45;
}
function metadata(draft: ImageDraft): Metadata {
  const context = draft.lessonContext;
  // Do not persist any original/photo URI from the learning context either.
  const safeContext = context ? { ...context, workImageUri: undefined, problemImageUri: undefined, workImageCurrent: false } : undefined;
  return { width: draft.width, height: draft.height, source: draft.source, mode: draft.mode, isMasked: draft.isMasked,
    problemText: draft.problemText, retrySubmissionId: draft.retrySubmissionId, arithmeticSubmissionId: draft.arithmeticSubmissionId,
    lessonContext: safeContext, cropEdit: draft.cropEdit, processingStarted: draft.processingStarted };
}
function valid(record: Record, images: Images) {
  return record?.version === 1 && record.scope === scope && record.owner === owner && record.session === session
    && typeof record.id === 'string' && record.id.length > 0 && record.id.length < 200 && typeof record.imageRevision === 'string'
    && Number.isFinite(record.createdAt) && Number.isFinite(record.expiresAt) && record.expiresAt <= record.createdAt + MAX_LIFE
    && Number.isInteger(record.meta?.width) && record.meta.width > 0 && record.meta.width <= 10000
    && Number.isInteger(record.meta.height) && record.meta.height > 0 && record.meta.height <= 10000 && isValidFlowDomain(record.meta.mode)
    && (!record.meta.cropEdit || validEdit(record.meta.cropEdit))
    && (record.step === 'privacy'
      ? record.expiresAt <= record.createdAt + PRIVACY_TTL && validPhoto(images?.original)
      : validPhoto(images?.privacy) && (!images.cropped || validPhoto(images.cropped)));
}
function validPhoto(blob?: Blob): blob is Blob {
  return blob instanceof Blob && blob.size > 0 && blob.size <= MAX_BYTES && /^image\/(jpeg|png|webp)$/.test(blob.type);
}
async function dimensions(blob: Blob) {
  const uri = URL.createObjectURL(blob);
  try {
    return await new Promise<{ width: number; height: number }>((resolve, reject) => {
      const image = new Image();
      const timer = setTimeout(() => { image.src = ''; reject(new Error('Image unavailable')); }, 5000);
      image.onload = () => { clearTimeout(timer); resolve({ width: image.naturalWidth, height: image.naturalHeight }); };
      image.onerror = () => { clearTimeout(timer); reject(new Error('Invalid image')); };
      image.src = uri;
    });
  } finally { URL.revokeObjectURL(uri); }
}
async function cleanup() {
  await transaction('readwrite', tx => {
    const request = tx.objectStore('drafts').getAll();
    request.onsuccess = () => {
      const rows = (request.result as Record[]).sort((a, b) => b.updatedAt - a.updatedAt);
      rows.forEach((record, index) => {
        if (record.expiresAt <= Date.now() || index >= 3) {
          tx.objectStore('drafts').delete(record.scope); tx.objectStore('images').delete(record.scope);
        }
      });
    };
  });
}
async function current(generation: number) {
  const expectedScope = scope, expectedSession = session;
  const actual = await tokenStorage.getDraftScopeId();
  return generation === revision && !!scope && expectedScope === scope && expectedSession === session && actual === session;
}
async function activate(nextOwner?: string | null, restoreDraft = true) {
  const generation = ++revision, oldScope = scope;
  owner = nextOwner || ''; session = scope = ''; saved = null; privacyUri = croppedUri = ''; returnMode = undefined;
  restoring = true; recognitionDraftStore.clearDraft(); restoring = false;
  for (const uri of [...urls]) revoke(uri);
  if (!owner || !restoreDraft) {
    clearTimeout(privacyExpiry);
    forgetPrivacyJournal(oldScope);
    if (owner) {
      const id = await tokenStorage.getDraftScopeId();
      if (generation !== revision) return;
      if (id) { session = id; scope = JSON.stringify([owner, id]); }
    }
    publish('missing');
    if (oldScope && oldScope !== scope) await remove(oldScope).catch(() => {});
    return;
  }
  publish('none', true);
  try {
    const id = await tokenStorage.getDraftScopeId();
    if (generation !== revision) return;
    if (!id) { publish('unauthorized'); return; }
    session = id; scope = JSON.stringify([owner, session]);
    const journal = privacyJournal();
    const privacyEntry = typeof window !== 'undefined' && /(?:^|\/)privacy\/?$/.test(window.location.pathname)
      && journal?.scope === scope && isValidFlowDomain(journal.mode);
    if (privacyEntry) returnMode = journal.mode;
    let record: Record | undefined, images: Images | undefined;
    await transaction('readonly', tx => {
      const m = tx.objectStore('drafts').get(scope), b = tx.objectStore('images').get(scope);
      m.onsuccess = () => { record = m.result; }; b.onsuccess = () => { images = b.result; };
    });
    if (!await current(generation)) return;
    if (!record) {
      if (privacyEntry) expirePrivacyMasks(scope, journal.id);
      publish('missing'); void cleanup().catch(() => {}); return;
    }
    if (!valid(record, images!)) { await remove(scope); if (generation === revision) publish('corrupt'); return; }
    if (record.expiresAt <= Date.now()) {
      if (record.step === 'privacy') expirePrivacyMasks(scope, record.id);
      await remove(scope);
      if (generation === revision) publish('expired');
      return;
    }
    if (record.step === 'privacy') {
      schedulePrivacyExpiry(record);
      if (!privacyEntry || journal.id !== record.id) { publish('missing'); return; }
      const raw = images!.original!;
      const uri = ownUrl(URL.createObjectURL(raw));
      const masks = Array.isArray(journal.masks) ? journal.masks.filter(validMask) : [];
      saved = record;
      restoring = true;
      recognitionDraftStore.setDraft({ ...record.meta, imageSessionId: record.id, privacyMaskDraft: masks,
        uri, rawUri: uri, sourceImageUri: uri, originalImageUri: uri, privacyConfirmed: false,
        mimeType: raw.type, filename: 'private-photo.jpg' });
      restoring = false;
      publish('none');
      return;
    }
    try {
      const privacySize = await dimensions(images!.privacy!);
      const activeSize = images!.cropped ? await dimensions(images!.cropped) : privacySize;
      if (activeSize.width !== record.meta.width || activeSize.height !== record.meta.height) throw new Error('Image revision does not match');
    } catch {
      if (!await current(generation)) return;
      await remove(scope);
      if (generation === revision) publish('corrupt');
      return;
    }
    if (!await current(generation)) return;
    try {
      const edit = JSON.parse(localStorage.getItem(JOURNAL) || 'null');
      if (edit?.scope === scope && edit.id === record.id && edit.imageRevision === record.imageRevision && edit.expiresAt > Date.now()) {
        if (!validEdit(edit.cropEdit)) throw new Error('Invalid crop');
        record.meta.cropEdit = edit.cropEdit;
      }
    } catch { /* Valid committed metadata remains usable when the small edit journal is unavailable. */ }
    if (!await current(generation)) return;
    privacyUri = ownUrl(URL.createObjectURL(images!.privacy!));
    croppedUri = images!.cropped ? ownUrl(URL.createObjectURL(images!.cropped)) : '';
    saved = record;
    restoring = true;
    const meta = metadata({ ...record.meta, uri: '', rawUri: '', mimeType: '', filename: '' });
    recognitionDraftStore.setDraft({ ...meta, imageSessionId: record.id, recoveredAfterReload: true,
      uri: croppedUri || privacyUri, rawUri: privacyUri, originalUri: privacyUri, originalImageUri: privacyUri,
      sourceImageUri: privacyUri, privacyImageUri: privacyUri, croppedImageUri: croppedUri || undefined,
      privacyConfirmed: true, mimeType: 'image/jpeg', filename: 'private-photo.jpg' });
    restoring = false;
    publish('none'); void cleanup().catch(() => {});
  } catch { if (generation === revision) { restoring = false; publish('unavailable'); } }
}
async function photo(uri: string) {
  if (!/^(blob:|data:image\/)/.test(uri)) throw new Error('Only local images can be saved');
  const response = await fetch(uri, { signal: AbortSignal.timeout(10000) });
  if (!response.ok) throw new Error('Image unavailable');
  const blob = await response.blob();
  if (!blob.size || blob.size > MAX_BYTES || !/^image\/(jpeg|png|webp)$/.test(blob.type)) throw new Error('Invalid image');
  return blob;
}
async function savePrivacy(draft: ImageDraft) {
  const generation = revision, key = scope, id = draft.imageSessionId;
  if (!id || draft.privacyConfirmed || !isValidFlowDomain(draft.mode) || !await current(generation)) return;
  try {
    // Without the tab's marker there is no safe way to restore this original.
    window.sessionStorage.setItem(PRIVACY_JOURNAL, JSON.stringify({ scope: key, id, mode: draft.mode, masks: [] }));
    const original = await photo(draft.sourceImageUri || draft.uri);
    if (!await current(generation) || recognitionDraftStore.getDraft()?.imageSessionId !== id) return;
    const now = Date.now();
    const record: Record = { version: 1, scope: key, owner, session, id, imageRevision: id,
      createdAt: now, updatedAt: now, expiresAt: now + PRIVACY_TTL, step: 'privacy', meta: metadata(draft) };
    await transaction('readwrite', tx => {
      if (generation !== revision || recognitionDraftStore.getDraft()?.imageSessionId !== id) throw new Error('Photo changed');
      tx.objectStore('drafts').put(record, key);
      tx.objectStore('images').put({ original }, key);
    });
    if (!await current(generation) || recognitionDraftStore.getDraft()?.imageSessionId !== id) return;
    saved = record;
    schedulePrivacyExpiry(record);
  } catch { /* The live photo can still be reviewed if browser storage is unavailable. */ }
}
function savePrivacyMasks(id: string, masks: Masks) {
  if (saved?.step !== 'privacy' || saved.id !== id || saved.expiresAt <= Date.now()) return;
  const entry = privacyJournal();
  if (entry?.scope !== scope || entry.id !== id) return;
  try {
    window.sessionStorage.setItem(PRIVACY_JOURNAL, JSON.stringify({ ...entry, masks: masks.filter(validMask) }));
  } catch { /* The live editor retains its masks when storage is unavailable. */ }
}
async function confirm(draft: ImageDraft, step: string) {
  const generation = revision, key = scope;
  try {
    if (!draft.privacyConfirmed || !draft.privacyImageUri || !draft.imageSessionId || !await current(generation)) throw new Error('Unapproved photo');
    forgetPrivacyJournal(key, draft.imageSessionId);
    const images: Images = { privacy: await photo(draft.privacyImageUri) };
    if (draft.croppedImageUri) images.cropped = await photo(draft.croppedImageUri);
    if (!await current(generation) || recognitionDraftStore.getDraft()?.imageSessionId !== draft.imageSessionId) return false;
    const now = Date.now(), createdAt = saved?.step !== 'privacy' && saved?.id === draft.imageSessionId ? saved.createdAt : now;
    const imageRevision = saved?.id === draft.imageSessionId && privacyUri === draft.privacyImageUri && croppedUri === (draft.croppedImageUri || '') ? saved.imageRevision
      : globalThis.crypto?.randomUUID?.() || `${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const record: Record = { version: 1, scope: key, owner, session, id: draft.imageSessionId, imageRevision,
      createdAt, updatedAt: now, expiresAt: Math.min(now + TTL, createdAt + MAX_LIFE), step, meta: metadata(draft) };
    await transaction('readwrite', tx => {
      if (generation !== revision) throw new Error('Session changed');
      tx.objectStore('drafts').put(record, key); tx.objectStore('images').put(images, key);
    });
    if (!await current(generation)) return false;
    saved = record; privacyUri = draft.privacyImageUri; croppedUri = draft.croppedImageUri || '';
    publish('none'); void cleanup().catch(() => {}); return true;
  } catch { if (generation === revision) publish('unavailable'); return false; }
}
function saveCrop(draft: ImageDraft, cropEdit: Edit) {
  if (!saved || saved.id !== draft.imageSessionId || !validEdit(cropEdit)) return;
  const generation = revision, key = scope, now = Date.now();
  saved = { ...saved, updatedAt: now, expiresAt: Math.min(now + TTL, saved.createdAt + MAX_LIFE), meta: { ...saved.meta, cropEdit } };
  const record = saved;
  // A tiny synchronous journal covers F5 immediately after pointer-up/key input.
  // Blobs and photo contents never enter localStorage, and metadata writes do not reserialize them.
  try { localStorage.setItem(JOURNAL, JSON.stringify({ scope: key, id: saved.id, imageRevision: saved.imageRevision, expiresAt: saved.expiresAt, cropEdit })); }
  catch { publish('unavailable'); }
  void transaction('readwrite', tx => { if (generation === revision) tx.objectStore('drafts').put(record, key); }).catch(() => {
    if (generation === revision) publish('unavailable');
  });
}
async function checkpoint(draft: ImageDraft, step: string) {
  if (!saved || saved.id !== draft.imageSessionId) return;
  const generation = revision, key = scope;
  const record: Record = { ...saved, step, meta: metadata(draft) };
  try {
    await transaction('readwrite', tx => { if (generation === revision) tx.objectStore('drafts').put(record, key); });
    if (generation === revision) saved = record;
  } catch { if (generation === revision) publish('unavailable'); }
}
if (typeof window !== 'undefined') window.addEventListener('portal_auth_changed', () => {
  void Promise.resolve(tokenStorage.getDraftScopeId()).then(id => { if (session && id !== session) void activate(null); });
});
export const imageDraftPersistence = {
  subscribe: (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
  getSnapshot: () => state,
  activate, confirm, savePrivacy, savePrivacyMasks, saveCrop, ownUrl, releaseUrl: revoke,
  identity: () => scope,
  checkpoint,
  beginProcessing: async (draft: ImageDraft) => {
    recognitionDraftStore.updateDraft({ processingStarted: true });
    await checkpoint({ ...draft, processingStarted: true }, 'processing');
  },
  complete: async () => { saved = null; await remove(scope).catch(() => publish('unavailable')); },
};
