import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, SafeAreaView, PanResponder, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import ViewShot from 'react-native-view-shot';
import { COLORS, SIZES, SHADOWS } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { Ionicons } from '@expo/vector-icons';
import { submissionDraftStore } from '../services/draft/submissionDraftStore';
import { ensureFileUri, logStageDiagnostic } from '../services/image/imagePipeline';
import * as ImageManipulator from 'expo-image-manipulator';

interface Mask {
  id: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export default function PrivacyGateScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri?: string; retrySubmissionId?: string }>();
  const draft = submissionDraftStore.getDraft();

  const rawUri = draft?.uri || (Array.isArray(params.uri) ? params.uri[0] : params.uri);
  const activeUri = rawUri ? ensureFileUri(rawUri) : '';
  const retrySubmissionId = draft?.retrySubmissionId || (Array.isArray(params.retrySubmissionId) ? params.retrySubmissionId[0] : params.retrySubmissionId);

  const [masks, setMasks] = useState<Mask[]>([]);
  const [selectedMaskId, setSelectedMaskId] = useState<number | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageLoadError, setImageLoadError] = useState(false);
  const viewShotRef = useRef<any>(null);

  useEffect(() => {
    if (activeUri) {
      logStageDiagnostic('PRIVACY_INPUT', {
        uri: activeUri,
        width: draft?.width,
        height: draft?.height,
        mimeType: draft?.mimeType,
        source: draft?.source,
      });
    }
  }, [activeUri, draft?.width, draft?.height, draft?.mimeType, draft?.source]);

  const panResponder = React.useMemo(() => {
    const state = {
      startX: 0,
      startY: 0,
      currentMaskId: null as number | null,
      action: null as 'DRAW' | 'MOVE' | 'RESIZE' | null,
      initialMask: null as Mask | null,
    };

    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        state.startX = evt.nativeEvent.locationX;
        state.startY = evt.nativeEvent.locationY;

        setMasks(prev => {
          let touchedMask: Mask | null = null;
          for (let i = prev.length - 1; i >= 0; i--) {
            const m = prev[i];
            if (
              state.startX >= m.x &&
              state.startX <= m.x + m.width &&
              state.startY >= m.y &&
              state.startY <= m.y + m.height
            ) {
              touchedMask = m;
              break;
            }
          }

          if (touchedMask) {
            state.currentMaskId = touchedMask.id;
            setSelectedMaskId(state.currentMaskId);
            state.initialMask = { ...touchedMask };

            if (
              state.startX >= touchedMask.x + touchedMask.width - 30 &&
              state.startY >= touchedMask.y + touchedMask.height - 30
            ) {
              state.action = 'RESIZE';
            } else {
              state.action = 'MOVE';
            }
            return prev;
          } else {
            state.currentMaskId = Date.now();
            setSelectedMaskId(state.currentMaskId);
            state.action = 'DRAW';
            return [
              ...prev,
              {
                id: state.currentMaskId,
                x: state.startX,
                y: state.startY,
                width: 0,
                height: 0,
              },
            ];
          }
        });
      },
      onPanResponderMove: (evt) => {
        if (!state.currentMaskId) return;

        const currentX = evt.nativeEvent.locationX;
        const currentY = evt.nativeEvent.locationY;
        const dx = currentX - state.startX;
        const dy = currentY - state.startY;

        setMasks(prev =>
          prev.map(mask => {
            if (mask.id === state.currentMaskId) {
              if (state.action === 'DRAW') {
                return {
                  ...mask,
                  x: Math.min(state.startX, currentX),
                  y: Math.min(state.startY, currentY),
                  width: Math.abs(currentX - state.startX),
                  height: Math.abs(currentY - state.startY),
                };
              } else if (state.action === 'MOVE' && state.initialMask) {
                return {
                  ...mask,
                  x: state.initialMask.x + dx,
                  y: state.initialMask.y + dy,
                };
              } else if (state.action === 'RESIZE' && state.initialMask) {
                return {
                  ...mask,
                  width: Math.max(24, state.initialMask.width + dx),
                  height: Math.max(24, state.initialMask.height + dy),
                };
              }
            }
            return mask;
          })
        );
      },
      onPanResponderRelease: () => {
        if (state.action === 'DRAW') {
          setMasks(prev => {
            const lastMask = prev.find(m => m.id === state.currentMaskId);
            if (lastMask && (lastMask.width < 20 || lastMask.height < 20)) {
              setSelectedMaskId(null);
              return prev.filter(m => m.id !== state.currentMaskId);
            }
            return prev;
          });
        }
        state.currentMaskId = null;
        state.action = null;
        state.initialMask = null;
      },
    });
  }, []);

  const undoLastMask = () => {
    setMasks(prev => prev.slice(0, -1));
    setSelectedMaskId(null);
  };

  const handleDone = async () => {
    if (!confirmed) return;

    setSelectedMaskId(null);

    try {
      // If no masks were drawn, do NOT rasterize via ViewShot!
      // Forward the normalized image without an additional privacy rasterization pass.
      if (masks.length === 0) {
        submissionDraftStore.updateDraft({ isMasked: false });
        logStageDiagnostic('PRIVACY_OUTPUT', {
          uri: activeUri,
          width: draft?.width,
          height: draft?.height,
          mimeType: draft?.mimeType || 'image/jpeg',
          source: draft?.source,
          extra: 'zero-mask bypass',
        });
        const targetPath = draft?.mode === 'OCR_PILOT_MULTILINE'
          ? '/ocr-pilot/multiline-review'
          : draft?.mode === 'OCR_PILOT'
            ? '/ocr-pilot/line-crop'
            : '/preview';
        router.push({
          pathname: targetPath as any,
          params: {
            uri: activeUri,
            originalUri: draft?.rawUri || activeUri,
            retrySubmissionId,
          },
        });
        return;
      }

      await new Promise(r => setTimeout(r, 120));

      if (viewShotRef.current && viewShotRef.current.capture) {
        const captured = await viewShotRef.current.capture();
        const finalMaskedUri = ensureFileUri(captured);

        // ViewShot output dimension audit: measure actual captured image file
        let outputWidth = draft?.width || 0;
        let outputHeight = draft?.height || 0;
        try {
          const manip = await ImageManipulator.manipulateAsync(finalMaskedUri, [], {});
          if (manip.width > 0 && manip.height > 0) {
            outputWidth = manip.width;
            outputHeight = manip.height;
          }
        } catch (inspectErr) {
          console.warn('[PRIVACY] Could not inspect ViewShot dimensions:', inspectErr);
        }

        // CRITICAL INVARIANT: Stored width/height MUST describe THAT NEW FILE
        submissionDraftStore.updateDraft({
          uri: finalMaskedUri,
          width: outputWidth,
          height: outputHeight,
          masks,
          isMasked: true,
        });

        logStageDiagnostic('PRIVACY_OUTPUT', {
          uri: finalMaskedUri,
          width: outputWidth,
          height: outputHeight,
          mimeType: 'image/jpeg',
          source: draft?.source,
          extra: `masked count=${masks.length}`,
        });

        const targetPath = draft?.mode === 'OCR_PILOT_MULTILINE'
          ? '/ocr-pilot/multiline-review'
          : draft?.mode === 'OCR_PILOT'
            ? '/ocr-pilot/line-crop'
            : '/preview';
        router.push({
          pathname: targetPath as any,
          params: {
            uri: finalMaskedUri,
            originalUri: activeUri,
            retrySubmissionId,
          },
        });
      }
    } catch (e) {
      console.error('[PRIVACY] Rasterization error:', e);
      Alert.alert('Lỗi', 'Không thể lưu ảnh đã che.');
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
    <SafeAreaView style={styles.container}>
      <AppHeader title="Bảo vệ thông tin riêng tư" showBack />

      {/* Child-friendly explanation */}
      <View style={styles.instructionCard}>
        <View style={styles.instructionHeader}>
          <Ionicons name="shield-checkmark" size={20} color={COLORS.primary} />
          <Text style={styles.instructionTitle}>Giữ an toàn cho em</Text>
        </View>
        <Text style={styles.instructionText}>
          Dùng ngón tay vẽ hộp đen che tên của em, tên trường hoặc khuôn mặt nếu có trong ảnh trước khi gửi bài nhé.
        </Text>
      </View>

      {/* Interactive Mask Canvas */}
      <View style={styles.imageContainer}>
        <ViewShot
          ref={viewShotRef}
          options={{ format: 'jpg', quality: 0.95 }}
          style={styles.viewShot}
        >
          <View
            style={styles.imageWrapper}
            collapsable={false}
            {...panResponder.panHandlers}
          >
            <Image
              source={{ uri: activeUri }}
              style={styles.image}
              resizeMode="contain"
              onLoadStart={() => {
                setImageLoaded(false);
                setImageLoadError(false);
              }}
              onLoad={() => {
                setImageLoaded(true);
                setImageLoadError(false);
              }}
              onError={(e) => {
                console.error('[PRIVACY] Image render failed:', e.nativeEvent.error);
                setImageLoadError(true);
              }}
            />

            {!imageLoaded && !imageLoadError && (
              <View style={styles.loadingOverlay}>
                <ActivityIndicator size="large" color={COLORS.primary} />
                <Text style={styles.loadingText}>Đang tải ảnh bài tập...</Text>
              </View>
            )}

            {imageLoadError && (
              <View style={styles.errorOverlay}>
                <Ionicons name="alert-circle" size={40} color={COLORS.error} />
                <Text style={styles.errorTitle}>Không thể hiển thị ảnh</Text>
                <Text style={styles.errorSub}>Vui lòng chụp lại hoặc chọn ảnh khác từ thư viện.</Text>
                <TouchableOpacity style={styles.retryButton} onPress={() => router.back()}>
                  <Text style={styles.retryButtonText}>Quay lại chụp ảnh</Text>
                </TouchableOpacity>
              </View>
            )}

            {masks.map(mask => {
              const isSelected = mask.id === selectedMaskId;
              return (
                <View
                  key={mask.id}
                  style={[
                    styles.maskBlock,
                    {
                      left: mask.x,
                      top: mask.y,
                      width: mask.width,
                      height: mask.height,
                      borderWidth: isSelected ? 2 : 0,
                      borderColor: COLORS.warning,
                    },
                  ]}
                />
              );
            })}
          </View>
        </ViewShot>

        {/* Floating Mask Control Buttons */}
        <View style={styles.floatingControls}>
          {selectedMaskId && (
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => {
                setMasks(prev => prev.filter(m => m.id !== selectedMaskId));
                setSelectedMaskId(null);
              }}
              accessibilityRole="button"
              accessibilityLabel="Xóa vùng che đang chọn"
            >
              <Ionicons name="trash-outline" size={20} color="#FFFFFF" />
              <Text style={styles.floatingButtonText}>Xóa vùng</Text>
            </TouchableOpacity>
          )}

          {masks.length > 0 && (
            <TouchableOpacity
              style={styles.undoButton}
              onPress={undoLastMask}
              accessibilityRole="button"
              accessibilityLabel="Hoàn tác vùng che vừa vẽ"
            >
              <Ionicons name="arrow-undo-outline" size={20} color="#FFFFFF" />
              <Text style={styles.floatingButtonText}>Hoàn tác</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Footer Confirmation & Actions */}
      <View style={[styles.footer, SHADOWS.medium]}>
        <TouchableOpacity
          style={styles.checkboxContainer}
          onPress={() => setConfirmed(!confirmed)}
          activeOpacity={0.8}
          accessibilityRole="checkbox"
          accessibilityState={{ checked: confirmed }}
          accessibilityLabel="Tôi đã kiểm tra và che thông tin riêng tư trong ảnh"
        >
          <Ionicons
            name={confirmed ? 'checkbox' : 'square-outline'}
            size={26}
            color={confirmed ? COLORS.primary : COLORS.textSecondary}
          />
          <Text style={styles.checkboxText}>
            Em đã kiểm tra và che hết thông tin riêng tư trong ảnh.
          </Text>
        </TouchableOpacity>

        <AppButton
          title="Tiếp tục xem lại"
          onPress={handleDone}
          disabled={!confirmed || imageLoadError}
          variant="primary"
        />
        <View style={{ height: SIZES.small }} />
        <AppButton
          title="Chụp lại ảnh khác"
          variant="secondary"
          onPress={() => router.back()}
        />
      </View>
    </SafeAreaView>
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
  instructionCard: {
    paddingHorizontal: SIZES.medium,
    paddingVertical: SIZES.small,
    backgroundColor: COLORS.surfaceSubdued,
    borderBottomWidth: 1,
    borderColor: '#BFDBFE',
  },
  instructionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 2,
  },
  instructionTitle: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  instructionText: {
    fontSize: 13,
    color: COLORS.textPrimary,
    lineHeight: 18,
  },
  imageContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
    position: 'relative',
  },
  viewShot: {
    flex: 1,
    width: '100%',
    height: '100%',
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
  loadingOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
    marginTop: 10,
    fontSize: 14,
    fontWeight: '600',
  },
  errorOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(15, 23, 42, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SIZES.large,
  },
  errorTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginTop: 12,
  },
  errorSub: {
    color: COLORS.textMuted,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 6,
    marginBottom: SIZES.large,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SIZES.large,
    paddingVertical: 10,
    borderRadius: SIZES.buttonRadius,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  maskBlock: {
    position: 'absolute',
    backgroundColor: '#000000',
    borderRadius: 4,
  },
  floatingControls: {
    position: 'absolute',
    bottom: SIZES.medium,
    left: SIZES.medium,
    right: SIZES.medium,
    flexDirection: 'row',
    justifyContent: 'space-between',
    zIndex: 10,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(220, 38, 38, 0.9)',
    minHeight: SIZES.minTouchTarget,
    paddingHorizontal: SIZES.medium,
    borderRadius: SIZES.pillRadius,
  },
  undoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    minHeight: SIZES.minTouchTarget,
    paddingHorizontal: SIZES.medium,
    borderRadius: SIZES.pillRadius,
    marginLeft: 'auto',
  },
  floatingButtonText: {
    color: '#FFFFFF',
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '700',
  },
  footer: {
    padding: SIZES.large,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: SIZES.minTouchTarget,
    marginBottom: SIZES.medium,
    paddingRight: SIZES.small,
  },
  checkboxText: {
    marginLeft: SIZES.small,
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
    flexShrink: 1,
    lineHeight: 20,
  },
});
