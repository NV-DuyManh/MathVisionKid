import React from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';
import { AuthContext, AuthProvider } from '../AuthContext';
import { authApi } from '../../services/api/authApi';
import { tokenStorage } from '../../services/auth/tokenStorage';
import { sessionEvents } from '../../services/auth/sessionEvents';
const mockReplace = jest.fn();
jest.mock('expo-router', () => ({ useRouter: () => ({ replace: mockReplace }) }));
jest.mock('../../services/auth/tokenStorage', () => ({ tokenStorage: {
  getAccessToken: jest.fn(), getRefreshToken: jest.fn(), getUser: jest.fn(),
  saveTokens: jest.fn(), saveUser: jest.fn(), clearTokens: jest.fn(),
} }));
jest.mock('../../services/api/authApi', () => ({ authApi: { login: jest.fn(), getMe: jest.fn(), logout: jest.fn() } }));
jest.mock('../../services/api/apiClient', () => ({ __esModule: true, default: { defaults: { headers: { common: {} } } } }));
jest.mock('../../features/recognition/api/RecognitionService', () => ({ RecognitionService: { clearCache: jest.fn() } }));
jest.mock('../../features/recognition/state/recognitionDraftStore', () => ({ recognitionDraftStore: { clearDraft: jest.fn() } }));
jest.mock('../../features/recognition/analytics/recognitionAnalyticsStore', () => ({ recognitionAnalyticsStore: { setUserScope: jest.fn() } }));
let context: React.ContextType<typeof AuthContext>;
function Probe() { context = React.useContext(AuthContext); return null; }
let root: ReactTestRenderer;
const student = { userId: 'student-a', role: 'STUDENT', active: true, displayName: 'Student A' };
async function mount() { await act(async () => { root = create(<AuthProvider><Probe /></AuthProvider>); }); }
beforeEach(() => {
  jest.clearAllMocks();
  (tokenStorage.getAccessToken as jest.Mock).mockResolvedValue(null);
  (tokenStorage.getRefreshToken as jest.Mock).mockResolvedValue(null);
  (authApi.login as jest.Mock).mockResolvedValue({ accessToken: 'test-access', refreshToken: 'test-refresh' });
});
afterEach(async () => { if (root) await act(async () => root.unmount()); });
test.each(['ADMIN', 'TEACHER'])('%s login cannot open Student Dashboard', async role => {
  (authApi.getMe as jest.Mock).mockResolvedValue({ ...student, role });
  await mount();
  await act(async () => { await expect(context!.login({ email: 'account@overhaul.test', password: 'test-value' })).rejects.toThrow('trình duyệt'); });
  expect(context!.isAuthenticated).toBe(false);
  expect(mockReplace).not.toHaveBeenCalledWith('/(tabs)');
  expect(tokenStorage.clearTokens).toHaveBeenCalled();
});
test('inactive student is rejected and valid student is admitted', async () => {
  await mount();
  (authApi.getMe as jest.Mock).mockResolvedValue({ ...student, active: false });
  await act(async () => { await expect(context!.login({})).rejects.toThrow(); });
  expect(context!.isAuthenticated).toBe(false);
  (authApi.getMe as jest.Mock).mockResolvedValue(student);
  await act(async () => { await context!.login({}); });
  expect(context!.isAuthenticated).toBe(true);
  expect(mockReplace).toHaveBeenLastCalledWith('/(tabs)');
});
test.each(['ADMIN', 'offline'])('cached student cannot override restored %s authority', async result => {
  (tokenStorage.getAccessToken as jest.Mock).mockResolvedValue('stored-access');
  (tokenStorage.getUser as jest.Mock).mockResolvedValue(student);
  if (result === 'offline') (authApi.getMe as jest.Mock).mockRejectedValue(new Error('Offline'));
  else (authApi.getMe as jest.Mock).mockResolvedValue({ ...student, role: result });
  await mount();
  expect(context!.isAuthenticated).toBe(false);
  expect(context!.user).toBeNull();
  expect(tokenStorage.saveUser).not.toHaveBeenCalled();
  expect(context!.sessionError).toMatch(result === 'ADMIN' ? /cổng quản trị/ : /kiểm tra kết nối/);
});
test('expired refresh removes the mounted student session', async () => {
  await mount();
  (authApi.getMe as jest.Mock).mockResolvedValue(student);
  await act(async () => { await context!.login({}); });
  await act(async () => { sessionEvents.expired(); });
  expect(context!.isAuthenticated).toBe(false);
  expect(mockReplace).toHaveBeenLastCalledWith('/login');
});
test('a late old /me result cannot replace the next login', async () => {
  await mount();
  let finishOld: (value: unknown) => void = () => {};
  (authApi.getMe as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finishOld = resolve; })).mockResolvedValueOnce({ ...student, userId: 'student-b' });
  let old: Promise<void>;
  await act(async () => { old = context!.login({}); await Promise.resolve(); });
  await act(async () => { await context!.login({}); });
  await act(async () => { finishOld({ ...student, role: 'ADMIN' }); await expect(old!).rejects.toThrow(); });
  expect(context!.user.userId).toBe('student-b');
});
