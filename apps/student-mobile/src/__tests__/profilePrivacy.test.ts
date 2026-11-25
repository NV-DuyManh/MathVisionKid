import apiClient from '../services/api/apiClient';
import { profileApi, type ProfileEdit, type StudentProfile } from '../features/student-profile/profileApi';
jest.mock('../services/api/apiClient', () => ({ put: jest.fn(), get: jest.fn() }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: { getSessionId: jest.fn().mockResolvedValue('profile-owner-session') } }));
const edit: ProfileEdit = { displayName: 'Minh Anh', avatar: 'moon', selectedTitle: null, leaderboardVisible: true, leaderboardNameHidden: false };
const profile = { ...edit } as StudentProfile;
beforeEach(() => { jest.clearAllMocks(); });

it.each([true, false])('preserves an explicitly selected name privacy value %s', async hidden => {
  const response = { ...profile, leaderboardNameHidden: hidden };
  jest.mocked(apiClient.put).mockResolvedValue({ data: response });
  await expect(profileApi.update({ ...edit, leaderboardNameHidden: hidden }, new AbortController().signal)).resolves.toEqual(response);
  expect(apiClient.get).not.toHaveBeenCalled();
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
