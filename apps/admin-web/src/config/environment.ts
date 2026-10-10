export interface AppConfig {
  readonly apiBaseUrl: string;
  readonly portalOrigin: string;
}

type WebEnv = Record<string, string | undefined>;

function readUrl(env: WebEnv, key: string, fallback: string, production: boolean, originOnly = false): string {
  const value = env[key]?.trim() || (production ? '' : fallback);
  if (!value) {
    throw new Error(`${key} is required for a production build.`);
  }

  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`${key} must be an absolute URL.`);
  }

  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new Error(`${key} must be an HTTP(S) URL without credentials, a query, or a fragment.`);
  }
  if (originOnly && url.pathname !== '/') {
    throw new Error(`${key} must be an origin without a path.`);
  }

  const host = url.hostname.toLowerCase().replace(/\.$/, '');
  const ipv4 = host.split('.').map(Number);
  const localHost = host === 'localhost' || host.endsWith('.localhost') || host.endsWith('.local') ||
    !host.includes('.') || host.startsWith('[') ||
    (ipv4.length === 4 && ipv4.every(Number.isInteger) && (
      ipv4[0] === 0 || ipv4[0] === 10 || ipv4[0] === 127 ||
      (ipv4[0] === 169 && ipv4[1] === 254) ||
      (ipv4[0] === 172 && ipv4[1] >= 16 && ipv4[1] <= 31) ||
      (ipv4[0] === 192 && ipv4[1] === 168)
    ));
  if (production && (url.protocol !== 'https:' || localHost)) {
    throw new Error(`${key} must use HTTPS with a public hostname for a production build.`);
  }

  return originOnly ? url.origin : url.href.replace(/\/+$/, '');
}

export function resolveAppConfig(env: WebEnv, production: boolean): AppConfig {
  return {
    apiBaseUrl: readUrl(env, 'VITE_API_BASE_URL', 'http://localhost:8080/api/v1', production),
    portalOrigin: readUrl(env, 'VITE_PORTAL_URL', 'http://localhost:5172', production, true),
  };
}
