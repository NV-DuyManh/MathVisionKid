import type { AppConfig } from './environment';

export const appConfig: AppConfig = __APP_CONFIG__;

// The build config also forces these flags off for every static build.
export const showDevTools = import.meta.env.DEV && import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';
export const useMocks = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === 'true';
export const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim() ?? '';
export const facebookConfigured = [import.meta.env.VITE_FIREBASE_API_KEY, import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  import.meta.env.VITE_FIREBASE_PROJECT_ID, import.meta.env.VITE_FIREBASE_APP_ID].every(value => Boolean(value?.trim()));
