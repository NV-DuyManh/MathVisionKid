import React, { useContext, useState } from 'react';
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
  return <AdmittedParentMode key={owner} owner={owner}
    onExit={() => router.canGoBack() ? router.back() : router.replace('/(tabs)/profile')}
    onChooseLesson={Platform.OS === 'web' ? () => router.replace('/(tabs)/lessons') : undefined} />;
}

function AdmittedParentMode({ owner, onExit, onChooseLesson }: React.ComponentProps<typeof ParentModePreview>) {
  const [admitted] = useState(() => Boolean(readParentModeSession(owner)));
  if (!admitted) return <Redirect href="/(tabs)/profile" />;
  return <ParentModePreview owner={owner} onExit={onExit} onChooseLesson={onChooseLesson} />;
}
