import React, { useContext } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet } from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { useIsCompactStudentWeb } from '../components/ui/useIsCompactStudentWeb';
import { STUDENT_WEB } from '../constants/studentWebDesign';
import { PersonalPageHeader } from '../features/student-profile/PersonalWeb';
import { ProfileProgress } from '../features/student-profile/ProfileProgress';
import { useStudentProfile } from '../features/student-profile/useStudentProfile';

export default function ProgressPage() {
  const compactWeb = useIsCompactStudentWeb();
  const auth = useContext(AuthContext);
  if (!compactWeb) return <Redirect href="/(tabs)/profile" />;
  const owner = auth?.user?.id ?? auth?.user?.userId;
  if (auth?.isLoading) return <ActivityIndicator accessibilityLabel="Đang mở tiến độ" />;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || !owner) return <Redirect href="/login" />;
  return <CompactProgress key={owner} owner={owner} />;
}

function CompactProgress({ owner }: { owner: string }) {
  const router = useRouter();
  const { value, failed, retry } = useStudentProfile(owner);
  return <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
    <PersonalPageHeader title="Tiến độ học tập" backLabel="Về thành tích" onBack={() => router.replace('/(tabs)/achievements')} />
    <ProfileProgress value={value} failed={failed} retry={retry} wide={false} hideHeading />
  </ScrollView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: STUDENT_WEB.background },
  content: { padding: 18, paddingBottom: 38, gap: 14 },
});
