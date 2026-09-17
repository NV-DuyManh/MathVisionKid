import { Stack } from 'expo-router';
import { AuthProvider } from '../context/AuthContext';
import { StatusBar } from 'expo-status-bar';
import { LogBox, Alert } from 'react-native';
import { useEffect } from 'react';
import { ENV } from '../config/env';

LogBox.ignoreLogs(['Cannot connect to Expo CLI']);

export default function RootLayout() {
  useEffect(() => {
    if (__DEV__) {
      const checkHealth = async () => {
        const baseUrl = ENV.API_BASE_URL.replace(/\/api\/v1\/?$/, '');
        const healthUrl = baseUrl + '/actuator/health';
        try {
          const res = await fetch(healthUrl, { method: 'GET' });
          if (!res.ok) {
            console.warn(`[HEALTH_CHECK] Backend health returned ${res.status}`);
          }
        } catch (e: any) {
          console.warn(`[HEALTH_CHECK] Backend unreachable:`, e.message);
          console.error(`Không kết nối được backend tại ${baseUrl}`);
          Alert.alert(
            'Lỗi kết nối máy chủ',
            `Không kết nối được backend tại ${baseUrl}`
          );
        }
      };
      checkHealth();
    }
  }, []);

  return (
    <AuthProvider>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="login" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="preview" />
        <Stack.Screen name="processing" />
        <Stack.Screen name="results" />
      </Stack>
    </AuthProvider>
  );
}
