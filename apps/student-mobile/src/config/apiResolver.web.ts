export interface ResolveOptions { manualOverride?: string }

export function resolveApiBaseUrl(options?: ResolveOptions | string): string {
  const configured = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (__DEV__) {
    const override = typeof options === 'string' ? options : options?.manualOverride;
    return (override || configured || 'http://127.0.0.1:8080/api/v1').replace(/\/+$/, '');
  }
  if (!configured) throw new Error('The student website requires its configured service address.');
  const url = new URL(configured);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      /^(localhost|127\.|\[?::1\]?)/i.test(url.hostname) || !url.hostname.includes('.') ||
      !url.pathname.replace(/\/+$/, '').endsWith('/api/v1')) {
    throw new Error('The student website service address must use public HTTPS.');
  }
  return configured.replace(/\/+$/, '');
}
