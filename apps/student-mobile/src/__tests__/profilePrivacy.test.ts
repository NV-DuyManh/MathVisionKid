import apiClient from '../services/api/apiClient';
import { profileApi, type ProfileEdit, type StudentProfile } from '../features/student-profile/profileApi';
jest.mock('../services/api/apiClient', () => ({ put: jest.fn(), get: jest.fn() }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: { getSessionId: jest.fn().mockResolvedValue('profile-owner-session') } }));
const edit: ProfileEdit = { displayName: 'Minh Anh', avatar: 'moon', selectedTitle: null, leaderboardVisible: true, leaderboardNameHidden: false };
const profile = {
  ...edit, leaderboardPhotoVisible: false, classrooms: [], titles: [], history: [], publicAlias: 'Hươu Sao',
  stars: 0, rank: { name: 'Sắt III' }, stats: { lessons: 0 },
} as StudentProfile;
beforeEach(() => { jest.clearAllMocks(); });

it('accepts current server privacy for a name-only edit', async () => {
  const nameEdit = { displayName: 'Sao Sáng', avatar: 'moon', selectedTitle: null };
  const response = { ...profile, ...nameEdit, leaderboardVisible: false, leaderboardNameHidden: true };
  jest.mocked(apiClient.put).mockResolvedValue({ data: response });
  await expect(profileApi.update(nameEdit, new AbortController().signal)).resolves.toEqual(response);
  expect(apiClient.get).not.toHaveBeenCalled();
});

it.each([{}, { displayName: 'Minh Anh', avatar: 'moon' }])('checks a partial name-only response %j against the current profile', async partial => {
  jest.mocked(apiClient.put).mockResolvedValue({ data: partial });
  jest.mocked(apiClient.get).mockResolvedValue({ data: profile });
  const signal = new AbortController().signal;
  await expect(profileApi.update({ displayName: 'Minh Anh' }, signal)).resolves.toEqual(profile);
  expect(apiClient.get).toHaveBeenCalledTimes(1);

  jest.mocked(apiClient.get).mockResolvedValue({ data: partial });
  await expect(profileApi.update({ displayName: 'Minh Anh' }, signal)).rejects.toMatchObject({ code: 'PROFILE_PRIVACY_UNCONFIRMED' });
});

it.each([true, false])('preserves an explicitly selected name privacy value %s', async hidden => {
  const response = { ...profile, leaderboardNameHidden: hidden };
  jest.mocked(apiClient.put).mockResolvedValue({ data: response });
  await expect(profileApi.update({ ...edit, leaderboardNameHidden: hidden }, new AbortController().signal)).resolves.toEqual(response);
  expect(apiClient.get).not.toHaveBeenCalled();
});

it('verifies that the server saved the new name even if its response has all required fields', async () => {
  const nameEdit = { displayName: 'Sao Sáng' };
  const updated = { ...profile, ...nameEdit };
  const signal = new AbortController().signal;
  jest.mocked(apiClient.put).mockResolvedValue({ data: profile });
  jest.mocked(apiClient.get).mockResolvedValue({ data: updated });
  await expect(profileApi.update(nameEdit, signal)).resolves.toEqual(updated);
  expect(apiClient.get).toHaveBeenCalledTimes(1);

  jest.mocked(apiClient.get).mockResolvedValue({ data: profile });
  await expect(profileApi.update(nameEdit, signal)).rejects.toMatchObject({ code: 'PROFILE_NAME_UNCONFIRMED' });
});

it('confirms persisted false when an older update response omits the field', async () => {
  const { leaderboardNameHidden: _hidden, ...legacy } = profile;
  jest.mocked(apiClient.put).mockResolvedValue({ data: legacy });
  jest.mocked(apiClient.get).mockResolvedValue({ data: profile });
  const signal = new AbortController().signal;
  await expect(profileApi.update(edit, signal)).resolves.toEqual(profile);
  expect(apiClient.get).toHaveBeenCalledWith('/student/profile', { signal, _identity: 'profile-owner-session', headers: { 'X-MathVision-Client': 'student-rank-v2' } });
});

it.each([undefined, null, true])('rejects an unconfirmed saved name setting %s instead of silently turning it on', async hidden => {
  const response = { ...profile, leaderboardNameHidden: hidden };
  jest.mocked(apiClient.put).mockResolvedValue({ data: response });
  jest.mocked(apiClient.get).mockResolvedValue({ data: response });
  await expect(profileApi.update(edit, new AbortController().signal)).rejects.toMatchObject({ code: 'PROFILE_PRIVACY_UNCONFIRMED' });
});

it('also rejects a stored participation setting that differs from the explicit selection', async () => {
  jest.mocked(apiClient.put).mockResolvedValue({ data: { ...profile, leaderboardVisible: false } });
  jest.mocked(apiClient.get).mockResolvedValue({ data: { ...profile, leaderboardVisible: false } });
  await expect(profileApi.update(edit, new AbortController().signal)).rejects.toMatchObject({ code: 'PROFILE_PRIVACY_UNCONFIRMED' });
});
