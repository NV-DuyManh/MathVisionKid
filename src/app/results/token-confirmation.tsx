import React, { useState } from 'react';
import { View, StyleSheet, ActivityIndicator, ScrollView, Text } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { TokenConfirmationCard } from '../../components/domain/TokenConfirmationCard';
import { MockSubmissionService } from '../../services/api/MockSubmissionService';

export default function TokenConfirmationScreen() {
  const router = useRouter();
  const { id, token } = useLocalSearchParams<{ id: string; token: string }>();
  const [loading, setLoading] = useState(false);

  const handleConfirm = async (confirmedToken: string) => {
    try {
      setLoading(true);
      const result = await MockSubmissionService.confirmToken(id as string, confirmedToken);

      if (result.validation?.decision === 'VALID') {
        router.replace({ pathname: '/results/correct', params: { data: JSON.stringify(result) } });
      } else {
        router.replace({ pathname: '/results/error-hint', params: { data: JSON.stringify(result) } });
      }
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <AppHeader title="Xác nhận chữ số" showBack />

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.spacerTop} />

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primary} />
            <Text style={styles.loadingText}>Đang cập nhật kết quả bài làm...</Text>
          </View>
        ) : (
          <TokenConfirmationCard
            initialToken={token || '7'}
            onConfirm={handleConfirm}
          />
        )}

        <View style={styles.spacer} />
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
    justifyContent: 'center',
  },
  spacerTop: {
    height: SIZES.medium,
  },
  spacer: {
    flex: 1,
    minHeight: SIZES.large,
  },
  loadingContainer: {
    alignItems: 'center',
    padding: SIZES.xxlarge,
  },
  loadingText: {
    marginTop: SIZES.medium,
    color: COLORS.textSecondary,
    fontSize: 15,
    fontWeight: '600',
  },
});
