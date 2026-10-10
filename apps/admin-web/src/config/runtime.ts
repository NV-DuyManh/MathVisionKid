import type { AppConfig } from './environment';

export const appConfig: AppConfig = __APP_CONFIG__;

// The build config also forces these flags off for every static build.
export const showDevTools = import.meta.env.DEV && import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';
export const useMocks = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK !== 'false';
