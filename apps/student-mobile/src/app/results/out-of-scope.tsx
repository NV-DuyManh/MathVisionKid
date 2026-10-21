import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { SIZES } from '../../constants/theme';
import { StudentResultShell } from '../../components/ui/StudentResultShell';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';

export default function OutOfScopeScreen() {
  const router = useRouter();

  return (
    <StudentResultShell title="Chưa hỗ trợ dạng bài">

        <StatusCard
          status="info"
          title="Dạng bài này MathVision đang học thêm"
          subtitle="Hiện tại MathVision hỗ trợ tốt nhất các phép tính cộng, trừ số tự nhiên đặt tính dọc (lớp 1 - lớp 5)."
        />

        <View style={styles.actions}>
          <AppButton
            title="Chụp phép tính đặt dọc khác"
            variant="primary"
            onPress={() => router.replace({ pathname: '/camera' as any, params: { mode: 'ARITHMETIC' } })}
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Về trang chủ"
            variant="secondary"
            onPress={() => router.replace('/(tabs)')}
          />
        </View>
      </StudentResultShell>
  );
}

const styles = StyleSheet.create({
  actions: {
    paddingBottom: SIZES.medium,
  },
});
