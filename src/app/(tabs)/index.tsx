import React, { useContext } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SHADOWS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import * as ImagePicker from 'expo-image-picker';
import { submissionDraftStore, resolveFlowDomain, logFlowDomain, FlowDomain } from '../../services/draft/submissionDraftStore';
import { normalizeImageDraft, logStageDiagnostic } from '../../services/image/imagePipeline';

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
        const asset = result.assets[0];
        logStageDiagnostic('ACQUIRE_GALLERY', {
          uri: asset.uri,
          width: asset.width,
          height: asset.height,
          mimeType: asset.mimeType,
          source: 'GALLERY',
        });
        const draft = await normalizeImageDraft(asset.uri, asset.width, asset.height, 'GALLERY');
        draft.mode = resolveFlowDomain(null, null); // Defaults to HANDWRITING_TEXT
        logFlowDomain('ACQUIRE', draft.mode);
        submissionDraftStore.setDraft(draft);
        router.push({ pathname: '/privacy' as any, params: { uri: draft.uri } });
      }
    } catch {
      // User cancelled or permissions issue
    }
  };

  const navigateToCamera = (mode: FlowDomain = 'HANDWRITING_TEXT') => {
    submissionDraftStore.clearDraft();
    logFlowDomain('ACQUIRE', mode);
    router.push({ pathname: '/camera' as any, params: { mode } });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      {/* Header: Greeting & Profile Avatar */}
      <View style={styles.header}>
        <View style={styles.greetingContainer}>
          <Text style={styles.greeting}>Xin chào, {userName}! 👋</Text>
          <Text style={styles.subtitle}>Cùng MathVision nhận diện và rèn luyện chữ viết tay nhé</Text>
        </View>
        <TouchableOpacity
          style={[styles.avatar, SHADOWS.small]}
          onPress={() => router.push('/(tabs)/profile')}
          accessibilityRole="button"
          accessibilityLabel="Trang cá nhân của em"
        >
          <Ionicons name="person" size={20} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {/* Main Unified Handwriting Entry Point */}
      <View style={[styles.mainHeroCard, SHADOWS.medium]}>
        <View style={styles.heroHeaderRow}>
          <View style={styles.heroIconBadge}>
            <Ionicons name="create" size={28} color="#FFFFFF" />
          </View>
          <View style={styles.heroTag}>
            <Text style={styles.heroTagText}>Chữ viết tay tiếng Việt</Text>
          </View>
        </View>

        <Text style={styles.heroTitle}>Đọc chữ viết tay</Text>
        <Text style={styles.heroDescription}>
          Chụp hoặc chọn ảnh bài viết để hệ thống tự động tách từng dòng chữ, nhận diện nội dung và hỗ trợ chỉnh sửa trực quan.
        </Text>

        {/* 2 Primary Direct CTAs */}
        <View style={styles.heroActionRow}>
          <TouchableOpacity
            style={[styles.ctaPrimaryBtn, SHADOWS.small]}
            onPress={() => navigateToCamera('HANDWRITING_TEXT')}
            activeOpacity={0.88}
            accessibilityRole="button"
            accessibilityLabel="Chụp ảnh mới"
          >
            <Ionicons name="camera" size={19} color={COLORS.primaryDark} />
            <Text style={styles.ctaPrimaryBtnText}>Chụp ảnh mới</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.ctaSecondaryBtn}
            onPress={handlePickImage}
            activeOpacity={0.88}
            accessibilityRole="button"
            accessibilityLabel="Chọn từ thư viện"
          >
            <Ionicons name="images-outline" size={19} color="#FFFFFF" />
            <Text style={styles.ctaSecondaryBtnText}>Chọn từ thư viện</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Secondary Feature: Arithmetic */}
      <View style={styles.sectionContainer}>
        <Text style={styles.sectionHeading}>Tính năng bổ trợ</Text>

        <TouchableOpacity
          style={[styles.secondaryFeatureCard, SHADOWS.small]}
          onPress={() => navigateToCamera('ARITHMETIC')}
          activeOpacity={0.88}
          accessibilityRole="button"
          accessibilityLabel="Đọc phép tính đặt dọc"
        >
          <View style={styles.featureIconBadge}>
            <Ionicons name="calculator-outline" size={22} color="#0284C7" />
          </View>
          <View style={styles.featureContent}>
            <Text style={styles.featureTitle}>Đọc phép tính đặt dọc</Text>
            <Text style={styles.featureSubtitle}>
              Nhận diện bài toán cộng, trừ, nhân, chia và hỗ trợ kiểm tra từng bước.
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
        </TouchableOpacity>
      </View>

      {/* Sleek Minimalist Photo Tips Card */}
      <View style={[styles.tipsCard, SHADOWS.small]}>
        <View style={styles.tipsHeader}>
          <View style={styles.tipsIconPill}>
            <Ionicons name="bulb-outline" size={16} color="#D97706" />
          </View>
          <Text style={styles.tipsHeading}>Mẹo chụp ảnh rõ nét</Text>
        </View>

        <View style={styles.tipsList}>
          <View style={styles.tipItem}>
            <Ionicons name="sunny-outline" size={16} color="#059669" style={styles.tipItemIcon} />
            <Text style={styles.tipItemText}>
              <Text style={styles.tipItemBold}>Đủ ánh sáng: </Text>
              Chụp ở nơi sáng đều, tránh để bóng tay che khuất các nét chữ.
            </Text>
          </View>

          <View style={styles.tipItem}>
            <Ionicons name="phone-portrait-outline" size={16} color="#2563EB" style={styles.tipItemIcon} />
            <Text style={styles.tipItemText}>
              <Text style={styles.tipItemBold}>Chụp thẳng góc: </Text>
              Giữ điện thoại song song với mặt trang giấy, tránh chụp quá nghiêng.
            </Text>
          </View>

          <View style={styles.tipItem}>
            <Ionicons name="scan-outline" size={16} color="#7C3AED" style={styles.tipItemIcon} />
            <Text style={styles.tipItemText}>
              <Text style={styles.tipItemBold}>Căn trọn khung hình: </Text>
              Để trọn vẹn các dòng chữ vào giữa khung, không bị cắt mép đầu hoặc đuôi dòng.
            </Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 52,
    paddingBottom: 40,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  greetingContainer: {
    flex: 1,
    paddingRight: 12,
  },
  greeting: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    justifyContent: 'center',
    alignItems: 'center',
  },

  /* Main Hero Card */
  mainHeroCard: {
    backgroundColor: '#1E40AF',
    borderRadius: 20,
    padding: 22,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#1D4ED8',
  },
  heroHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  heroIconBadge: {
    width: 52,
    height: 52,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroTag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
  },
  heroTagText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#DBEAFE',
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.3,
    marginBottom: 8,
  },
  heroDescription: {
    fontSize: 13,
    color: '#BFDBFE',
    lineHeight: 20,
    marginBottom: 20,
  },
  heroActionRow: {
    flexDirection: 'row',
    gap: 12,
  },
  ctaPrimaryBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 13,
    borderRadius: 12,
    gap: 8,
  },
  ctaPrimaryBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E40AF',
  },
  ctaSecondaryBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.14)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.28)',
    paddingVertical: 13,
    borderRadius: 12,
    gap: 8,
  },
  ctaSecondaryBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },

  /* Section Container */
  sectionContainer: {
    marginBottom: 24,
  },
  sectionHeading: {
    fontSize: 14,
    fontWeight: '700',
    color: '#334155',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  secondaryFeatureCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 14,
  },
  featureIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#F0F9FF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 3,
  },
  featureSubtitle: {
    fontSize: 12,
    color: '#64748B',
    lineHeight: 17,
  },

  /* Sleek Tips Card */
  tipsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  tipsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  tipsIconPill: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#FEF3C7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  tipsHeading: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  tipsList: {
    gap: 10,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  tipItemIcon: {
    marginTop: 2,
  },
  tipItemText: {
    flex: 1,
    fontSize: 12,
    color: '#475569',
    lineHeight: 18,
  },
  tipItemBold: {
    fontWeight: '700',
    color: '#1E293B',
  },
});
