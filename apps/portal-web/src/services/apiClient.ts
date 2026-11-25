import { createWebSession } from '../../../../packages/shared-contracts/src/webSession';

export const webSession = createWebSession('portal', [
  'portal_access_token', 'portal_refresh_token', 'portal_session_id',
]);
export const { apiClient } = webSession;
export const tokenStore = {
  hasTokens: webSession.hasSession,
  getSessionId: webSession.getSessionId,
  clearTokens() {
    webSession.clearSession();
    window.dispatchEvent(new Event('portal_auth_changed'));
  },
};
webSession.onExpired(() => window.dispatchEvent(new Event('portal_auth_changed')));
