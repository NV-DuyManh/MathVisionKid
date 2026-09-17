
import { resolveApiBaseUrl } from './apiResolver';

export const ENV = {
  // Use EXPO_PUBLIC_API_BASE_URL if defined, otherwise dynamically resolve LAN IP
  // or use localhost/127.0.0.1 for web / iOS simulator.
  API_BASE_URL: resolveApiBaseUrl(),
  USE_MOCK: process.env.EXPO_PUBLIC_USE_MOCK === 'true',
};
