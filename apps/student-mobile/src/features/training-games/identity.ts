import { isStudentUuid } from '@mathvisionkid/training-games';

/** /me returns userId UUID; Student inherits that same primary key in the backend. */
export function trainingStudentId(user: unknown, authenticated: boolean): string | null {
  if (!authenticated || !user || typeof user !== 'object') return null;
  const record = user as Record<string, unknown>;
  if (record.active === false || (record.role !== 'STUDENT' && record.role !== 'ROLE_STUDENT')) return null;
  const id = record.userId ?? record.id;
  return isStudentUuid(id) ? id.toLowerCase() : null;
}

export type TrainingAccess =
  | { kind: 'student'; studentId: string }
  | { kind: 'trial'; owner: string }
  | { kind: 'blocked'; message: string };

// An opaque, non-UUID owner ties trial lifetime to the authenticated context.
// Never pass a mock ID (which may contain an email) to gameplay or diagnostics.
const trialOwners = new WeakMap<object, string>();
let trialSequence = 0;
export function trainingAccess(user: unknown, authenticated: boolean, development = __DEV__): TrainingAccess {
  const studentId = trainingStudentId(user, authenticated);
  if (studentId) return { kind: 'student', studentId };
  if (development && authenticated && user && typeof user === 'object') {
    const record = user as Record<string, unknown>;
    const id = record.userId ?? record.id;
    if (record.active !== false && (record.role === 'STUDENT' || record.role === 'ROLE_STUDENT') && typeof id === 'string' && id.startsWith('mock_student_')) {
      let owner = trialOwners.get(user);
      if (!owner) { owner = `development-trial:${++trialSequence}`; trialOwners.set(user, owner); }
      return { kind: 'trial', owner };
    }
  }
  return { kind: 'blocked', message: 'Vui lòng đăng nhập bằng tài khoản học sinh để lưu kết quả.' };
}
