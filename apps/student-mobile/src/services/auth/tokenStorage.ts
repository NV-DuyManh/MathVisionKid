import * as SecureStore from 'expo-secure-store';
const ACCESS = 'mathvision_access_token', REFRESH = 'mathvision_refresh_token', USER = 'mathvision_user_data';
let generation = 0;
let writes: Promise<void> = Promise.resolve();
function mutate(operation: () => Promise<void>, expected = generation) {
  const task = writes.then(async () => { if (expected === generation) await operation(); });
  writes = task.catch(() => {});
  return task;
}
async function read(key: string) {
  await writes;
  return SecureStore.getItemAsync(key);
}
async function write(key: string, value: string) {
  await SecureStore.setItemAsync(key, value);
}
async function remove(key: string) {
  await SecureStore.deleteItemAsync(key);
}
export const tokenStorage = {
  getDraftScopeId(): string | null { return null; },
  async getSessionId() { return String(generation); },
  saveTokens(access: string, refresh: string, expected?: string | null) {
    const captured = generation;
    return mutate(async () => {
      if (expected != null && expected !== String(generation)) return;
      await write(ACCESS, access); await write(REFRESH, refresh);
    }, captured);
  },
  clearTokens() {
    generation++;
    return mutate(async () => { await remove(ACCESS); await remove(REFRESH); await remove(USER); });
  },
  getAccessToken: () => read(ACCESS),
  getRefreshToken: () => read(REFRESH),
  saveUser(user: any) { return mutate(() => write(USER, JSON.stringify(user))); },
  async getUser() { try { const value = await read(USER); return value ? JSON.parse(value) : null; } catch { return null; } },
};
