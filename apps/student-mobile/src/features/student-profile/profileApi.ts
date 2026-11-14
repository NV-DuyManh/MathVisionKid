import apiClient from '../../services/api/apiClient';
import { Platform } from 'react-native';
import { tokenStorage } from '../../services/auth/tokenStorage';

export type Rank = { name: string; masterStars: number; progress: number; goal: number };
export type StudentTitle = { id: string; name: string; rarity: string; description: string; progress: number; goal: number; unlocked: boolean };
export type StudentProfile = {
  displayName: string;
  gradeLevel: number | null;
  joinedAt: string | null;
  classrooms: { id: string; name: string }[];
  avatar: string;
  avatarPhoto?: string | null;
  passwordLoginAvailable?: boolean;
  leaderboardVisible: boolean;
  publicAlias: string;
  selectedTitle: string | null;
  stars: number;
  rank: Rank;
  highestRank: string;
  position: number | null;
  stats: { lessons: number; quizzes: number; games: number; days: number; week: number; month: number; today: number; streak: number };
  titles: StudentTitle[];
  history: { source: 'LESSON' | 'QUIZ' | 'GAME'; completedAt: string; stars: number }[];
};
export type ProfileEdit = Pick<StudentProfile, 'displayName' | 'avatar' | 'leaderboardVisible' | 'selectedTitle'> & { removePhoto?: boolean };
export type Leaderboard = {
  ownPosition: number | null;
  entries: { position: number; alias: string; avatar: string; stars: number; rank: Rank; self: boolean }[];
};
export type RankMilestone = { name: string; stars: number; top: number | null };
export type GameMode = 'ARITHMETIC_QUEST' | 'RACE_TO_FINISH' | 'TERRAIN_RACING' | 'ENERGY_DEFENSE' | 'PLANET_RESCUE' | 'BLOCK_ISLAND';
export type GameRun = {
  id: string; question: number; prompt: string | null; correct: number; length: number; completed: boolean; stars: number;
  rewardStatus?: 'AWARDED' | 'REPEAT' | 'DAILY_LIMIT' | 'GAME_LIMIT' | 'UNAVAILABLE' | null;
};
const root = '/student';
export const profileApi = {
  async get(signal: AbortSignal) {
    return (await apiClient.get<StudentProfile>(root + '/profile', { signal })).data;
  },
  async update(edit: ProfileEdit, signal: AbortSignal) {
    const config = { signal, _identity: await tokenStorage.getSessionId() };
    return (await apiClient.put<StudentProfile>(root + '/profile', edit, config)).data;
  },
  async uploadPhoto(uri: string, signal: AbortSignal, expectedSession?: string | null) {
    const identity = expectedSession === undefined ? await tokenStorage.getSessionId() : expectedSession;
    const form = new FormData();
    if (Platform.OS === 'web') {
      const response = await fetch(uri, { signal });
      if (!response.ok) throw new Error('Chưa mở được ảnh đã chọn.');
      form.append('file', await response.blob(), 'avatar.png');
    } else form.append('file', { uri, name: 'avatar.png', type: 'image/png' } as any);
    const config = { signal, _identity: identity, transformRequest: [(value: unknown) => value], headers: { 'Content-Type': undefined } };
    return (await apiClient.put<StudentProfile>(root + '/profile/photo', form, config)).data;
  },
  async leaderboard(classroom: string | undefined, signal: AbortSignal) {
    return (await apiClient.get<Leaderboard>(root + '/leaderboard', { params: { classroom }, signal })).data;
  },
  async rankMilestones(signal: AbortSignal) {
    return (await apiClient.get<RankMilestone[]>(root + '/rank-milestones', { signal })).data;
  },
  async startGame(mode: GameMode, signal: AbortSignal, identity: string | null) {
    const config = { params: { mode }, signal, _identity: identity };
    return (await apiClient.post<GameRun>(root + '/game-runs', undefined, config)).data;
  },
  async readGame(id: string, signal: AbortSignal, identity: string | null) {
    const config = { signal, _identity: identity };
    return (await apiClient.get<GameRun>(root + '/game-runs/' + id, config)).data;
  },
  async answer(run: GameRun, answer: number, signal: AbortSignal, identity: string | null) {
    const config = { signal, _identity: identity };
    return (await apiClient.post<GameRun>(root + '/game-runs/' + run.id + '/answers', { question: run.question, answer }, config)).data;
  },
};
