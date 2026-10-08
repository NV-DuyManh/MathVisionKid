import { Stack } from 'expo-router';
import { AuthProvider } from '../context/AuthContext';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, LogBox, Pressable, Text, View } from 'react-native';
import { useEffect, useState } from 'react';
import { ENV } from '../config/env';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { prepareIllustrations } from '../components/ui/AppIllustration';
import { COLORS, FONTS } from '../constants/theme';

SplashScreen.preventAutoHideAsync().catch(() => {});

LogBox.ignoreLogs(['Cannot connect to Expo CLI']);

export default function RootLayout() {
  const [artReady, setArtReady] = useState(false);
  const [artError, setArtError] = useState(false);
  const [retry, setRetry] = useState(0);
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
    let active = true;
    setArtError(false);
    const timeout = setTimeout(() => { if (active) setArtError(true); }, 15000);
    prepareIllustrations().then(() => {
      if (active) { setArtReady(true); setArtError(false); }
    }).catch(() => { if (active) setArtError(true); }).finally(() => clearTimeout(timeout));
    return () => { active = false; clearTimeout(timeout); };
  }, [retry]);
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
  if (!artReady) return <View style={{ flex: 1, backgroundColor: COLORS.background, alignItems: 'center', justifyContent: 'center', gap: 18, padding: 24 }}>
    <Text style={{ fontFamily: FONTS.extraBold, fontSize: 28, color: COLORS.primaryDark }}>MathVisionKid</Text>
    {artError ? <>
      <Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary, textAlign: 'center' }}>Chưa tải đủ hình. Em thử lại để mở bài học nhé.</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Tải lại hình" onPress={() => setRetry(value => value + 1)} style={({ pressed }) => ({ minHeight: 48, padding: 16, borderRadius: 16, backgroundColor: COLORS.primary, opacity: pressed ? .8 : 1 })}>
        <Text style={{ color: 'white', fontFamily: FONTS.bold }}>Thử lại</Text>
      </Pressable>
    </> : <><ActivityIndicator color={COLORS.primary} /><Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary }}>Đang chuẩn bị bài học cho em…</Text></>}
  </View>;

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
