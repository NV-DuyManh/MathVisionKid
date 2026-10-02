import React, { useContext } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Redirect, Stack } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';
import { COLORS } from '../../constants/theme';

export default function RecognitionLayout() {
  const auth = useContext(AuthContext);
  if (auth?.isLoading) {
    return <View style={{ flex: 1, justifyContent: 'center' }}><ActivityIndicator color={COLORS.primary} /></View>;
  }
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
