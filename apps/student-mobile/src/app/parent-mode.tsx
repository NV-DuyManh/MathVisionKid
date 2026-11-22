import React, { useContext } from 'react';
import { ActivityIndicator, Platform, View } from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { ParentModePreview } from '../features/student-profile/ParentModePreview';
import { readParentModeSession } from '../features/student-profile/parentModeHandoff';

export default function ParentModePage() {
  const auth = useContext(AuthContext);
  const router = useRouter();
  const owner = auth?.user?.id ?? auth?.user?.userId;
  if (auth?.isLoading) return <View style={{ flex: 1, justifyContent: 'center' }}><ActivityIndicator accessibilityLabel="Đang mở Góc phụ huynh" /></View>;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || auth.user.active !== true || !owner) return <Redirect href="/login" />;
  if (Platform.OS === 'web' && !readParentModeSession(owner)) return <Redirect href="/(tabs)/profile" />;
  return <ParentModePreview key={owner} owner={owner} onExit={() => router.canGoBack() ? router.back() : router.replace('/(tabs)/profile')} />;
}
