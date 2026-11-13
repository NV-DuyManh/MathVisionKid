/// <reference types="vite/client" />

declare const __APP_CONFIG__: import('./config/environment').AppConfig;

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_TEACHER_URL?: string;
  readonly VITE_ADMIN_URL?: string;
  readonly VITE_SHOW_DEV_TOOLS?: string;
  readonly VITE_USE_MOCK?: string;
  readonly VITE_GOOGLE_CLIENT_ID?: string;
  readonly VITE_FIREBASE_API_KEY?: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN?: string;
  readonly VITE_FIREBASE_PROJECT_ID?: string;
  readonly VITE_FIREBASE_APP_ID?: string;
  readonly VITE_FACEBOOK_AUTH_ENABLED?: string;
}
