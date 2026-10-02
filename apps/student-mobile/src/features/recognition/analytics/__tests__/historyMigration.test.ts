import * as SecureStore from 'expo-secure-store';
import { RecognitionAnalyticsStore } from '../recognitionAnalyticsStore';
import { LEGACY_HISTORY_KEY } from '../legacyHistory';

const currentKey = 'mathvision_recognition_history_v4';
const storage = new Map<string, string>();
const oldHistory = JSON.stringify([{
  sessionId: 'existing-trial', status: 'COMPLETED', totalLines: 1, confirmedLines: 1,
  imageSha256: 'original-page-hash', datasetVersion: 'original-source-version', modelVersion: 'original-model',
  lineMetrics: [{ lineId: 'line-1', ocrOutput: '25 - 8 = 18', finalResult: '25 - 8 = 18' }],
}]);

beforeEach(async () => {
  storage.clear();
  jest.spyOn(SecureStore, 'getItemAsync').mockImplementation(async key => storage.get(key) ?? null);
  jest.spyOn(SecureStore, 'setItemAsync').mockImplementation(async (key, value) => { storage.set(key, value); });
  jest.spyOn(SecureStore, 'deleteItemAsync').mockImplementation(async key => { storage.delete(key); });
  await new RecognitionAnalyticsStore().reset();
});
afterEach(() => jest.restoreAllMocks());

test('migrates history without changing image hashes, model provenance, or student answers', async () => {
  storage.set(LEGACY_HISTORY_KEY, oldHistory);
  const store = new RecognitionAnalyticsStore();
  await store.init();
  expect(storage.get(currentKey)).toBe(oldHistory);
  expect(storage.has(LEGACY_HISTORY_KEY)).toBe(false);
  expect(store.getSessions()[0].imageSha256).toBe('original-page-hash');
  expect(store.getSessions()[0].modelVersion).toBe('original-model');
  expect(store.getSessions()[0].lineMetrics?.[0].finalResult).toBe('25 - 8 = 18');
  const reload = new RecognitionAnalyticsStore();
  await reload.init();
  expect(reload.getSessions()).toHaveLength(1);
});

test('keeps the old history when durable migration fails', async () => {
  storage.set(LEGACY_HISTORY_KEY, oldHistory);
  (SecureStore.setItemAsync as jest.Mock).mockRejectedValueOnce(new Error('Storage unavailable'));
  const store = new RecognitionAnalyticsStore();
  await store.init();
  expect(storage.get(LEGACY_HISTORY_KEY)).toBe(oldHistory);
  expect(store.getSessions()[0].sessionId).toBe('existing-trial');
});

test('does not resurrect sample sessions after an explicitly emptied history', async () => {
  storage.set(currentKey, '[]');
  const store = new RecognitionAnalyticsStore();
  await store.init();
  expect(store.getSessions()).toEqual([]);
});

test('keeps student histories and saved trial details separate across account changes', async () => {
  const store = new RecognitionAnalyticsStore();
  store.setUserScope('student-A');
  await store.init();
  await store.completeTrial({ trialId: 'student-A-trial', lines: [
    { lineId: 'line-1', predictedText: '25 - 8 = 18', rawOcrText: '25 - 8 = 18', verifiedTextRaw: '25 - 8 = 18', verdict: 'CORRECT' },
  ] } as any);
  expect(store.getSessions()).toHaveLength(1);
  store.setUserScope('student-B');
  await store.init();
  expect(store.getSessions()).toHaveLength(0);
  expect(await store.getCurrentTrialAnalytics('student-A-trial')).toBeNull();
  store.setUserScope('student-A');
  await store.init();
  expect(store.getSessions()[0].sessionId).toBe('student-A-trial');
  expect((await store.getCurrentTrialAnalytics('student-A-trial'))?.trialId).toBe('student-A-trial');
});

test('preserves unowned legacy data without assigning it to the next signed-in student', async () => {
  storage.set(LEGACY_HISTORY_KEY, oldHistory);
  const store = new RecognitionAnalyticsStore();
  store.setUserScope('student-C');
  await store.init();
  expect(storage.get(currentKey)).toBe(oldHistory);
  expect(store.getSessions()).toHaveLength(0);
});

test('does not return another current trial when the requested trial is missing', async () => {
  const store = new RecognitionAnalyticsStore();
  store.setCurrentTrialAnalytics({ trialId: 'other-current-trial' } as any);
  expect(await store.getCurrentTrialAnalytics('missing-trial')).toBeNull();
});
