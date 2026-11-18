import { readFileSync } from 'node:fs';
import { ModuleKind, transpileModule } from 'typescript';
import { test, expect } from '../browser/fixtures.mjs';

// Exercise the controller's public API with real browser IndexedDB. Only the
// auth/store boundary and the completion time of one image decode are controlled.
const controller = transpileModule(readFileSync(new URL('../../apps/student-mobile/src/features/recognition/state/imageDraftPersistence.web.ts', import.meta.url), 'utf8'),
  { compilerOptions: { module: ModuleKind.CommonJS } }).outputText;

for (const outcome of ['error', 'success']) {
  test(`A stale ${outcome} during photo restoration cannot remove the next session draft`, async ({ page }) => {
    await page.route('https://draft-race.example.test/', route => route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>Private photo controller contract</title>' }));
    await page.goto('https://draft-race.example.test/');
    const result = await page.evaluate(async ({ controller, outcome }) => {
      const db = await new Promise((resolve, reject) => {
        const request = indexedDB.open('mathvision-private-photo-v1', 1);
        request.onupgradeneeded = () => {
          request.result.createObjectStore('drafts'); request.result.createObjectStore('images');
        };
        request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
      });
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 16;
      const context = canvas.getContext('2d'); context.fillRect(0, 0, 16, 16);
      const photo = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
      const scopes = ['old', 'new'].map(name => JSON.stringify([`owner-${name}`, `session-${name}`]));
      await new Promise((resolve, reject) => {
        const tx = db.transaction(['drafts', 'images'], 'readwrite');
        for (const [index, name] of ['old', 'new'].entries()) {
          const now = Date.now();
          tx.objectStore('drafts').put({ version: 1, scope: scopes[index], owner: `owner-${name}`, session: `session-${name}`,
            id: `photo-${name}`, imageRevision: name, createdAt: now, updatedAt: now, expiresAt: now + 60000, step: 'crop',
            meta: { width: 16, height: 16, source: 'GALLERY', mode: 'ARITHMETIC', isMasked: true } }, scopes[index]);
          tx.objectStore('images').put({ privacy: photo }, scopes[index]);
        }
        tx.oncomplete = resolve; tx.onerror = () => reject(tx.error);
      });
      let session = 'session-old', draft = null;
      const listeners = new Set();
      const notify = () => listeners.forEach(listener => listener());
      const store = { getDraft: () => draft, subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
        clearDraft: () => { draft = null; notify(); }, setDraft: value => { draft = value; notify(); } };
      const exported = {};
      new Function('require', 'exports', controller)(name => {
        if (name.endsWith('recognitionDraftStore')) return { recognitionDraftStore: store, isValidFlowDomain: mode => mode === 'ARITHMETIC' };
        if (name.endsWith('tokenStorage')) return { tokenStorage: { getSessionId: async () => session } };
        throw new Error(`Unexpected controller dependency: ${name}`);
      }, exported);
      const persistence = exported.imageDraftPersistence;
      const RealImage = window.Image, sourceProperty = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
      let hold = true, release;
      let entered;
      const decoding = new Promise(resolve => { entered = resolve; });
      window.Image = function () {
        const image = new RealImage();
        if (hold) {
          hold = false;
          Object.defineProperty(image, 'src', { configurable: true, set(value) {
            release = () => outcome === 'error' ? image.onerror(new Event('error')) : sourceProperty.set.call(image, value);
            entered();
          } });
        }
        return image;
      };
      try {
        const previous = persistence.activate('owner-old');
        await decoding;
        session = 'session-new';
        await persistence.activate('owner-new');
        const restored = draft?.imageSessionId;
        release(); await previous;
        const exists = await new Promise((resolve, reject) => {
          const tx = db.transaction(['drafts', 'images'], 'readonly');
          const meta = tx.objectStore('drafts').get(scopes[1]), image = tx.objectStore('images').get(scopes[1]);
          tx.oncomplete = () => resolve(!!meta.result && image.result?.privacy instanceof Blob);
          tx.onerror = () => reject(tx.error);
        });
        return { restored, exists, active: draft?.imageSessionId, state: persistence.getSnapshot() };
      } finally { window.Image = RealImage; db.close(); }
    }, { controller, outcome });
    expect(result).toEqual({ restored: 'photo-new', exists: true, active: 'photo-new', state: { restoring: false, issue: 'none' } });
  });
}
