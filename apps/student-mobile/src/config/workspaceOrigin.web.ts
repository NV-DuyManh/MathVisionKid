/** Trusted workspace destinations; never accept a redirect address from the login form. */
export function workspaceOrigin(role: 'TEACHER' | 'ADMIN' | 'PORTAL'): string {
  const configured = role === 'TEACHER' ? process.env.EXPO_PUBLIC_TEACHER_URL
    : role === 'ADMIN' ? process.env.EXPO_PUBLIC_ADMIN_URL : process.env.EXPO_PUBLIC_PORTAL_URL;
  const development = typeof __DEV__ !== 'undefined' && __DEV__;
  const local = development && typeof window !== 'undefined'
    ? `http://${window.location.hostname}:${role === 'TEACHER' ? 5173 : role === 'ADMIN' ? 5174 : 5172}` : '';
  try {
    const url = new URL(configured?.trim() || local);
    if ((url.protocol !== 'https:' && !(development && url.protocol === 'http:')) ||
        url.username || url.password || url.pathname !== '/' || url.search || url.hash ||
        (!development && (/^(localhost|127\.|\[?::1\]?)/i.test(url.hostname) || !url.hostname.includes('.')))) {
      throw new Error('Invalid workspace origin');
    }
    return url.origin;
  } catch {
    throw Object.assign(new Error('Chưa mở được không gian làm việc của tài khoản. Vui lòng thử lại sau.'), { code: 'VALIDATION_ERROR' });
  }
}
