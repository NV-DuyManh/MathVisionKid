const mockValues = new Map<string, string>();
const mockWrite = jest.fn(async (key: string, value: string) => { mockValues.set(key, value); });
jest.mock('react-native', () => ({ Platform: { OS: 'android' } }));
jest.mock('expo-secure-store', () => ({
  getItemAsync: async (key: string) => mockValues.get(key) ?? null,
  setItemAsync: (key: string, value: string) => mockWrite(key, value),
  deleteItemAsync: async (key: string) => { mockValues.delete(key); },
}));
import { tokenStorage } from '../tokenStorage';
test('queued refresh writes cannot overwrite the next account after local logout', async () => {
  await tokenStorage.clearTokens();
  await tokenStorage.saveTokens('a-access', 'a-refresh');
  const oldId = await tokenStorage.getSessionId();
  let finishWrite: () => void = () => {};
  let started: () => void = () => {};
  const pendingWrite = new Promise<void>(resolve => { finishWrite = resolve; });
  const writeStarted = new Promise<void>(resolve => { started = resolve; });
  mockWrite.mockImplementationOnce(async (key, value) => { started(); await pendingWrite; mockValues.set(key, value); });
  const oldRefresh = tokenStorage.saveTokens('a-rotated', 'a-refresh-rotated', oldId);
  await writeStarted;
  const clear = tokenStorage.clearTokens();
  const next = tokenStorage.saveTokens('b-access', 'b-refresh');
  finishWrite();
  await Promise.all([oldRefresh, clear, next]);
  expect(await tokenStorage.getAccessToken()).toBe('b-access');
  expect(await tokenStorage.getRefreshToken()).toBe('b-refresh');
  await tokenStorage.saveTokens('a-late', 'a-late-refresh', oldId);
  expect(await tokenStorage.getAccessToken()).toBe('b-access');
});
