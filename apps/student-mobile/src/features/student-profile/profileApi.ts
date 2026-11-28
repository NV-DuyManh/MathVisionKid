import apiClient from '../../services/api/apiClient';
import { Platform } from 'react-native';
import { tokenStorage } from '../../services/auth/tokenStorage';

export type Rank = { name: string; masterStars: number; progress: number; goal: number; scheme?: number };
export type StudentTitle = { id: string; name: string; rarity: string; description: string; progress: number; goal: number; unlocked: boolean };
export type StarActivity = { source: 'LESSON' | 'QUIZ' | 'GAME'; completedAt: string; stars: number };
type StarHistoryPage = { entries: StarActivity[]; page: number; totalPages: number };
export type StudentProfile = {
  displayName: string;
  gradeLevel: number | null;
  joinedAt: string | null;
  classrooms: { id: string; name: string }[];
  avatar: string;
  avatarPhoto?: string | null;
  passwordLoginAvailable?: boolean;
  googleLinked?: boolean;
  leaderboardVisible: boolean;
  leaderboardNameHidden?: boolean;
  leaderboardPhotoVisible?: boolean;
  privacyRevision?: string;
  publicAlias: string;
  selectedTitle: string | null;
  stars: number;
  rank: Rank;
  highestRank: string;
  position: number | null;
  stats: { lessons: number; quizzes: number; games: number; days: number; week: number; month: number; today: number; streak: number };
  titles: StudentTitle[];
  history: StarActivity[];
};
export type ProfileEdit = Partial<Pick<StudentProfile, 'displayName' | 'avatar' | 'selectedTitle' |
  'leaderboardVisible' | 'leaderboardNameHidden' | 'leaderboardPhotoVisible' | 'privacyRevision'>>
  & { removePhoto?: boolean };
export type Leaderboard = {
  gradeLevel?: number | null;
  ownPosition: number | null;
  entries: { position: number; alias: string; avatar: string; stars: number; rank: Rank; self: boolean; avatarPhoto?: string }[];
};
export type RankMilestone = { name: string; stars: number; top: number | null; scheme?: number };
export type GameMode = 'ARITHMETIC_QUEST' | 'RACE_TO_FINISH' | 'TERRAIN_RACING' | 'ENERGY_DEFENSE' | 'PLANET_RESCUE' | 'BLOCK_ISLAND';
export type GameRun = {
  id: string; question: number; prompt: string | null; correct: number; length: number; completed: boolean; stars: number;
  rewardStatus?: 'AWARDED' | 'REPEAT' | 'DAILY_LIMIT' | 'GAME_LIMIT' | 'UNAVAILABLE' | null;
};
const root = '/student';
const rankHeaders = { 'X-MathVision-Client': 'student-rank-v2' };

const privacyRevisionPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const statFields = ['lessons', 'quizzes', 'games', 'days', 'week', 'month', 'today', 'streak'] as const;
const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
const isNumber = (value: unknown) => typeof value === 'number' && Number.isFinite(value);
const isNullableString = (value: unknown) => value === null || typeof value === 'string';

function isProfile(value: unknown): value is Omit<StudentProfile, 'privacyRevision'> & { privacyRevision?: unknown } {
  if (!isRecord(value)) return false;
  const { rank, stats } = value;
  return typeof value.displayName === 'string' && typeof value.avatar === 'string'
    && typeof value.leaderboardVisible === 'boolean' && typeof value.leaderboardNameHidden === 'boolean'
    && typeof value.leaderboardPhotoVisible === 'boolean' && typeof value.publicAlias === 'string'
    && (value.gradeLevel === null || isNumber(value.gradeLevel)) && isNullableString(value.joinedAt)
    && isNullableString(value.selectedTitle) && (value.avatarPhoto === undefined || isNullableString(value.avatarPhoto))
    && (value.passwordLoginAvailable === undefined || typeof value.passwordLoginAvailable === 'boolean')
    && (value.googleLinked === undefined || typeof value.googleLinked === 'boolean')
    && isNumber(value.stars) && typeof value.highestRank === 'string' && (value.position === null || isNumber(value.position))
    && isRecord(rank) && typeof rank.name === 'string' && isNumber(rank.masterStars)
    && isNumber(rank.progress) && isNumber(rank.goal) && (rank.scheme === undefined || isNumber(rank.scheme))
    && isRecord(stats) && statFields.every(field => isNumber(stats[field]))
    && Array.isArray(value.classrooms) && value.classrooms.every(room => isRecord(room) && typeof room.id === 'string' && typeof room.name === 'string')
    && Array.isArray(value.history) && value.history.every(activity => isRecord(activity)
      && (activity.source === 'LESSON' || activity.source === 'QUIZ' || activity.source === 'GAME')
      && typeof activity.completedAt === 'string' && isNumber(activity.stars))
    && Array.isArray(value.titles) && value.titles.every(title => isRecord(title) && typeof title.id === 'string'
      && typeof title.name === 'string' && typeof title.rarity === 'string' && typeof title.description === 'string'
      && isNumber(title.progress) && isNumber(title.goal) && typeof title.unlocked === 'boolean');
}

