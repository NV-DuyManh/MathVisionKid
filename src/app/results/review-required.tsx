import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';

export default function ReviewRequiredScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <AppHeader title="Chờ thầy cô xem lại" showBack />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.spacerTop} />

        <StatusCard
          status="warning"
          title="MathVision cần thầy cô xem giúp"
          subtitle="Chữ viết trong bài này có nét hơi mờ hoặc đặc biệt, bài của em đã được chuyển cho thầy cô xem thêm."
        />

        <View style={styles.spacer} />

        <View style={styles.actions}>
          <AppButton
            title="Chụp lại thật rõ nét"
            variant="primary"
            onPress={() => router.replace('/camera' as any)}
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Về trang chủ"
            variant="secondary"
            onPress={() => router.replace('/(tabs)')}
          />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.large,
    flexGrow: 1,
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },
  spacerTop: {
    height: SIZES.large,
  },
  spacer: {
    flex: 1,
    minHeight: SIZES.xlarge,
  },
  actions: {
    paddingBottom: SIZES.medium,
  },
});
