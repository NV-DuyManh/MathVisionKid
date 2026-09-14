/* eslint-disable react-hooks/immutability, react-hooks/set-state-in-effect, react-hooks/exhaustive-deps, @typescript-eslint/no-unused-vars */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Image, Alert, ActivityIndicator, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImageManipulator from 'expo-image-manipulator';
import { COLORS, SIZES } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { Ionicons } from '@expo/vector-icons';
import { submissionDraftStore, resolveFlowDomain } from '../services/draft/submissionDraftStore';
import { ensureFileUri, logStageDiagnostic } from '../services/image/imagePipeline';
import { Gesture, GestureDetector, GestureHandlerRootView } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedStyle, runOnJS } from 'react-native-reanimated';
import {
  calculateDrag,
  calculateResizeTL,
  calculateResizeTR,
  calculateResizeBL,
  calculateResizeBR,
  displayRectToSourceRect
} from '../utils/cropGeometry';

const MIN_CROP_SIZE = 60;
const HIT_SLOP = { top: 24, bottom: 24, left: 24, right: 24 };


export default function CropScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ retrySubmissionId?: string }>();
  const draft = submissionDraftStore.getDraft();
  const activeUri = draft?.uri ? ensureFileUri(draft.uri) : '';
  const retrySubmissionId = draft?.retrySubmissionId || (Array.isArray(params.retrySubmissionId) ? params.retrySubmissionId[0] : params.retrySubmissionId);

  const [imageLayout, setImageLayout] = useState({ width: 0, height: 0, x: 0, y: 0 });
  const [actualSize, setActualSize] = useState({ w: draft?.width || 0, h: draft?.height || 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [imageLoadError, setImageLoadError] = useState(false);
  const [boundsReady, setBoundsReady] = useState(false);

  // Shared values for UI-thread gesture animations
  const boxX = useSharedValue(0);
  const boxY = useSharedValue(0);
  const boxW = useSharedValue(0);
  const boxH = useSharedValue(0);
  
  const startX = useSharedValue(0);
  const startY = useSharedValue(0);
  const startW = useSharedValue(0);
  const startH = useSharedValue(0);
  
  // Bounds
  const bMinX = useSharedValue(0);
  const bMinY = useSharedValue(0);
  const bMaxX = useSharedValue(0);
  const bMaxY = useSharedValue(0);
  const imgScale = useSharedValue(1);

  useEffect(() => {
    if (activeUri) {
      logStageDiagnostic('CROP_INPUT', {
        uri: activeUri,
        width: draft?.width,
        height: draft?.height,
        mimeType: draft?.mimeType,
        source: draft?.source,
      });

      // Async resolve actual dimensions if missing
      if (!draft?.width || !draft?.height) {
        ImageManipulator.manipulateAsync(activeUri, [], {})
          .then(res => {
            if (res.width && res.height) setActualSize({ w: res.width, h: res.height });
          })
          .catch(() => {
            Image.getSize(activeUri, (w, h) => setActualSize({ w, h }), () => {});
          });
      }
    }
  }, [activeUri]);

  // Recalculate physical display bounds whenever layout or actual size changes
  useEffect(() => {
    if (imageLayout.width > 0 && imageLayout.height > 0 && actualSize.w > 0 && actualSize.h > 0) {
      const containerRatio = imageLayout.width / imageLayout.height;
      const imageRatio = actualSize.w / actualSize.h;
      
      let renderedWidth = imageLayout.width;
      let renderedHeight = imageLayout.height;
      let offsetX = 0;
      let offsetY = 0;

      if (imageRatio > containerRatio) {
        renderedHeight = imageLayout.width / imageRatio;
        offsetY = (imageLayout.height - renderedHeight) / 2;
      } else {
        renderedWidth = imageLayout.height * imageRatio;
        offsetX = (imageLayout.width - renderedWidth) / 2;
      }

      bMinX.value = offsetX;
      bMinY.value = offsetY;
      bMaxX.value = offsetX + renderedWidth;
      bMaxY.value = offsetY + renderedHeight;
      imgScale.value = actualSize.w / renderedWidth;

      // Initialize box centered and slightly inset (80%)
      const initialW = renderedWidth * 0.8;
      const initialH = renderedHeight * 0.8;
      boxW.value = initialW;
      boxH.value = initialH;
      boxX.value = offsetX + (renderedWidth - initialW) / 2;
      boxY.value = offsetY + (renderedHeight - initialH) / 2;

      setBoundsReady(true);
    }
  }, [imageLayout.width, imageLayout.height, actualSize.w, actualSize.h]);

  const animatedBoxStyle = useAnimatedStyle(() => {
    return {
      left: boxX.value,
      top: boxY.value,
      width: boxW.value,
      height: boxH.value,
    };
  });

  // --- Gestures ---
  const dragGesture = Gesture.Pan()
    .activeOffsetX([-2, 2])
    .activeOffsetY([-2, 2])
    .onStart(() => {
      startX.value = boxX.value;
      startY.value = boxY.value;
      startW.value = boxW.value;
      startH.value = boxH.value;
    })
    .onUpdate((e) => {
      const box = { x: startX.value, y: startY.value, w: startW.value, h: startH.value };
      const bounds = { minX: bMinX.value, minY: bMinY.value, maxX: bMaxX.value, maxY: bMaxY.value };
      const res = calculateDrag(e.translationX, e.translationY, box, bounds);
      boxX.value = res.x;
      boxY.value = res.y;
    });

  const resizeTL = Gesture.Pan()
    .activeOffsetX([-2, 2])
    .activeOffsetY([-2, 2])
    .onStart(() => {
      startX.value = boxX.value;
      startY.value = boxY.value;
      startW.value = boxW.value;
      startH.value = boxH.value;
    })
    .onUpdate((e) => {
      const box = { x: startX.value, y: startY.value, w: startW.value, h: startH.value };
      const bounds = { minX: bMinX.value, minY: bMinY.value, maxX: bMaxX.value, maxY: bMaxY.value };
      const res = calculateResizeTL(e.translationX, e.translationY, box, bounds);
      boxX.value = res.x; boxY.value = res.y; boxW.value = res.w; boxH.value = res.h;
    });

  const resizeTR = Gesture.Pan()
    .activeOffsetX([-2, 2])
    .activeOffsetY([-2, 2])
    .onStart(() => {
      startX.value = boxX.value;
      startY.value = boxY.value;
      startW.value = boxW.value;
      startH.value = boxH.value;
    })
    .onUpdate((e) => {
      const box = { x: startX.value, y: startY.value, w: startW.value, h: startH.value };
      const bounds = { minX: bMinX.value, minY: bMinY.value, maxX: bMaxX.value, maxY: bMaxY.value };
      const res = calculateResizeTR(e.translationX, e.translationY, box, bounds);
      boxX.value = res.x; boxY.value = res.y; boxW.value = res.w; boxH.value = res.h;
    });

  const resizeBL = Gesture.Pan()
    .activeOffsetX([-2, 2])
    .activeOffsetY([-2, 2])
    .onStart(() => {
      startX.value = boxX.value;
      startY.value = boxY.value;
      startW.value = boxW.value;
      startH.value = boxH.value;
    })
    .onUpdate((e) => {
      const box = { x: startX.value, y: startY.value, w: startW.value, h: startH.value };
      const bounds = { minX: bMinX.value, minY: bMinY.value, maxX: bMaxX.value, maxY: bMaxY.value };
      const res = calculateResizeBL(e.translationX, e.translationY, box, bounds);
      boxX.value = res.x; boxY.value = res.y; boxW.value = res.w; boxH.value = res.h;
    });

  const resizeBR = Gesture.Pan()
    .activeOffsetX([-2, 2])
    .activeOffsetY([-2, 2])
    .onStart(() => {
      startX.value = boxX.value;
      startY.value = boxY.value;
      startW.value = boxW.value;
      startH.value = boxH.value;
    })
    .onUpdate((e) => {
      const box = { x: startX.value, y: startY.value, w: startW.value, h: startH.value };
      const bounds = { minX: bMinX.value, minY: bMinY.value, maxX: bMaxX.value, maxY: bMaxY.value };
      const res = calculateResizeBR(e.translationX, e.translationY, box, bounds);
      boxX.value = res.x; boxY.value = res.y; boxW.value = res.w; boxH.value = res.h;
    });

  const resetBox = () => {
    if (boundsReady) {
      const renderedWidth = bMaxX.value - bMinX.value;
      const renderedHeight = bMaxY.value - bMinY.value;
      const initialW = renderedWidth * 0.8;
      const initialH = renderedHeight * 0.8;
      boxW.value = initialW;
      boxH.value = initialH;
      boxX.value = bMinX.value + (renderedWidth - initialW) / 2;
      boxY.value = bMinY.value + (renderedHeight - initialH) / 2;
    }
  };

  const setFullImage = () => {
    if (boundsReady) {
      boxX.value = bMinX.value;
      boxY.value = bMinY.value;
      boxW.value = bMaxX.value - bMinX.value;
      boxH.value = bMaxY.value - bMinY.value;
    }
  };

  const handleDone = async () => {
    if (!boundsReady) return;

    setIsProcessing(true);
    try {
      const { x: realX, y: realY, w: realW, h: realH } = displayRectToSourceRect(
        boxX.value, boxY.value, boxW.value, boxH.value,
        bMinX.value, bMinY.value, imgScale.value,
        actualSize.w, actualSize.h
      );

      if (realW <= 10 || realH <= 10) {
        setIsProcessing(false);
        Alert.alert('Lỗi', 'Vùng chọn quá nhỏ. Em hãy kéo khung lớn hơn nhé.');
        return;
      }

      console.log('[DEV_STAGE][CROP_EXECUTION]', {
        activeUri,
        actualSize,
        imageLayout,
        box: { x: boxX.value, y: boxY.value, w: boxW.value, h: boxH.value },
        bMin: { x: bMinX.value, y: bMinY.value },
        imgScale: imgScale.value,
        cropRect: { originX: realX, originY: realY, width: realW, height: realH }
      });

      const result = await ImageManipulator.manipulateAsync(
        activeUri,
        [{ crop: { originX: realX, originY: realY, width: realW, height: realH } }],
        { compress: 0.95, format: ImageManipulator.SaveFormat.JPEG }
      );

      const croppedUri = ensureFileUri(result.uri);
      const cropW = result.width || Math.round(realW);
      const cropH = result.height || Math.round(realH);
      
      submissionDraftStore.updateDraft({
        uri: croppedUri,
        width: cropW,
        height: cropH,
      });

      logStageDiagnostic('CROP_OUTPUT', {
        uri: croppedUri,
        width: cropW,
        height: cropH,
        mimeType: 'image/jpeg',
        source: draft?.source,
      });

      console.log('[DEV_STAGE][CROP_IDENTITY]', {
        croppedUri,
        width: cropW,
        height: cropH,
        mimeType: 'image/jpeg',
        source: draft?.source,
        timestamp: new Date().toISOString(),
      });

      setIsProcessing(false);
      
      const postPrivacyMode = resolveFlowDomain(null, draft?.mode);
      const targetPath = postPrivacyMode === 'ARITHMETIC' ? '/preview' : (postPrivacyMode === 'OCR_PILOT' ? '/ocr-pilot/line-crop' : '/ocr-pilot/multiline-review');
      
      router.push({
        pathname: targetPath as any,
        params: { retrySubmissionId },
      });
    } catch (err: any) {
      setIsProcessing(false);
      console.error('[CROP] Crop execution error:', err?.message || err);
      Alert.alert('Lỗi', 'Không thể đọc kích thước ảnh bài tập hoặc cắt ảnh. Vui lòng thử lại.');
    }
  };

  if (!activeUri) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>Chưa có ảnh bài tập</Text>
        <AppButton title="Quay lại" onPress={() => router.back()} />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={styles.container}>
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        <AppHeader title="Cắt gọn ảnh bài tập" showBack />

        <View style={styles.instructionBox}>
          <Ionicons name="crop-outline" size={20} color={COLORS.primary} style={styles.instructionIcon} />
          <Text style={styles.instructionText}>
            Kéo các góc để chọn phần nội dung em muốn nhận diện.
          </Text>
        </View>

        <View style={styles.imageContainer}>
          <View
            style={styles.imageWrapper}
            collapsable={false}
            onLayout={(e) => setImageLayout(e.nativeEvent.layout)}
          >
            <Image 
              source={{ uri: activeUri }} 
              style={styles.image} 
              resizeMode="contain" 
              onError={(e) => {
                console.error('[CROP] Image load failed:', e.nativeEvent.error);
                setImageLoadError(true);
              }}
            />

            {imageLoadError && (
              <View style={styles.errorOverlay}>
                <Ionicons name="alert-circle" size={40} color={COLORS.error} />
                <Text style={styles.errorText}>Không thể hiển thị ảnh</Text>
              </View>
            )}

            {boundsReady && !imageLoadError && (
              <Animated.View style={[styles.cropRect, animatedBoxStyle]}>
                {/* Center Drag Zone */}
                <GestureDetector gesture={dragGesture}>
                  <Animated.View style={StyleSheet.absoluteFill as object} />
                </GestureDetector>
                
                {/* 4 Corner Resize Handles */}
                <GestureDetector gesture={resizeTL}>
                  <Animated.View style={[styles.cornerHitTarget, styles.tl]} hitSlop={HIT_SLOP}>
                    <View style={[styles.cornerVisual, styles.visualTL]} />
                  </Animated.View>
                </GestureDetector>
                <GestureDetector gesture={resizeTR}>
                  <Animated.View style={[styles.cornerHitTarget, styles.tr]} hitSlop={HIT_SLOP}>
                    <View style={[styles.cornerVisual, styles.visualTR]} />
                  </Animated.View>
                </GestureDetector>
                <GestureDetector gesture={resizeBL}>
                  <Animated.View style={[styles.cornerHitTarget, styles.bl]} hitSlop={HIT_SLOP}>
                    <View style={[styles.cornerVisual, styles.visualBL]} />
                  </Animated.View>
                </GestureDetector>
                <GestureDetector gesture={resizeBR}>
                  <Animated.View style={[styles.cornerHitTarget, styles.br]} hitSlop={HIT_SLOP}>
                    <View style={[styles.cornerVisual, styles.visualBR]} />
                  </Animated.View>
                </GestureDetector>

                {/* Aesthetic Edges (non-interactive) */}
                <View style={styles.cropOverlayEdgeTop} pointerEvents="none" />
                <View style={styles.cropOverlayEdgeBottom} pointerEvents="none" />
                <View style={styles.cropOverlayEdgeLeft} pointerEvents="none" />
                <View style={styles.cropOverlayEdgeRight} pointerEvents="none" />
              </Animated.View>
            )}

            {isProcessing && (
              <View style={styles.processingOverlay}>
                <ActivityIndicator size="large" color="#FFFFFF" />
                <Text style={styles.processingText}>Đang cắt ảnh...</Text>
              </View>
            )}
          </View>
        </View>

        <View style={styles.footer}>
          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.iconBtn} onPress={resetBox}>
              <Ionicons name="refresh-outline" size={24} color={COLORS.primary} />
              <Text style={styles.iconBtnText}>Đặt lại</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconBtn} onPress={setFullImage}>
              <Ionicons name="expand-outline" size={24} color={COLORS.primary} />
              <Text style={styles.iconBtnText}>Dùng toàn ảnh</Text>
            </TouchableOpacity>
          </View>
          
          <AppButton
            title={isProcessing ? "Đang xử lý..." : "Xác nhận cắt ảnh"}
            onPress={handleDone}
            disabled={!boundsReady || isProcessing || imageLoadError}
            variant="primary"
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Quay lại"
            variant="secondary"
            onPress={() => router.back()}
            disabled={isProcessing}
          />
        </View>
      </SafeAreaView>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SIZES.large,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginBottom: SIZES.large,
  },
  instructionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SIZES.medium,
    paddingVertical: SIZES.small,
    backgroundColor: COLORS.surfaceSubdued,
    borderBottomWidth: 1,
    borderColor: '#BFDBFE',
  },
  instructionIcon: {
    marginRight: 8,
  },
  instructionText: {
    fontSize: 13,
    color: COLORS.textPrimary,
    lineHeight: 18,
    flex: 1,
    fontWeight: '600',
  },
  imageContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  imageWrapper: {
    flex: 1,
    width: '100%',
    height: '100%',
    position: 'relative',
  },
  image: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  cropRect: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: '#22C55E',
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
  },
  cornerHitTarget: {
    position: 'absolute',
    width: 48,
    height: 48,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  cornerVisual: {
    width: 24,
    height: 24,
    borderColor: '#22C55E',
    position: 'absolute',
  },
  tl: { top: -24, left: -24 },
  tr: { top: -24, right: -24 },
  bl: { bottom: -24, left: -24 },
  br: { bottom: -24, right: -24 },
  visualTL: { top: 20, left: 20, borderTopWidth: 4, borderLeftWidth: 4 },
  visualTR: { top: 20, right: 20, borderTopWidth: 4, borderRightWidth: 4 },
  visualBL: { bottom: 20, left: 20, borderBottomWidth: 4, borderLeftWidth: 4 },
  visualBR: { bottom: 20, right: 20, borderBottomWidth: 4, borderRightWidth: 4 },
  cropOverlayEdgeTop: {
    position: 'absolute',
    top: -4,
    left: 20,
    right: 20,
    height: 12,
    backgroundColor: 'transparent',
  },
  cropOverlayEdgeBottom: {
    position: 'absolute',
    bottom: -4,
    left: 20,
    right: 20,
    height: 12,
    backgroundColor: 'transparent',
  },
  cropOverlayEdgeLeft: {
    position: 'absolute',
    left: -4,
    top: 20,
    bottom: 20,
    width: 12,
    backgroundColor: 'transparent',
  },
  cropOverlayEdgeRight: {
    position: 'absolute',
    right: -4,
    top: 20,
    bottom: 20,
    width: 12,
    backgroundColor: 'transparent',
  },
  processingOverlay: {
    ...StyleSheet.absoluteFill as object,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 100,
  },
  processingText: {
    color: '#FFFFFF',
    marginTop: 12,
    fontSize: 16,
    fontWeight: '600',
  },
  errorOverlay: {
    ...StyleSheet.absoluteFill as object,
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: COLORS.error,
    marginTop: 10,
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    padding: SIZES.large,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SIZES.medium,
  },
  iconBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
    backgroundColor: COLORS.surfaceSubdued,
    flex: 0.48,
    justifyContent: 'center',
  },
  iconBtnText: {
    marginLeft: 6,
    color: COLORS.primary,
    fontWeight: '600',
    fontSize: 14,
  },
});
