import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import AchievementsScreen from '../app/(tabs)/achievements';
import { AuthContext } from '../context/AuthContext';
import { profileApi } from '../features/student-profile/profileApi';

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../features/student-profile/profileApi', () => ({ profileApi: { get: jest.fn(), leaderboard: jest.fn() } }));

it('shows registered-grade ranking, keeps public names and handles an empty name', async () => {
  const rank = { name: 'Đồng III', masterStars: 0, progress: 1, goal: 3 };
  jest.mocked(profileApi.get).mockResolvedValue({
    displayName: 'Bạn nhỏ', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
    leaderboardVisible: true, leaderboardNameHidden: false, publicAlias: 'Hươu Sao', selectedTitle: null, stars: 1,
    rank, highestRank: 'Đồng III', position: 1,
    stats: { lessons: 1, quizzes: 0, games: 0, days: 1, week: 1, month: 1, today: 1, streak: 1 }, titles: [], history: [],
  });
  jest.mocked(profileApi.leaderboard).mockResolvedValue({
    gradeLevel: 5, ownPosition: 1, entries: [
      { position: 1, alias: 'Minh Anh', avatar: 'star', stars: 2, rank, self: true },
      { position: 2, alias: '', avatar: 'moon', stars: 1, rank, self: false },
    ],
  });
  let tree: TestRenderer.ReactTestRenderer;
  const auth = { user: { id: 'student' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
  await act(async () => { tree = TestRenderer.create(<AuthContext.Provider value={auth}><AchievementsScreen /></AuthContext.Provider>); });
  const words = tree!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
  expect(words).toContain('Bảng xếp hạng, khối 5');
  expect(words).toContain('Minh Anh');
  expect(words).toContain('Bạn chăm học');
  expect(words).toContain('Em');
  expect(words).not.toContain('Toàn hệ thống');
  expect(profileApi.leaderboard).toHaveBeenCalledWith(undefined, expect.any(AbortSignal));
  act(() => tree!.unmount());
});
