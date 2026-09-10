import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, SafeAreaView, Alert } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { COLORS, SIZES } from '../constants/theme';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../components/ui/AppButton';
import { ScanFrame } from '../components/domain/ScanFrame';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function CameraScreen() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const insets = useSafeAreaInsets();

  const facing = 'back';
  const [flash, setFlash] = useState<'off' | 'on'>('off');

  if (!permission) {
    return <View style={styles.container} />;
  }

  const handlePickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        quality: 1,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const uri = result.assets[0].uri;
        router.push({ pathname: '/privacy' as any, params: { uri } });
      }
    } catch {
      Alert.alert('Lỗi', 'MathVision không mở được thư viện ảnh.');
    }
  };

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.permissionContainer}>
        <View style={styles.permissionIconBadge}>
          <Ionicons name="camera-outline" size={48} color={COLORS.primary} />
        </View>
        <Text style={styles.permissionTitle}>MathVision cần mở máy ảnh</Text>
        <Text style={styles.permissionText}>
          Em hãy cho phép ứng dụng truy cập máy ảnh để chụp và kiểm tra bài toán nhé.
        </Text>
        <View style={styles.permissionActions}>
          <AppButton title="Cho phép mở máy ảnh" onPress={requestPermission} />
          <View style={{ height: SIZES.medium }} />
          <AppButton
            title="Chọn ảnh từ thư viện"
            variant="secondary"
            onPress={handlePickImage}
          />
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            accessibilityRole="button"
            accessibilityLabel="Quay lại trang chủ"
          >
            <Text style={styles.backButtonText}>Quay lại</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const handleCapture = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync({ quality: 1, base64: false });
        if (photo) {
          router.push({ pathname: '/privacy' as any, params: { uri: photo.uri } });
        }
      } catch {
        Alert.alert('Lỗi', 'Không thể chụp ảnh, vui lòng thử lại.');
      }
    }
  };

  const toggleFlash = () => {
    setFlash((f) => (f === 'off' ? 'on' : 'off'));
  };

  return (
    <View style={styles.container}>
      <CameraView
        style={styles.camera}
        facing={facing}
        enableTorch={flash === 'on'}
        ref={cameraRef}
      >
        <SafeAreaView style={styles.safeArea}>
          {/* Header Controls */}
          <View style={[styles.header, { marginTop: Math.max(insets.top, SIZES.small) }]}>
            <TouchableOpacity
              onPress={() => router.back()}
              style={styles.iconButton}
              accessibilityRole="button"
              accessibilityLabel="Đóng máy ảnh, quay lại"
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="close" size={26} color="#FFFFFF" />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.iconButton}
              onPress={() =>
                Alert.alert(
                  'Hướng dẫn chụp bài',
                  '1. Đặt trọn vẹn phép tính vào khung.\n2. Chụp trong không gian đủ ánh sáng.\n3. Giữ chắc tay để ảnh không bị mờ.'
                )
              }
              accessibilityRole="button"
              accessibilityLabel="Xem hướng dẫn chụp ảnh"
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="help-circle-outline" size={26} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* Central Scan Frame */}
          <ScanFrame />

          {/* Bottom Controls */}
          <View
            style={[
              styles.footer,
              { paddingBottom: Math.max(insets.bottom + 8, SIZES.large) },
            ]}
          >
            <TouchableOpacity
              style={styles.footerAction}
              onPress={handlePickImage}
              accessibilityRole="button"
              accessibilityLabel="Chọn ảnh từ thư viện"
            >
              <View style={styles.footerIconCircle}>
                <Ionicons name="images-outline" size={24} color="#FFFFFF" />
              </View>
              <Text style={styles.footerActionText}>Thư viện</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.captureButton}
              onPress={handleCapture}
              accessibilityRole="button"
              accessibilityLabel="Chụp ảnh bài toán"
            >
              <View style={styles.captureInner} />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.footerAction}
              onPress={toggleFlash}
              accessibilityRole="button"
              accessibilityLabel={flash === 'on' ? 'Tắt đèn pin' : 'Bật đèn pin'}
            >
              <View
                style={[
                  styles.footerIconCircle,
                  flash === 'on' && styles.footerIconCircleActive,
                ]}
              >
                <Ionicons
                  name={flash === 'on' ? 'flash' : 'flash-off-outline'}
                  size={24}
                  color={flash === 'on' ? COLORS.warning : '#FFFFFF'}
                />
              </View>
              <Text style={styles.footerActionText}>
                {flash === 'on' ? 'Tắt đèn' : 'Bật đèn'}
              </Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  camera: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    justifyContent: 'space-between',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SIZES.xlarge,
    backgroundColor: COLORS.background,
  },
  permissionIconBadge: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 2,
    borderColor: '#BFDBFE',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SIZES.large,
  },
  permissionTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: SIZES.small,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 15,
    textAlign: 'center',
    marginBottom: SIZES.xxlarge,
    color: COLORS.textSecondary,
    lineHeight: 22,
    maxWidth: 320,
  },
  permissionActions: {
    width: '100%',
    maxWidth: 320,
  },
  backButton: {
    marginTop: SIZES.medium,
    alignItems: 'center',
    padding: SIZES.medium,
    minHeight: SIZES.minTouchTarget,
  },
  backButtonText: {
    fontSize: 15,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: SIZES.medium,
    zIndex: 20,
  },
  iconButton: {
    width: SIZES.minTouchTarget,
    height: SIZES.minTouchTarget,
    backgroundColor: 'rgba(15, 23, 42, 0.5)',
    borderRadius: SIZES.minTouchTarget / 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  footer: {
    width: '100%',
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    zIndex: 20,
    paddingTop: SIZES.large,
  },
  footerAction: {
    alignItems: 'center',
    width: 80,
    minHeight: SIZES.minTouchTarget,
  },
  footerIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  footerIconCircleActive: {
    backgroundColor: 'rgba(245, 158, 11, 0.25)',
    borderWidth: 1.5,
    borderColor: COLORS.warning,
  },
  footerActionText: {
    color: '#FFFFFF',
    fontSize: 12,
    marginTop: 6,
    fontWeight: '600',
  },
  captureButton: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  captureInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#FFFFFF',
  },
});
