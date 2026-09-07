import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { AppCard } from '../../components/ui/AppCard';
import * as ImagePicker from 'expo-image-picker';

export default function HomeScreen() {
  const router = useRouter();

  const handlePickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: false,
      quality: 1,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      const uri = result.assets[0].uri;
      router.push({ pathname: '/preview', params: { uri } });
    }
  };

  const navigateToCamera = () => {
    router.navigate('/camera' as any);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <TouchableOpacity 
          onLongPress={() => router.push('/dev-demo')} 
          delayLongPress={1000}
        >
          <Text style={styles.greeting}>Xin chào Minh 👋</Text>
          <Text style={styles.subtitle}>Hôm nay mình kiểm tra một bài toán nhé!</Text>
        </TouchableOpacity>
        <View style={styles.avatar}>
          <Ionicons name="person" size={24} color={COLORS.primary} />
        </View>
      </View>

      <TouchableOpacity activeOpacity={0.9} onPress={navigateToCamera}>
        <AppCard style={styles.heroCard}>
          <View style={styles.heroIconContainer}>
            <Ionicons name="camera" size={48} color={COLORS.surface} />
          </View>
          <Text style={styles.heroTitle}>CHỤP BÀI CỦA EM</Text>
          <Text style={styles.heroSubtitle}>AI sẽ kiểm tra từng bước và giúp em tìm chỗ cần sửa</Text>
        </AppCard>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryAction} onPress={handlePickImage}>
        <Ionicons name="images" size={24} color={COLORS.primary} />
        <Text style={styles.secondaryActionText}>Chọn ảnh từ thư viện</Text>
      </TouchableOpacity>

      <View style={styles.guidanceSection}>
        <Text style={styles.guidanceTitle}>Mẹo nhỏ chụp ảnh</Text>
        <View style={styles.guidanceRow}>
          <AppCard style={styles.guidanceCard} variant="outlined">
            <Ionicons name="sunny" size={32} color={COLORS.warning} style={styles.guidanceIcon} />
            <Text style={styles.guidanceText}>Ảnh đủ sáng</Text>
          </AppCard>
          <View style={{ width: SIZES.medium }} />
          <AppCard style={styles.guidanceCard} variant="outlined">
            <Ionicons name="scan" size={32} color={COLORS.success} style={styles.guidanceIcon} />
            <Text style={styles.guidanceText}>Một bài trong ảnh</Text>
          </AppCard>
        </View>
      </View>


    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.medium,
    paddingTop: 60,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SIZES.xlarge,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#EEF2FF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroCard: {
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    paddingVertical: SIZES.xxlarge,
    marginBottom: SIZES.medium,
    ...SHADOWS.medium,
  },
  heroIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SIZES.medium,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.surface,
    marginBottom: 8,
    letterSpacing: 1,
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    paddingHorizontal: SIZES.large,
  },
  secondaryAction: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: SIZES.medium,
    backgroundColor: '#EEF2FF',
    borderRadius: SIZES.cardRadius,
    marginBottom: SIZES.xlarge,
  },
  secondaryActionText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  guidanceSection: {
    marginBottom: SIZES.xlarge,
  },
  guidanceTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: SIZES.medium,
  },
  guidanceRow: {
    flexDirection: 'row',
  },
  guidanceCard: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SIZES.large,
    backgroundColor: COLORS.surface,
  },
  guidanceIcon: {
    marginBottom: 8,
  },
  guidanceText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  demoSection: {
    marginTop: SIZES.xlarge,
    paddingTop: SIZES.large,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  demoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: SIZES.small,
  },
  demoPill: {
    backgroundColor: COLORS.border,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  demoPillText: {
    fontSize: 12,
    color: COLORS.textPrimary,
  }
});
