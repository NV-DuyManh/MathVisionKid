import { createWebSession } from '../../../../../packages/shared-contracts/src/webSession';

export const teacherSession = createWebSession('teacher', ['accessToken', 'refreshToken', 'teacher_session_id']);
const notify = () => window.dispatchEvent(new Event('teacher_auth_changed'));
export async function establishTeacherSession(path: string, body: object) {
  const id = await teacherSession.establish(path, body);
  notify();
  return id;
}
export const AuthTokenStore = {
  getSessionId: teacherSession.getSessionId,
  hasSession: teacherSession.hasSession,
  clearTokens() {
    teacherSession.clearSession();
    notify();
  },
};
teacherSession.onExpired(notify);
