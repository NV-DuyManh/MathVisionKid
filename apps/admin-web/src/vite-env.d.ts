/// <reference types="vite/client" />

declare const __APP_CONFIG__: import('./config/environment').AppConfig;

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_PORTAL_URL?: string;
  readonly VITE_SHOW_DEV_TOOLS?: string;
  readonly VITE_USE_MOCK?: string;
}
