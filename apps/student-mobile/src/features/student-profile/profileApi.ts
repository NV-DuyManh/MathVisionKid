import apiClient from '../../services/api/apiClient';

export type Rank = { name: string; masterStars: number; progress: number; goal: number };
export type StudentTitle = { id: string; name: string; rarity: string; description: string; progress: number; goal: number; unlocked: boolean };
export type StudentProfile = {
  displayName: string;
  gradeLevel: number | null;
  joinedAt: string | null;
  classrooms: { id: string; name: string }[];
  avatar: string;
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
export type ProfileEdit = Pick<StudentProfile, 'displayName' | 'avatar' | 'leaderboardVisible' | 'selectedTitle'>;
export type Leaderboard = {
  ownPosition: number | null;
  entries: { position: number; alias: string; avatar: string; stars: number; rank: Rank; self: boolean }[];
};
export type GameRun = { id: string; question: number; prompt: string | null; correct: number; length: number; completed: boolean; stars: number };
const root = '/student';
export const profileApi = {
  async get(signal: AbortSignal) {
    return (await apiClient.get<StudentProfile>(root + '/profile', { signal })).data;
  },
  async update(edit: ProfileEdit, signal: AbortSignal) {
    return (await apiClient.put<StudentProfile>(root + '/profile', edit, { signal })).data;
  },
  async leaderboard(classroom: string | undefined, signal: AbortSignal) {
    return (await apiClient.get<Leaderboard>(root + '/leaderboard', { params: { classroom }, signal })).data;
  },
  async startGame(signal: AbortSignal) {
    return (await apiClient.post<GameRun>(root + '/game-runs', undefined, { signal })).data;
  },
  async answer(run: GameRun, answer: number, signal: AbortSignal) {
    return (await apiClient.post<GameRun>(root + '/game-runs/' + run.id + '/answers', { question: run.question, answer }, { signal })).data;
  },
};
