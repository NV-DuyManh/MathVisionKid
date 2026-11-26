import React, { useState, useEffect, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, Alert, ScrollView, useWindowDimensions, Platform } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { FONTS, COLORS, SIZES, SHADOWS, IS_STUDENT_WEB, WEB_DESIGN } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { RecoveryNotice } from '../components/ui/RecoveryNotice';
import { AppButton } from '../components/ui/AppButton';
import { Ionicons } from '@expo/vector-icons';
import * as ImageManipulator from 'expo-image-manipulator';
import { recognitionDraftStore, resolveFlowDomain, isHandwritingDomain } from '../features/recognition/state/recognitionDraftStore';
import { ensureFileUri, logStageDiagnostic } from '../features/recognition/image/imagePipeline';
import { imageDraftPersistence } from '../features/recognition/state/imageDraftPersistence';
import { DraftImagePicker } from '../features/recognition/components/DraftImagePicker';

export default function PreviewScreen() {
  const { width, height } = useWindowDimensions();
  const wide = width >= 1000;
  const router = useRouter();
  const params = useLocalSearchParams<{
    uri?: string;
    originalUri?: string;
    retrySubmissionId?: string;
  }>();

  const draft = recognitionDraftStore.getDraft();
  const hasDraft = !!draft;
  const effectiveMode = resolveFlowDomain(null, draft?.mode);
  const rawUri = draft?.uri || (Array.isArray(params.uri) ? params.uri[0] : params.uri);
  const initialUri = rawUri ? ensureFileUri(rawUri) : '';

  const [imageUri, setImageUri] = useState<string>(initialUri);
  const [imageError, setImageError] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [rotationFailed, setRotationFailed] = useState(false);
  const rotation = useRef(0), focused = useRef(true), rotationLocked = useRef(false);
  useFocusEffect(useCallback(() => {
    focused.current = true; rotationLocked.current = false; setRotating(false);
    return () => { focused.current = false; rotation.current++; };
  }, []));

  useEffect(() => {
    if (Platform.OS === 'web' && !hasDraft) return;
    if (isHandwritingDomain(effectiveMode) || effectiveMode !== 'ARITHMETIC') {
      if (__DEV__) {
        console.warn('[HANDWRITING_PREVIEW_GUARD_TRIGGERED] Non-arithmetic mode reached /preview. Redirecting to handwriting review.');
      }
      if (effectiveMode === 'OCR_PILOT') {
        router.replace('/recognition/line-crop' as any);
      } else {
        router.replace('/recognition/multiline-review' as any);
      }
      return;
    }

    if (initialUri) {
      logStageDiagnostic('PREVIEW_INPUT', {
        uri: initialUri,
        width: draft?.width,
        height: draft?.height,
        mimeType: draft?.mimeType,
        source: draft?.source,
        extra: `mode=${effectiveMode}`,
      });
    }
  }, [initialUri, draft?.width, draft?.height, draft?.mimeType, draft?.source, effectiveMode, hasDraft, router]);

  const handleContinue = () => {
    if (isHandwritingDomain(effectiveMode) || effectiveMode !== 'ARITHMETIC') {
      if (__DEV__) {
        console.warn('[HANDWRITING_PREVIEW_GUARD_TRIGGERED] Non-arithmetic mode in handleContinue. Blocking /processing.');
      }
      router.replace('/recognition/multiline-review' as any);
      return;
    }

    const activeUri = ensureFileUri(imageUri);
    recognitionDraftStore.updateDraft({ uri: activeUri, mode: 'ARITHMETIC', processingStarted: false, recoveredAfterReload: false });

    router.replace({
      pathname: '/processing' as any,
      params: {
        uri: activeUri,
        originalUri: draft?.rawUri || (Array.isArray(params.originalUri) ? params.originalUri[0] : params.originalUri),
        retrySubmissionId: draft?.retrySubmissionId || (Array.isArray(params.retrySubmissionId) ? params.retrySubmissionId[0] : params.retrySubmissionId),
      },
    });
  };

  const handleRotate = async () => {
    if (rotationLocked.current) return;
    rotationLocked.current = true; setRotating(true); setRotationFailed(false);
    const request = ++rotation.current, sourceId = draft?.imageSessionId;
    const identity = imageDraftPersistence.identity();
    const current = () => focused.current && request === rotation.current &&
      (Platform.OS !== 'web' || (sourceId === recognitionDraftStore.getDraft()?.imageSessionId && identity === imageDraftPersistence.identity()));
    try {
      const activeUri = ensureFileUri(imageUri);
      const manipResult = await ImageManipulator.manipulateAsync(
        activeUri,
        [{ rotate: 90 }],
        { compress: 0.95, format: ImageManipulator.SaveFormat.JPEG }
      );
      const rotatedUri = ensureFileUri(manipResult.uri);
      if (!current()) { imageDraftPersistence.releaseUrl(rotatedUri); return; }
      imageDraftPersistence.ownUrl(rotatedUri);
      setImageUri(rotatedUri);
      const cropEdit = recognitionDraftStore.getDraft()?.cropEdit;
      const selection = cropEdit?.selection ?? { x: 0, y: 0, w: 1, h: 1 };
      recognitionDraftStore.updateDraft({
        uri: rotatedUri,
        croppedImageUri: rotatedUri,
        arithmeticSubmissionId: undefined,
        processingStarted: false,
        recoveredAfterReload: false,
        width: manipResult.width,
        height: manipResult.height,
        ...(Platform.OS === 'web' && { cropEdit: {
          turns: ((cropEdit?.turns ?? 0) + 1) % 4,
          fine: cropEdit?.fine ?? 0,
          selection: { x: Math.max(0, 1 - selection.y - selection.h), y: selection.x, w: selection.h, h: selection.w },
        } }),
      });
      const updated = recognitionDraftStore.getDraft();
      if (updated) await imageDraftPersistence.confirm(updated, 'preview');
    } catch {
      if (current()) {
        if (IS_STUDENT_WEB) setRotationFailed(true);
        else Alert.alert('Lỗi', 'Không thể xoay ảnh. Vui lòng thử lại.');
      }
    } finally {
      if (current()) { rotationLocked.current = false; setRotating(false); }
    }
  };

  const handleCrop = () => {
    const activeUri = ensureFileUri(imageUri);
    router.push({
      pathname: '/crop' as any,
      params: {
        uri: activeUri,
        retrySubmissionId: draft?.retrySubmissionId || (Array.isArray(params.retrySubmissionId) ? params.retrySubmissionId[0] : params.retrySubmissionId),
      },
    });
  };

  if (Platform.OS === 'web' && (!draft?.privacyConfirmed || !imageUri || imageError)) return <View style={styles.container}>
    <AppHeader title="Xem lại bài đã chụp" showBack /><DraftImagePicker showReason mode="ARITHMETIC" />
  </View>;
  return (
    <View style={styles.container}>
      <AppHeader title="Xem lại bài đã chụp" showBack backFallback={Platform.OS === 'web' ? '/crop' : undefined} />

      <ScrollView contentContainerStyle={[styles.content, { minHeight: Math.max(0, height - 90) }, wide && styles.contentWide, IS_STUDENT_WEB && styles.webContent]}>
        {/* Preview image box with quality badge overlay */}
        <View style={[styles.imageContainer, SHADOWS.small, wide && styles.imageWide, IS_STUDENT_WEB && styles.webImage]}>
          <Image source={{ uri: imageUri }} style={styles.image} resizeMode="contain" accessibilityLabel="Ảnh bài toán em đã chọn" onError={() => setImageError(true)} />

          {!IS_STUDENT_WEB && <View style={styles.qualityOverlay}>
            <Text style={styles.checkingText}>Em kiểm tra ảnh có rõ chữ, đủ bài và đúng chiều trước khi gửi nhé.</Text>
          </View>}
        </View>

        <View style={[styles.controlColumn, wide && styles.controlColumnWide, IS_STUDENT_WEB && styles.webControls]}>
        <Text accessibilityRole="header" style={styles.reviewTitle}>{IS_STUDENT_WEB ? 'Ảnh đã rõ chưa?' : 'Sẵn sàng xem bài?'}</Text>
        <Text style={styles.reviewCopy}>{IS_STUDENT_WEB ? 'Xem lại chữ số, vùng bài và chiều ảnh trước khi gửi.' : 'Em nhìn lại chữ số và vùng bài đã chọn. Khi ảnh rõ, mình cùng kiểm tra nhé.'}</Text>
        {rotationFailed && <RecoveryNotice dialog title="Chưa xoay được ảnh"
          message="Ảnh của em vẫn còn. Em có thể thử xoay lại hoặc chỉnh vùng bài."
          actions={[
            { label: 'Thử xoay lại', onPress: () => void handleRotate(), disabled: rotating },
            { label: 'Chỉnh vùng bài', onPress: handleCrop, disabled: rotating },
          ]} />}
        {/* Tools row: Xoay & Chỉnh vùng bài */}
        <View style={styles.toolsRow}>
          <TouchableOpacity
            style={[styles.toolButton, IS_STUDENT_WEB && styles.webTool]}
            onPress={handleRotate}
            disabled={rotating}
            accessibilityState={{ disabled: rotating, busy: rotating }}
            accessibilityRole="button"
            accessibilityLabel="Xoay ảnh 90 độ"
          >
            <Ionicons name="refresh" size={20} color={COLORS.primary} />
            <Text style={styles.toolText}>Xoay ảnh</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.toolButton, IS_STUDENT_WEB && styles.webTool]}
            onPress={handleCrop}
            disabled={rotating}
            accessibilityState={{ disabled: rotating }}
            accessibilityRole="button"
            accessibilityLabel="Chỉnh lại vùng bài toán"
          >
            <Ionicons name="crop-outline" size={20} color={COLORS.primary} />
            <Text style={styles.toolText}>Chỉnh vùng bài</Text>
          </TouchableOpacity>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionSection}>
          <AppButton
            title="KIỂM TRA BÀI TOÁN"
            disabled={rotating}
            onPress={handleContinue}
            variant="primary"
          />
          <View style={{ height: SIZES.small }} />
          {Platform.OS === 'web' ? <DraftImagePicker title="Chọn ảnh khác" mode="ARITHMETIC" disabled={rotating} /> : <AppButton
            title="Chụp lại ảnh khác"
            variant="secondary"
            onPress={() => router.back()}
          />}
        </View>
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
    flexGrow: 1,
    padding: 22,
    maxWidth: 760,
    width: '100%',
    alignSelf: 'center',
  },
  contentWide: { maxWidth: 1140, flexDirection: 'row', alignItems: 'center', gap: 32 },
  webContent: { padding: 16 },
  webImage: { borderRadius: WEB_DESIGN.radii.notebook, backgroundColor: WEB_DESIGN.colors.ink },
  webControls: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: WEB_DESIGN.colors.paperLine, borderRadius: WEB_DESIGN.radii.notebook, padding: 16 },
  webTool: { borderRadius: WEB_DESIGN.radii.control, borderColor: COLORS.border, paddingHorizontal: 8 },
  controlColumn: { gap: 10 }, controlColumnWide: { width: 360 },
  reviewTitle: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 23, lineHeight: 31 },
  reviewCopy: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 14, lineHeight: 23, marginBottom: 12 },
  imageWide: { minHeight: 500, marginBottom: 0 },
  imageContainer: {
    flex: 1,
    minHeight: 280,
    backgroundColor: '#0F172A',
    borderRadius: 27,
    overflow: 'hidden',
    marginBottom: SIZES.medium,
    position: 'relative',
  },
  image: {
    flex: 1,
  },
  qualityOverlay: {
    position: 'absolute',
    bottom: 0,
    width: '100%',
    padding: SIZES.medium,
    backgroundColor: 'rgba(255, 255, 255, 0.96)',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  },
  checkingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
  },
  checkingText: {
    marginLeft: 8,
    color: COLORS.textSecondary,
    fontSize: 14,
    fontFamily: FONTS.semiBold,
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  toolsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: SIZES.large,
    gap: SIZES.medium,
  },
  toolButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    paddingHorizontal: SIZES.large,
    minHeight: SIZES.minTouchTarget,
    borderRadius: SIZES.buttonRadius,
    borderWidth: 1.5,
    borderColor: '#E0D3F6',
    flex: 1,
  },
  toolText: {
    marginLeft: 8,
    color: COLORS.primaryDark,
    fontSize: 14,
    fontFamily: FONTS.bold,
  },
  actionSection: {
    paddingBottom: SIZES.medium,
  },
});
