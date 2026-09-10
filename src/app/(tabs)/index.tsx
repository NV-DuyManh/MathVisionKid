import React, { useContext } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { AppCard } from '../../components/ui/AppCard';
import { AuthContext } from '../../context/AuthContext';
import * as ImagePicker from 'expo-image-picker';

export default function HomeScreen() {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const userName = auth?.user?.name || 'em';

  const handlePickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        quality: 1,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const uri = result.assets[0].uri;
        router.push({ pathname: '/preview', params: { uri } });
      }
    } catch {
      // User cancelled or permissions issue
    }
  };

  const navigateToCamera = () => {
    router.navigate('/camera' as any);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header with greeting and avatar */}
      <View style={styles.header}>
        <View style={styles.greetingContainer}>
          <Text style={styles.greeting}>Xin chào {userName}! 👋</Text>
          <Text style={styles.subtitle}>Hôm nay mình cùng kiểm tra bài toán nhé!</Text>
        </View>
        <TouchableOpacity
          style={styles.avatar}
          onPress={() => router.push('/(tabs)/profile')}
          accessibilityRole="button"
          accessibilityLabel="Trang cá nhân của em"
        >
          <Ionicons name="person" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {/* Primary Hero Action: CHỤP BÀI CỦA EM */}
      <TouchableOpacity
        activeOpacity={0.92}
        onPress={navigateToCamera}
        accessibilityRole="button"
        accessibilityLabel="Chụp bài của em, AI sẽ kiểm tra từng bước phép tính"
      >
        <View style={[styles.heroCard, SHADOWS.medium]}>
          <View style={styles.heroIconBadge}>
            <Ionicons name="camera" size={44} color="#FFFFFF" />
          </View>
          <Text style={styles.heroTitle}>CHỤP BÀI CỦA EM</Text>
          <Text style={styles.heroSubtitle}>
            Chụp phép tính đặt dọc, MathVision sẽ giúp em kiểm tra từng hàng và gợi ý cách sửa.
          </Text>
          <View style={styles.heroCtaPill}>
            <Text style={styles.heroCtaText}>Mở máy ảnh</Text>
            <Ionicons name="arrow-forward" size={18} color={COLORS.primaryDark} />
          </View>
        </View>
      </TouchableOpacity>

      {/* Secondary Action: Thư viện ảnh */}
      <TouchableOpacity
        style={styles.secondaryAction}
        onPress={handlePickImage}
        accessibilityRole="button"
        accessibilityLabel="Chọn ảnh bài tập từ thư viện máy"
      >
        <Ionicons name="images-outline" size={22} color={COLORS.primary} />
        <Text style={styles.secondaryActionText}>Chọn ảnh có sẵn từ thư viện</Text>
      </TouchableOpacity>

      {/* Guidance Section: Mẹo nhỏ chụp ảnh */}
      <View style={styles.guidanceSection}>
        <Text style={styles.guidanceTitle}>Mẹo nhỏ để kiểm tra chính xác</Text>
        <View style={styles.guidanceRow}>
          <AppCard style={styles.guidanceCard} variant="outlined">
            <View style={[styles.tipIconBadge, { backgroundColor: '#FEF3C7' }]}>
              <Ionicons name="sunny" size={24} color={COLORS.warning} />
            </View>
            <Text style={styles.guidanceHead}>Đủ ánh sáng</Text>
            <Text style={styles.guidanceSub}>Tránh để bóng tay che chữ số</Text>
          </AppCard>

          <View style={{ width: SIZES.medium }} />

          <AppCard style={styles.guidanceCard} variant="outlined">
            <View style={[styles.tipIconBadge, { backgroundColor: '#DCFCE7' }]}>
              <Ionicons name="scan" size={24} color={COLORS.success} />
            </View>
            <Text style={styles.guidanceHead}>Một phép tính</Text>
            <Text style={styles.guidanceSub}>Đưa trọn vẹn bài vào khung</Text>
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
    paddingTop: 56,
    paddingBottom: SIZES.xxlarge,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SIZES.xlarge,
  },
  greetingContainer: {
    flex: 1,
    paddingRight: SIZES.small,
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
    lineHeight: 20,
  },
  avatar: {
    width: SIZES.minTouchTarget,
    height: SIZES.minTouchTarget,
    borderRadius: SIZES.minTouchTarget / 2,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 1.5,
    borderColor: '#BFDBFE',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroCard: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.cardRadius,
    alignItems: 'center',
    paddingVertical: SIZES.xxlarge,
    paddingHorizontal: SIZES.large,
    marginBottom: SIZES.medium,
  },
  heroIconBadge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.22)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SIZES.medium,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.35)',
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 8,
    letterSpacing: 0.8,
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.92)',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: SIZES.large,
    paddingHorizontal: SIZES.small,
  },
  heroCtaPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: SIZES.large,
    paddingVertical: 10,
    borderRadius: SIZES.pillRadius,
  },
  heroCtaText: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginRight: 6,
  },
  secondaryAction: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: SIZES.minTouchTarget,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 1.5,
    borderColor: '#BFDBFE',
    borderRadius: SIZES.cardRadius,
    marginBottom: SIZES.xlarge,
  },
  secondaryActionText: {
    marginLeft: SIZES.small,
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.primary,
  },
  guidanceSection: {
    marginBottom: SIZES.large,
  },
  guidanceTitle: {
    fontSize: 17,
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
    paddingVertical: SIZES.large,
    paddingHorizontal: SIZES.small,
  },
  tipIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SIZES.small,
  },
  guidanceHead: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 4,
    textAlign: 'center',
  },
  guidanceSub: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 16,
  },
});
