import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import Head from 'expo-router/head';
import { View } from 'react-native';
import { useFonts } from 'expo-font';
import { AuthProvider } from '../context/AuthContext';
import { WebAlerts } from '../components/ui/WebAlerts.web';
import { StudentWebWorkspace } from '../components/ui/StudentWebWorkspace.web';
import { COLORS } from '../constants/theme';
import { observeLearningPerformance } from '../features/tutoring/webPerformance.web';
import { StudentUsageTracker } from '../features/student-profile/studentUsage';
import { StudentDailyLimit } from '../features/student-profile/StudentDailyLimit';

export default function StudentWebLayout() {
  useEffect(observeLearningPerformance, []);
  useEffect(() => { if (typeof document !== 'undefined') document.documentElement.lang = 'vi'; }, []);
  useFonts({
    NunitoRegular: require('../../assets/fonts/Nunito-Regular.ttf'),
    NunitoMedium: require('../../assets/fonts/Nunito-Medium.ttf'),
    NunitoSemiBold: require('../../assets/fonts/Nunito-SemiBold.ttf'),
    NunitoBold: require('../../assets/fonts/Nunito-Bold.ttf'),
    NunitoExtraBold: require('../../assets/fonts/Nunito-ExtraBold.ttf'),
    NunitoBlack: require('../../assets/fonts/Nunito-Black.ttf'),
  });
  return <View style={{ flex: 1, backgroundColor: COLORS.background }}>
    <Head><title>MathVisionKid — Cùng em học toán</title></Head>
    <style>{`@media (min-width: 1100px) and (hover: hover) and (pointer: fine) { :root { zoom: 1.07; } }`}</style>
    <WebAlerts />
    <View style={{ flex: 1, width: '100%', minWidth: 0 }}>
      <AuthProvider>
        <StudentUsageTracker />
        <StudentDailyLimit><StudentWebWorkspace><Stack screenOptions={{ headerShown: false }} /></StudentWebWorkspace></StudentDailyLimit>
      </AuthProvider>
    </View>
  </View>;
}
