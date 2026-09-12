import React, { useState } from 'react';
import { View, Text, StyleSheet, Image, PanResponder, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImageManipulator from 'expo-image-manipulator';
import { COLORS, SIZES } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { Ionicons } from '@expo/vector-icons';
import { submissionDraftStore } from '../services/draft/submissionDraftStore';
import { ensureFileUri, logStageDiagnostic } from '../services/image/imagePipeline';

export default function CropScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri?: string; retrySubmissionId?: string }>();
  const draft = submissionDraftStore.getDraft();

  const rawUri = draft?.uri || (Array.isArray(params.uri) ? params.uri[0] : params.uri);
  const activeUri = rawUri ? ensureFileUri(rawUri) : '';
  const retrySubmissionId = draft?.retrySubmissionId || (Array.isArray(params.retrySubmissionId) ? params.retrySubmissionId[0] : params.retrySubmissionId);

  const [cropRect, setCropRect] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [imageLayout, setImageLayout] = useState({ width: 0, height: 0, x: 0, y: 0 });
  const [isProcessing, setIsProcessing] = useState(false);

  React.useEffect(() => {
    if (activeUri) {
      logStageDiagnostic('CROP_INPUT', {
        uri: activeUri,
        width: draft?.width,
        height: draft?.height,
        mimeType: draft?.mimeType,
        source: draft?.source,
      });
    }
  }, [activeUri, draft?.width, draft?.height, draft?.mimeType, draft?.source]);

  const panResponder = React.useMemo(() => {
    const state = { x: 0, y: 0 };
    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        state.x = evt.nativeEvent.locationX;
        state.y = evt.nativeEvent.locationY;
        setCropRect({ x: state.x, y: state.y, width: 0, height: 0 });
      },
      onPanResponderMove: (evt) => {
        const currentX = evt.nativeEvent.locationX;
        const currentY = evt.nativeEvent.locationY;

        setCropRect({
          x: Math.min(state.x, currentX),
          y: Math.min(state.y, currentY),
          width: Math.abs(currentX - state.x),
          height: Math.abs(currentY - state.y),
        });
      },
      onPanResponderRelease: () => {
        setCropRect(prev => {
          if (prev && (prev.width < 40 || prev.height < 40)) {
            return null;
          }
          return prev;
        });
      },
    });
  }, []);

  const resolveImageDimensions = async (uri: string): Promise<{ width: number; height: number }> => {
    // 1. Primary: Use dimensions already known in submission draft
    if (draft && draft.width > 0 && draft.height > 0) {
      return { width: draft.width, height: draft.height };
    }

    // 2. Secondary: Fast native resolution via ImageManipulator (reads JPEG header on Android)
    try {
      const manip = await ImageManipulator.manipulateAsync(uri, [], {});
      if (manip.width > 0 && manip.height > 0) {
        return { width: manip.width, height: manip.height };
      }
    } catch (e) {
      console.warn('[CROP] Native header inspection error:', e);
    }

    // 3. Fallback: React Native Image.getSize
    return new Promise((resolve, reject) => {
      Image.getSize(
        uri,
        (width, height) => resolve({ width, height }),
        (error) => reject(error)
      );
    });
  };

  const handleDone = async () => {
    if (!cropRect) {
      Alert.alert('Thông báo', 'Em hãy dùng ngón tay vẽ một khung quanh phép tính muốn kiểm tra nhé.');
      return;
    }

    setIsProcessing(true);
    try {
      const dimensions = await resolveImageDimensions(activeUri);
      const actualWidth = dimensions.width;
      const actualHeight = dimensions.height;

      const containerRatio = imageLayout.width / (imageLayout.height || 1);
      const imageRatio = actualWidth / (actualHeight || 1);

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

      const scale = actualWidth / (renderedWidth || 1);

      const realX = Math.max(0, (cropRect.x - offsetX) * scale);
      const realY = Math.max(0, (cropRect.y - offsetY) * scale);
      const realWidth = Math.min(actualWidth - realX, cropRect.width * scale);
      const realHeight = Math.min(actualHeight - realY, cropRect.height * scale);

      if (realWidth <= 10 || realHeight <= 10) {
        setIsProcessing(false);
        Alert.alert('Lỗi', 'Vùng chọn quá nhỏ. Em hãy vẽ lại khung lớn hơn nhé.');
        return;
      }

      const result = await ImageManipulator.manipulateAsync(
        activeUri,
        [{ crop: { originX: realX, originY: realY, width: realWidth, height: realHeight } }],
        { compress: 0.95, format: ImageManipulator.SaveFormat.JPEG }
      );

      const croppedUri = ensureFileUri(result.uri);
      const cropW = result.width || Math.round(realWidth);
      const cropH = result.height || Math.round(realHeight);
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

      setIsProcessing(false);
      // Route to privacy screen with the newly cropped image
      router.push({
        pathname: '/privacy' as any,
        params: { uri: croppedUri, retrySubmissionId },
      });
    } catch (err) {
      setIsProcessing(false);
      console.error('[CROP] Crop execution error:', err);
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
    <SafeAreaView style={styles.container}>
      <AppHeader title="Chỉnh vùng bài toán" showBack />

      <View style={styles.instructionBox}>
        <Ionicons name="hand-right-outline" size={20} color={COLORS.primary} style={styles.instructionIcon} />
        <Text style={styles.instructionText}>
          Dùng ngón tay kéo thành một khung hình chữ nhật bao trọn phép tính em muốn kiểm tra.
        </Text>
      </View>

      <View style={styles.imageContainer}>
        <View
          style={styles.imageWrapper}
          collapsable={false}
          onLayout={(e) => setImageLayout(e.nativeEvent.layout)}
          {...panResponder.panHandlers}
        >
          <Image source={{ uri: activeUri }} style={styles.image} resizeMode="contain" />

          {cropRect && (
            <View
              style={[
                styles.cropRect,
                {
                  left: cropRect.x,
                  top: cropRect.y,
                  width: cropRect.width,
                  height: cropRect.height,
                },
              ]}
            >
              <View style={styles.cropCornerTopLeft} />
              <View style={styles.cropCornerTopRight} />
              <View style={styles.cropCornerBottomLeft} />
              <View style={styles.cropCornerBottomRight} />
            </View>
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
        <AppButton
          title={isProcessing ? "Đang xử lý..." : "Xong, kiểm tra vùng này"}
          onPress={handleDone}
          disabled={!cropRect || isProcessing}
          variant="primary"
        />
        <View style={{ height: SIZES.small }} />
        <AppButton
          title="Hủy bỏ"
          variant="secondary"
          onPress={() => router.back()}
          disabled={isProcessing}
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
    borderColor: COLORS.primary,
    backgroundColor: 'rgba(37, 99, 235, 0.18)',
  },
  cropCornerTopLeft: {
    position: 'absolute',
    top: -2,
    left: -2,
    width: 14,
    height: 14,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderColor: '#FFFFFF',
  },
  cropCornerTopRight: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 14,
    height: 14,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderColor: '#FFFFFF',
  },
  cropCornerBottomLeft: {
    position: 'absolute',
    bottom: -2,
    left: -2,
    width: 14,
    height: 14,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderColor: '#FFFFFF',
  },
  cropCornerBottomRight: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 14,
    height: 14,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderColor: '#FFFFFF',
  },
  processingOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingText: {
    color: '#FFFFFF',
    marginTop: 8,
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    padding: SIZES.large,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  },
});
