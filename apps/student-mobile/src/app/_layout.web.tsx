import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import Head from 'expo-router/head';
import { View } from 'react-native';
import { useFonts } from 'expo-font';
import { AuthProvider } from '../context/AuthContext';
import { WebAlerts } from '../components/ui/WebAlerts.web';
import { COLORS } from '../constants/theme';
import { observeLearningPerformance } from '../features/tutoring/webPerformance.web';

export default function StudentWebLayout() {
  useEffect(observeLearningPerformance, []);
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
    <WebAlerts />
    <View style={{ flex: 1, width: '100%', minWidth: 0 }}>
      <AuthProvider><Stack screenOptions={{ headerShown: false }} /></AuthProvider>
    </View>
  </View>;
}
