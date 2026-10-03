import React, { useContext } from 'react';
import { Redirect, Stack } from 'expo-router';
import { View } from 'react-native';
import { AuthContext } from '../../context/AuthContext';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';

export default function LearningLayout() {
  const auth = useContext(AuthContext);
  if (auth?.isLoading) return <View style={{ flex: 1, justifyContent: 'center', padding: 24 }}>
    <RecognitionProgress title="Chuẩn bị bài học" description="Chờ một chút để bắt đầu nhé." />
  </View>;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
