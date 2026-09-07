import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, SafeAreaView, PanResponder, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImageManipulator from 'expo-image-manipulator';
import { COLORS, SIZES } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';

export default function CropScreen() {
  const router = useRouter();
  const { uri, retrySubmissionId } = useLocalSearchParams<{ uri: string, retrySubmissionId?: string }>();
  
  const [cropRect, setCropRect] = useState<{x: number, y: number, width: number, height: number} | null>(null);
  const [imageLayout, setImageLayout] = useState({ width: 0, height: 0, x: 0, y: 0 });
  
  const panResponder = React.useMemo(() => {
    const state = { x: 0, y: 0 };
    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt, gestureState) => {
        state.x = evt.nativeEvent.locationX;
        state.y = evt.nativeEvent.locationY;
        setCropRect({ x: state.x, y: state.y, width: 0, height: 0 });
      },
      onPanResponderMove: (evt, gestureState) => {
        const currentX = evt.nativeEvent.locationX;
        const currentY = evt.nativeEvent.locationY;

        setCropRect({
          x: Math.min(state.x, currentX),
          y: Math.min(state.y, currentY),
          width: Math.abs(currentX - state.x),
          height: Math.abs(currentY - state.y)
        });
      },
      onPanResponderRelease: () => {
        setCropRect(prev => {
          if (prev && (prev.width < 50 || prev.height < 50)) {
            return null; // Ignore tiny accidental taps
          }
          return prev;
        });
      }
    });
  }, []);

  const handleDone = async () => {
    if (!cropRect) {
      Alert.alert('Thông báo', 'Vui lòng vẽ một khung quanh phần bài em muốn kiểm tra.');
      return;
    }

    try {
      // Calculate real crop dimensions based on rendered image size vs actual image size
      // We assume the image is rendered with resizeMode="contain".
      // This is an approximation since we don't have the exact rendered image dimensions inside the container easily.
      // For MVP, we'll use a rough ratio based on the container.
      
      let scaleX = 1;
      let scaleY = 1;

      // In a real robust implementation we'd calculate the contain box.
      // But we can just use the provided cropRect directly if we assume fill, but we use contain.
      // So this is a simplified MVP. We will just pass the rectangle.
      
      // Let's just mock the crop if it's too complex to get real image dimensions synchronously without Image.getSize
      // Wait, we can get image size!
      Image.getSize(uri, async (actualWidth, actualHeight) => {
        const containerRatio = imageLayout.width / imageLayout.height;
        const imageRatio = actualWidth / actualHeight;
        
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

        const scale = actualWidth / renderedWidth;

        const realX = Math.max(0, (cropRect.x - offsetX) * scale);
        const realY = Math.max(0, (cropRect.y - offsetY) * scale);
        const realWidth = Math.min(actualWidth - realX, cropRect.width * scale);
        const realHeight = Math.min(actualHeight - realY, cropRect.height * scale);

        if (realWidth <= 0 || realHeight <= 0) {
          Alert.alert('Lỗi', 'Vùng chọn không hợp lệ.');
          return;
        }

        const result = await ImageManipulator.manipulateAsync(
          uri,
          [{ crop: { originX: realX, originY: realY, width: realWidth, height: realHeight } }],
          { compress: 1, format: ImageManipulator.SaveFormat.JPEG }
        );

        // After crop, route to Privacy Gate again because crop changed the image!
        router.push({ 
          pathname: '/privacy' as any, 
          params: { uri: result.uri, retrySubmissionId } 
        });

      }, (error) => {
        Alert.alert('Lỗi', 'Không thể đọc kích thước ảnh.');
      });

    } catch (e) {
      console.error(e);
      Alert.alert('Lỗi', 'Không thể cắt ảnh.');
    }
  };

  if (!uri) {
    return <View style={styles.container}><Text>No Image Provided</Text></View>;
  }

  return (
    <SafeAreaView style={styles.container}>
      <AppHeader title="Chỉnh vùng bài" />
      
      <View style={styles.instructionBox}>
        <Text style={styles.instructionText}>
          Dùng tay vẽ một khung hình chữ nhật bao quanh phép tính em muốn kiểm tra.
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
                }
              ]}
            />
          )}
        </View>
      </View>

      <View style={styles.footer}>
        <AppButton 
          title="Xong" 
          onPress={handleDone} 
          disabled={!cropRect}
        />
        <View style={{ height: SIZES.small }} />
        <AppButton 
          title="Huỷ" 
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
  instructionBox: {
    padding: SIZES.medium,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderColor: COLORS.border,
  },
  instructionText: {
    fontSize: 14,
    color: COLORS.textPrimary,
    lineHeight: 20,
  },
  imageContainer: {
    flex: 1,
    backgroundColor: '#000',
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
    backgroundColor: 'rgba(74, 144, 226, 0.2)', // translucent blue
  },
  footer: {
    padding: SIZES.large,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  }
});
