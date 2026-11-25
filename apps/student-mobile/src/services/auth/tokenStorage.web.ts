import { createWebSession } from '../../../../../packages/shared-contracts/src/webSession';

const USER = 'mathvision_student_web_user_v1';
const DRAFT_TAB = 'mathvision_photo_tab_id';
if (typeof window !== 'undefined' && window.opener) {
  try {
    if (window.opener.sessionStorage.getItem(DRAFT_TAB) === window.sessionStorage.getItem(DRAFT_TAB)) {
      window.sessionStorage.removeItem(DRAFT_TAB);
    }
  } catch { /* Cross-origin opener storage is inaccessible. */ }
}
export const studentSession = createWebSession('portal', [
  'portal_access_token', 'portal_refresh_token', 'portal_session_id',
], 60000);

export const tokenStorage = {
  async getSessionId() { return studentSession.getSessionId(); },
  getDraftScopeId() {
    const session = studentSession.getSessionId();
    if (!session || typeof window === 'undefined') return null;
    let tab = window.sessionStorage.getItem(DRAFT_TAB);
    if (!tab) {
      tab = Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');
      window.sessionStorage.setItem(DRAFT_TAB, tab);
    }
    return `${session}:${tab}`;
  },
  async clearTokens() { studentSession.clearSession(); },
  async saveUser(user: unknown) { if (typeof window !== 'undefined') window.sessionStorage.setItem(USER, JSON.stringify(user)); },
  async getUser() { try { const value = typeof window === 'undefined' ? null : window.sessionStorage.getItem(USER); return value ? JSON.parse(value) : null; } catch { return null; } },
};
