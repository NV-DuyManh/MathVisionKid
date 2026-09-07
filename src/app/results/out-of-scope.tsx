import { View, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';

export default function OutOfScopeScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <AppHeader title="Kết quả" showBack />
      
      <View style={styles.content}>
        <View style={styles.spacer} />
        
        <StatusCard 
          status="info" 
          title="Bài này MathVision chưa hỗ trợ" 
          subtitle="Phiên bản hiện tại đang hỗ trợ phép cộng và phép trừ số tự nhiên đặt tính dọc."
        />

        <View style={styles.spacer} />

        <AppButton 
          title="Chụp bài khác" 
          onPress={() => router.replace('/camera' as any)} 
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
