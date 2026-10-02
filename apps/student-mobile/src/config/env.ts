import { resolveApiBaseUrl } from './apiResolver';

export const ENV = {
  get API_BASE_URL(): string { return resolveApiBaseUrl(); },
  USE_MOCK: process.env.EXPO_PUBLIC_USE_MOCK === 'true',
};
