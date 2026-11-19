import React, { useContext } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Redirect, useLocalSearchParams } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { AccountScreen } from '../features/student-profile/AccountScreen';
import { IS_STUDENT_WEB } from '../constants/theme';

export default function AccountPage() {
  const auth = useContext(AuthContext);
  const { section } = useLocalSearchParams<{ section?: string }>();
  const owner = auth?.user?.id ?? auth?.user?.userId;
  if (auth?.isLoading) return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}><ActivityIndicator accessibilityLabel="Đang mở hồ sơ" /></View>;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || !owner) return <Redirect href="/login" />;
  return <AccountScreen key={owner} owner={owner} openPrivacy={section === 'privacy'} openLogout={IS_STUDENT_WEB && section === 'logout'} />;
}
