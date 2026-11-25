import { createWebSession } from '../../../../../packages/shared-contracts/src/webSession';

export const adminSession = createWebSession('admin', []);
for (const key of ['mvk_admin_access_token', 'mvk_admin_refresh_token', 'mvk_admin_session_id']) {
  window.localStorage.removeItem(key);
}
export const tokenStore = {
  clearTokens: adminSession.clearSession,
  hasTokens: adminSession.hasSession,
};
adminSession.onExpired(() => window.dispatchEvent(new CustomEvent('admin_auth_required')));
