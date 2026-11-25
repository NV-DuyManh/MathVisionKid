import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import AchievementsScreen from '../app/(tabs)/achievements';
import { AuthContext } from '../context/AuthContext';
import { profileApi } from '../features/student-profile/profileApi';
import { Platform, ScrollView, StyleSheet } from 'react-native';

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../features/student-profile/profileApi', () => ({ profileApi: { get: jest.fn(), leaderboard: jest.fn() } }));

it('shows registered-grade ranking, keeps public names and handles an empty name', async () => {
  const rank = { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 };
  jest.mocked(profileApi.get).mockResolvedValue({
    displayName: 'Bạn nhỏ', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
    leaderboardVisible: true, leaderboardNameHidden: false, publicAlias: 'Hươu Sao', selectedTitle: null, stars: 1,
    rank, highestRank: 'Sắt III', position: 1,
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
  const scroll = tree!.root.findByType(ScrollView);
  expect(scroll.props.showsVerticalScrollIndicator).toBe(false);
  expect(StyleSheet.flatten(scroll.props.contentContainerStyle).paddingTop).toBe(12);
  expect(words).toContain('Bạn chăm học');
  expect(words).toContain('Em');
  expect(words).not.toContain('Toàn hệ thống');
  expect(profileApi.leaderboard).toHaveBeenCalledWith(undefined, expect.any(AbortSignal));
  act(() => tree!.unmount());
});

it('keeps web privacy state explicit and protects the self row while preference responses settle', async () => {
  const previousPlatform = Platform.OS;
  Platform.OS = 'web';
  const rank = { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 };
  const profile = {
    displayName: 'Tên riêng của em', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
    leaderboardVisible: true, leaderboardNameHidden: true, publicAlias: 'Hươu Sao', selectedTitle: null, stars: 1,
    rank, highestRank: 'Sắt III', position: 1,
    stats: { lessons: 1, quizzes: 0, games: 0, days: 1, week: 1, month: 1, today: 1, streak: 1 }, titles: [], history: [],
  };
  jest.mocked(profileApi.get).mockResolvedValue(profile);
  jest.mocked(profileApi.leaderboard).mockResolvedValue({
    gradeLevel: 5, ownPosition: 1, entries: [{ position: 1, alias: profile.displayName, avatar: 'star', stars: 2, rank, self: true }],
  });
  const auth = { user: { id: 'private-student' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
  let tree: TestRenderer.ReactTestRenderer | undefined;
  try {
    await act(async () => { tree = TestRenderer.create(<AuthContext.Provider value={auth}><AchievementsScreen /></AuthContext.Provider>); });
    const words = () => tree!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(words()).toContain('Em đang dùng bí danh');
    expect(words()).toContain('Hươu Sao');
    expect(words()).not.toContain(profile.displayName);
    await act(async () => { tree!.unmount(); });
    tree = undefined;
    jest.mocked(profileApi.get).mockResolvedValue({ ...profile, leaderboardVisible: false });
    await act(async () => { tree = TestRenderer.create(<AuthContext.Provider value={auth}><AchievementsScreen /></AuthContext.Provider>); });
    expect(words()).toContain('Em đang ẩn khỏi bảng xếp hạng');
    expect(words()).toContain('Em chưa tham gia bảng xếp hạng');
    expect(tree!.root.findAll(node => node.props.testID === 'leaderboard-entry')).toHaveLength(0);
  } finally {
    if (tree) act(() => tree!.unmount());
    Platform.OS = previousPlatform;
  }
});

it('retries a mismatched grade and reveals the private self row beyond the first page on web', async () => {
  const previousPlatform = Platform.OS;
  Platform.OS = 'web';
  const rank = { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 };
  const profile = {
    displayName: 'Tên riêng của em', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
    leaderboardVisible: true, leaderboardNameHidden: true, publicAlias: 'Hươu Sao', selectedTitle: null, stars: 1,
    rank, highestRank: 'Sắt III', position: 12,
    stats: { lessons: 1, quizzes: 0, games: 0, days: 1, week: 1, month: 1, today: 1, streak: 1 }, titles: [], history: [],
  };
  jest.mocked(profileApi.get).mockResolvedValue(profile);
  const entries = Array.from({ length: 12 }, (_, index) => ({
    position: index + 1, alias: index === 11 ? profile.displayName : `Bí danh ${index + 1}`, avatar: 'star', stars: 20 - index, rank, self: index === 11,
  }));
  jest.mocked(profileApi.leaderboard).mockResolvedValue({ gradeLevel: 4, ownPosition: 12, entries });
  const auth = { user: { id: 'grade-five-student' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
  let tree: TestRenderer.ReactTestRenderer | undefined;
  try {
    await act(async () => { tree = TestRenderer.create(<AuthContext.Provider value={auth}><AchievementsScreen /></AuthContext.Provider>); });
    const button = (label: string) => tree!.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
    expect(tree!.root.findAll(node => node.props.testID === 'leaderboard-entry')).toHaveLength(0);
    jest.mocked(profileApi.leaderboard).mockResolvedValue({ gradeLevel: 5, ownPosition: 12, entries });
    await act(async () => { button('Tải lại bảng xếp hạng đúng khối lớp').props.onPress(); });
    expect(tree!.root.findAll(node => typeof node.type === 'string' && node.props.testID === 'leaderboard-entry')).toHaveLength(10);
    act(() => { button('Xem vị trí của em').props.onPress(); });
    expect(tree!.root.findAll(node => typeof node.type === 'string' && node.props.testID === 'leaderboard-entry')).toHaveLength(12);
    const words = tree!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(words).toContain('Hươu Sao');
    expect(words).not.toContain(profile.displayName);
  } finally {
    if (tree) act(() => tree!.unmount());
    Platform.OS = previousPlatform;
  }
});
