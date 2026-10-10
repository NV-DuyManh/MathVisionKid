import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import Head from 'expo-router/head';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import { useFonts } from 'expo-font';
import { AuthProvider } from '../context/AuthContext';
import { prepareIllustrations } from '../components/ui/AppIllustration';
import { WebAlerts } from '../components/ui/WebAlerts.web';
import { COLORS, FONTS } from '../constants/theme';

export default function StudentWebLayout() {
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
    let active = true;
    setArtError(false);
    prepareIllustrations().then(() => { if (active) setArtReady(true); })
      .catch(() => { if (active) setArtError(true); });
    return () => { active = false; };
  }, [retry]);
  return <View style={{ flex: 1, backgroundColor: COLORS.background }}>
    <Head><title>MathVisionKid — Cùng em học toán</title></Head>
    <WebAlerts />
    <View style={{ flex: 1, width: '100%', maxWidth: 860, alignSelf: 'center' }}>
      {(!fontsLoaded && !fontError) || !artReady
        ? <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 18, padding: 24 }}>
          <Text style={{ fontFamily: fontsLoaded ? FONTS.extraBold : undefined, fontSize: 28, color: COLORS.primaryDark }}>MathVisionKid</Text>
          {artError ? <>
            <Text style={{ textAlign: 'center', color: COLORS.textSecondary }}>Chưa tải đủ hình. Em thử lại để mở bài học nhé.</Text>
            <Pressable accessibilityRole="button" accessibilityLabel="Tải lại hình" onPress={() => setRetry(value => value + 1)}
              style={{ minHeight: 48, padding: 16, borderRadius: 16, backgroundColor: COLORS.primary }}>
              <Text style={{ color: 'white' }}>Thử lại</Text>
            </Pressable>
          </> : <><ActivityIndicator color={COLORS.primary} /><Text>Đang chuẩn bị bài học cho em…</Text></>}
        </View>
        : <AuthProvider><Stack screenOptions={{ headerShown: false }} /></AuthProvider>}
    </View>
  </View>;
}
