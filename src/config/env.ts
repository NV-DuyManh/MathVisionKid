export const ENV = {
  // Use EXPO_PUBLIC_API_BASE_URL if defined, otherwise default to a LAN IP for device testing,
  // or localhost for iOS simulator / web.
  // Example for LAN: 'http://192.168.1.x:8080/api/v1'
  // Remember to replace localhost with your actual machine's local IP if testing on a physical Android device.
  API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL || 'http://10.0.2.2:8080/api/v1',
  USE_MOCK: process.env.EXPO_PUBLIC_USE_MOCK === 'true' || false,
};
