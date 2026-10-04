import { Stack } from 'expo-router';
import { AuthProvider } from '../context/AuthContext';
import { StatusBar } from 'expo-status-bar';
import { LogBox } from 'react-native';
import { useEffect } from 'react';
import { ENV } from '../config/env';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';

SplashScreen.preventAutoHideAsync().catch(() => {});

LogBox.ignoreLogs(['Cannot connect to Expo CLI']);

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    NunitoRegular: require('../../assets/fonts/Nunito-Regular.ttf'),
    NunitoMedium: require('../../assets/fonts/Nunito-Medium.ttf'),
    NunitoSemiBold: require('../../assets/fonts/Nunito-SemiBold.ttf'),
    NunitoBold: require('../../assets/fonts/Nunito-Bold.ttf'),
    NunitoExtraBold: require('../../assets/fonts/Nunito-ExtraBold.ttf'),
    NunitoBlack: require('../../assets/fonts/Nunito-Black.ttf'),
  });
  useEffect(() => {
    if (fontsLoaded || fontError) SplashScreen.hideAsync().catch(() => {});
  }, [fontsLoaded, fontError]);
  useEffect(() => {
    if (__DEV__) {
      const checkHealth = async () => {
        const baseUrl = ENV.API_BASE_URL.replace(/\/api\/v1\/?$/, '');
        const healthUrl = baseUrl + '/actuator/health';
        try {
          const res = await fetch(healthUrl, { method: 'GET' });
          if (!res.ok) {
            console.warn(`[HEALTH_CHECK] Backend health returned ${res.status}`);
          } else {
            console.log(`[HEALTH_CHECK] Backend is UP at ${baseUrl}`);
          }
        } catch (e: any) {
          console.warn(`[HEALTH_CHECK] Backend unreachable at ${baseUrl}:`, e.message);
        }
      };
      checkHealth();
    }
  }, []);

  if (!fontsLoaded && !fontError) return null;

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
        <Stack.Screen name="gallery" />
      </Stack>
    </AuthProvider>
  );
}
