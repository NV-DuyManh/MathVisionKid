import React, { useState } from 'react';
import { View, Text, StyleSheet, Image, SafeAreaView, PanResponder, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImageManipulator from 'expo-image-manipulator';
import { COLORS, SIZES } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { Ionicons } from '@expo/vector-icons';

export default function CropScreen() {
  const router = useRouter();
  const { uri, retrySubmissionId } = useLocalSearchParams<{ uri: string; retrySubmissionId?: string }>();

  const [cropRect, setCropRect] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [imageLayout, setImageLayout] = useState({ width: 0, height: 0, x: 0, y: 0 });

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

  const handleDone = async () => {
    if (!cropRect) {
      Alert.alert('Thông báo', 'Em hãy dùng ngón tay vẽ một khung quanh phép tính muốn kiểm tra nhé.');
      return;
    }

    try {
      Image.getSize(
        uri,
        async (actualWidth, actualHeight) => {
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
            Alert.alert('Lỗi', 'Vùng chọn quá nhỏ. Em hãy vẽ lại khung lớn hơn nhé.');
            return;
          }

          const result = await ImageManipulator.manipulateAsync(
            uri,
            [{ crop: { originX: realX, originY: realY, width: realWidth, height: realHeight } }],
            { compress: 1, format: ImageManipulator.SaveFormat.JPEG }
          );

          // Route to privacy screen with the newly cropped image
          router.push({
            pathname: '/privacy' as any,
            params: { uri: result.uri, retrySubmissionId },
          });
        },
        () => {
          Alert.alert('Lỗi', 'Không thể đọc kích thước ảnh bài tập.');
        }
      );
    } catch {
      Alert.alert('Lỗi', 'Không thể cắt ảnh.');
    }
  };

  if (!uri) {
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
          onLayout={(e) => setImageLayout(e.nativeEvent.layout)}
          {...panResponder.panHandlers}
        >
          <Image source={{ uri }} style={styles.image} resizeMode="contain" />

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
        </View>
      </View>

      <View style={styles.footer}>
        <AppButton
          title="Xong, kiểm tra vùng này"
          onPress={handleDone}
          disabled={!cropRect}
          variant="primary"
        />
        <View style={{ height: SIZES.small }} />
        <AppButton
          title="Hủy bỏ"
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
    width: '100%',
    height: '100%',
  },
  image: {
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
  footer: {
    padding: SIZES.large,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  },
});
