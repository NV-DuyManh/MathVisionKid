import React, { useState } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { TokenConfirmationCard } from '../../components/domain/TokenConfirmationCard';
import { MockSubmissionService } from '../../services/api/MockSubmissionService';

export default function TokenConfirmationScreen() {
  const router = useRouter();
  const { id, token } = useLocalSearchParams<{ id: string, token: string }>();
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
      <AppHeader title="Xác nhận" showBack />
      
      <View style={styles.content}>
        <View style={styles.spacer} />
        
        {loading ? (
          <ActivityIndicator size="large" color={COLORS.primary} />
        ) : (
          <TokenConfirmationCard 
            initialToken={token || '7'} 
            onConfirm={handleConfirm}
          />
        )}

        <View style={styles.spacer} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    padding: SIZES.medium,
  },
  spacer: {
    flex: 1,
  }
});
