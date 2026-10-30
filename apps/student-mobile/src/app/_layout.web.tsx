import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import Head from 'expo-router/head';
import { Text, View } from 'react-native';
import { useFonts } from 'expo-font';
import { AuthProvider } from '../context/AuthContext';
import { prepareIllustrations } from '../components/ui/AppIllustration';
import { WebAlerts } from '../components/ui/WebAlerts.web';
import { COLORS, FONTS } from '../constants/theme';
import { TaskProgress } from '../components/ui/TaskProgress';
import { observeLearningPerformance } from '../features/tutoring/webPerformance.web';

export default function StudentWebLayout() {
  useEffect(observeLearningPerformance, []);
  const [artReady, setArtReady] = useState(false);
  const [artError, setArtError] = useState(false);
  const [startupExpired, setStartupExpired] = useState(false);
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
    prepareIllustrations().then(() => { if (active) setArtReady(true); })
      .catch(() => { if (active) setArtError(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const timer = setTimeout(() => setStartupExpired(true), 12000);
    return () => clearTimeout(timer);
  }, []);
  return <View style={{ flex: 1, backgroundColor: COLORS.background }}>
    <Head><title>MathVisionKid — Cùng em học toán</title></Head>
    <WebAlerts />
    <View style={{ flex: 1, width: '100%', minWidth: 0 }}>
      {((!fontsLoaded && !fontError) || (!artReady && !artError)) && !startupExpired
        ? <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 18, padding: 24 }}>
          <Text style={{ fontFamily: fontsLoaded ? FONTS.extraBold : undefined, fontSize: 28, color: COLORS.primaryDark }}>MathVisionKid</Text>
          <View style={{ width: '100%', maxWidth: 360 }}><TaskProgress steps={['Tải chữ', 'Tải hình minh họa', 'Mở ứng dụng']} activeStep={fontsLoaded || fontError ? 1 : 0} timeoutSeconds={12} /></View>
        </View>
        : <AuthProvider><Stack screenOptions={{ headerShown: false }} /></AuthProvider>}
    </View>
  </View>;
}
