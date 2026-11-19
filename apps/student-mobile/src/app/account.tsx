import React, { useContext } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Redirect } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { AccountScreen } from '../features/student-profile/AccountScreen';

export default function AccountPage() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  if (auth?.isLoading) return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}><ActivityIndicator accessibilityLabel="Đang mở hồ sơ" /></View>;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || !owner) return <Redirect href="/login" />;
  return <AccountScreen key={owner} owner={owner} />;
}