function parseProfile(value: unknown): StudentProfile | undefined {
  if (!isProfile(value)) return undefined;
  const { privacyRevision, ...profile } = value;
  return typeof privacyRevision === 'string' && privacyRevisionPattern.test(privacyRevision)
    ? { ...profile, privacyRevision }
    : profile;
}

type ProfileRequest = { signal: AbortSignal; _identity?: string | null; headers: typeof rankHeaders };

async function readProfile(config: ProfileRequest) {
  return parseProfile((await apiClient.get<unknown>(root + '/profile', config)).data);
}

async function readPrivacySnapshot(config: ProfileRequest) {
  const profile = await readProfile(config);
  if (!profile?.privacyRevision) {
    throw new Error('Chưa tải được quyền riêng tư hiện tại.');
  }
  return profile;
}

export const profileApi = {
  async get(signal: AbortSignal) {
    const profile = await readProfile({ signal, headers: rankHeaders });
    if (!profile) throw new Error('Chưa tải được hồ sơ học sinh.');
    return profile;
  },
  async reloadPrivacy(signal: AbortSignal) {
    return readPrivacySnapshot({ signal, _identity: await tokenStorage.getSessionId(), headers: rankHeaders });
  },
  async update(edit: ProfileEdit, signal: AbortSignal) {
    const config = { signal, _identity: await tokenStorage.getSessionId(), headers: rankHeaders };
    let next: StudentProfile | undefined;
    try {
      next = parseProfile((await apiClient.put<unknown>(root + '/profile', edit, config)).data);
    } catch (error) {
      const response = (error as { response?: { status?: number; data?: { error?: { code?: string } } } } | null)?.response;
      if (response?.status !== 409 || response.data?.error?.code !== 'PROFILE_PRIVACY_CONFLICT') throw error;
      const currentProfile = await readPrivacySnapshot(config).catch(() => undefined);
      throw Object.assign(new Error('Lựa chọn quyền riêng tư đã thay đổi.'), {
        code: 'PROFILE_PRIVACY_CONFLICT', currentProfile,
      });
    }
    const matchesPrivacy = (value: StudentProfile | undefined): value is StudentProfile => value !== undefined
      && (edit.privacyRevision === undefined || value.privacyRevision !== undefined)
      && (edit.leaderboardVisible === undefined || value.leaderboardVisible === edit.leaderboardVisible)
      && (edit.leaderboardNameHidden === undefined || value.leaderboardNameHidden === edit.leaderboardNameHidden)
      && (edit.leaderboardPhotoVisible === undefined || value.leaderboardPhotoVisible === edit.leaderboardPhotoVisible);
    // Confirm the stored edit when the update response omits fields or returns an older value.
    if (!next?.privacyRevision || !matchesPrivacy(next) || (edit.displayName !== undefined && next.displayName !== edit.displayName)) {
      next = await readProfile(config);
    }
    if (!matchesPrivacy(next)) throw Object.assign(new Error('Chưa xác nhận được quyền riêng tư đã lưu.'), { code: 'PROFILE_PRIVACY_UNCONFIRMED' });
    if (edit.displayName !== undefined && next.displayName !== edit.displayName) {
      throw Object.assign(new Error('Chưa xác nhận được tên hiển thị đã lưu.'), { code: 'PROFILE_NAME_UNCONFIRMED' });
    }
    return next;
  },
  async uploadPhoto(uri: string, signal: AbortSignal, expectedSession?: string | null) {
    const identity = expectedSession === undefined ? await tokenStorage.getSessionId() : expectedSession;
    const form = new FormData();
    if (Platform.OS === 'web') {
      const response = await fetch(uri, { signal });
      if (!response.ok) throw new Error('Chưa mở được ảnh đã chọn.');
      form.append('file', await response.blob(), 'avatar.png');
    } else form.append('file', { uri, name: 'avatar.png', type: 'image/png' } as any);
    const config = { signal, _identity: identity, transformRequest: [(value: unknown) => value], headers: { ...rankHeaders, 'Content-Type': undefined } };
    const updated = parseProfile((await apiClient.put<unknown>(root + '/profile/photo', form, config)).data);
    const profile = updated?.privacyRevision ? updated : await readProfile({ signal, _identity: identity, headers: rankHeaders });
    if (!profile?.avatarPhoto || profile.leaderboardPhotoVisible) throw new Error('Chưa xác nhận được ảnh đã cập nhật.');
    return profile;
  },
  async leaderboard(classroom: string | undefined, signal: AbortSignal, allGrades?: true) {
    return (await apiClient.get<Leaderboard>(root + '/leaderboard', { params: { classroom, allGrades }, signal, headers: rankHeaders })).data;
  },
  async starHistory(page: number, signal: AbortSignal) {
    return (await apiClient.get<StarHistoryPage>(root + '/star-history', { params: { page }, signal })).data;
  },
  async rankMilestones(signal: AbortSignal) {
    return (await apiClient.get<RankMilestone[]>(root + '/rank-milestones', { signal, headers: rankHeaders })).data;
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
