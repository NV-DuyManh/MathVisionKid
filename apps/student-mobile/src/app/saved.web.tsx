import React, { useContext } from 'react';
import { ActivityIndicator } from 'react-native';
import { Redirect, useLocalSearchParams } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { ProfileContent } from './(tabs)/profile';

export default function SavedPage() {
  const auth = useContext(AuthContext);
  const { tab } = useLocalSearchParams<{ tab?: string }>();
  const owner = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  if (auth?.isLoading) return <ActivityIndicator accessibilityLabel="Đang mở sổ học tập" />;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || !owner) return <Redirect href="/login" />;
  const initialTab = tab === 'work' || tab === 'notes' ? tab : 'saved';
  return <ProfileContent key={owner + ':' + initialTab} owner={owner} savedOnly initialTab={initialTab} />;
}
