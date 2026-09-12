import React, { useContext } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { AppCard } from '../../components/ui/AppCard';
import { AuthContext } from '../../context/AuthContext';
import * as ImagePicker from 'expo-image-picker';
import { submissionDraftStore } from '../../services/draft/submissionDraftStore';
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
        draft.mode = 'ARITHMETIC';
        submissionDraftStore.setDraft(draft);
        router.push({ pathname: '/privacy' as any, params: { uri: draft.uri } });
      }
    } catch {
      // User cancelled or permissions issue
    }
  };

  const navigateToCamera = () => {
    router.navigate('/camera' as any);
  };

  const handleStartOcrPilot = () => {
    Alert.alert(
      'Thử nhận diện 1 dòng chữ (Pilot 1)',
      'Em muốn chụp ảnh mới hay chọn ảnh có sẵn từ thư viện?',
      [
        {
          text: 'Chụp ảnh mới',
          onPress: () => {
            submissionDraftStore.clearDraft();
            router.push({ pathname: '/camera' as any, params: { mode: 'OCR_PILOT' } });
          },
        },
        {
          text: 'Chọn từ thư viện',
          onPress: async () => {
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
                  extra: 'ocr-pilot mode',
                });
                const draft = await normalizeImageDraft(asset.uri, asset.width, asset.height, 'GALLERY');
                draft.mode = 'OCR_PILOT';
                submissionDraftStore.setDraft(draft);
                router.push({ pathname: '/privacy' as any, params: { uri: draft.uri } });
              }
            } catch {
              // cancelled
            }
          },
        },
        { text: 'Hủy', style: 'cancel' },
      ]
    );
  };

  const handleStartOcrPilotMultiline = () => {
    Alert.alert(
      'Thử nhận diện nhiều dòng chữ (Pilot 2)',
      'Em muốn chụp ảnh mới hay chọn ảnh có sẵn từ thư viện?',
      [
        {
          text: 'Chụp ảnh mới',
          onPress: () => {
            submissionDraftStore.clearDraft();
            router.push({ pathname: '/camera' as any, params: { mode: 'OCR_PILOT_MULTILINE' } });
          },
        },
        {
          text: 'Chọn từ thư viện',
          onPress: async () => {
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
                  extra: 'ocr-pilot-multiline mode',
                });
                const draft = await normalizeImageDraft(asset.uri, asset.width, asset.height, 'GALLERY');
                draft.mode = 'OCR_PILOT_MULTILINE';
                submissionDraftStore.setDraft(draft);
                router.push({ pathname: '/privacy' as any, params: { uri: draft.uri } });
              }
            } catch {
              // cancelled
            }
          },
        },
        { text: 'Hủy', style: 'cancel' },
      ]
    );
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

      {/* OCR Pilot 1 Action: THỬ NHẬN DIỆN 1 DÒNG */}
      <TouchableOpacity
        style={[styles.ocrPilotAction, SHADOWS.small]}
        onPress={handleStartOcrPilot}
        activeOpacity={0.88}
        accessibilityRole="button"
        accessibilityLabel="Thử nhận diện 1 dòng chữ viết tay tiếng Việt với mô hình CRNN"
      >
        <View style={styles.ocrPilotIconBadge}>
          <Ionicons name="document-text" size={24} color="#FFFFFF" />
        </View>
        <View style={styles.ocrPilotContent}>
          <View style={styles.ocrPilotHeaderRow}>
            <Text style={styles.ocrPilotTitle}>THỬ NHẬN DIỆN 1 DÒNG</Text>
            <View style={styles.ocrPilotTag}><Text style={styles.ocrPilotTagText}>PILOT 1</Text></View>
          </View>
          <Text style={styles.ocrPilotSubtitle}>
            Chụp hoặc chọn 1 dòng chữ tiếng Việt để AI đọc & gửi phản hồi
          </Text>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#047857" />
      </TouchableOpacity>

      {/* OCR Pilot 2 Action: THỬ NHẬN DIỆN NHIỀU DÒNG */}
      <TouchableOpacity
        style={[styles.ocrPilotAction, styles.ocrPilot2Action, SHADOWS.small]}
        onPress={handleStartOcrPilotMultiline}
        activeOpacity={0.88}
        accessibilityRole="button"
        accessibilityLabel="Thử nhận diện nhiều dòng chữ viết tay với phân đoạn dòng"
      >
        <View style={[styles.ocrPilotIconBadge, { backgroundColor: '#2563EB' }]}>
          <Ionicons name="list" size={24} color="#FFFFFF" />
        </View>
        <View style={styles.ocrPilotContent}>
          <View style={styles.ocrPilotHeaderRow}>
            <Text style={[styles.ocrPilotTitle, { color: '#1E40AF' }]}>THỬ NHẬN DIỆN NHIỀU DÒNG</Text>
            <View style={[styles.ocrPilotTag, { backgroundColor: '#2563EB' }]}><Text style={styles.ocrPilotTagText}>PILOT 2</Text></View>
          </View>
          <Text style={[styles.ocrPilotSubtitle, { color: '#1E40AF' }]}>
            Chụp đoạn văn nhiều dòng, tự động tách & chỉnh sửa khung từng dòng
          </Text>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#2563EB" />
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
  ocrPilotAction: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderWidth: 1.5,
    borderColor: '#86EFAC',
    borderRadius: SIZES.cardRadius,
    padding: SIZES.medium,
    marginBottom: SIZES.medium,
  },
  ocrPilot2Action: {
    backgroundColor: '#EFF6FF',
    borderColor: '#93C5FD',
    marginBottom: SIZES.xlarge,
  },
  ocrPilotIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#10B981',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SIZES.small,
  },
  ocrPilotContent: {
    flex: 1,
  },
  ocrPilotHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 2,
  },
  ocrPilotTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#065F46',
    marginRight: 6,
  },
  ocrPilotTag: {
    backgroundColor: '#047857',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  ocrPilotTagText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  ocrPilotSubtitle: {
    fontSize: 12,
    color: '#047857',
    lineHeight: 16,
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
