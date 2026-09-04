import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';

export default function ReviewRequiredScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <AppHeader title="Kết quả" showBack />
      
      <View style={styles.content}>
        <View style={styles.spacer} />
        
        <StatusCard 
          status="warning" 
          title="MathVision cần xem kỹ hơn" 
          subtitle="Chữ viết trong bài này chưa đủ rõ để kết luận chắc chắn."
        />

        <View style={styles.spacer} />

        <AppButton 
          title="Chụp lại" 
          onPress={() => router.replace('/(tabs)/camera')} 
        />
        <View style={{ height: SIZES.medium }} />
        <AppButton 
          title="Để giáo viên xem" 
          variant="secondary"
          onPress={() => router.replace('/(tabs)')} 
        />
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
