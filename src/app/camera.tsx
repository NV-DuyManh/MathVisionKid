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
  
  // Always default to rear (back) camera
  const facing = 'back';
  const [flash, setFlash] = useState<'off' | 'on'>('off');

  if (!permission) {
    return <View style={styles.container} />;
  }

  const handlePickImage = async () => {
    try {
      let result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        quality: 1,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const uri = result.assets[0].uri;
        router.push({ pathname: '/privacy' as any, params: { uri } });
      }
    } catch (e) {
      Alert.alert("Lỗi", "MathVision không mở được thư viện ảnh.");
    }
  };

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.permissionContainer}>
        <Text style={styles.permissionTitle}>MathVision chưa mở được camera</Text>
        <Text style={styles.permissionText}>Em hãy cho phép truy cập Camera để chụp bài nhé.</Text>
        <AppButton title="Cho phép Camera" onPress={requestPermission} />
        <View style={{ height: SIZES.medium }} />
        <AppButton title="Chọn ảnh từ thư viện" variant="secondary" onPress={handlePickImage} />
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Quay lại</Text>
        </TouchableOpacity>
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
      } catch (e) {
        Alert.alert("Lỗi", "Không thể chụp ảnh, vui lòng thử lại.");
      }
    }
  };

  const toggleFlash = () => {
    setFlash(f => (f === 'off' ? 'on' : 'off'));
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
            <TouchableOpacity onPress={() => router.back()} style={styles.iconButton} accessibilityLabel="Quay lại">
              <Ionicons name="close" size={32} color={COLORS.surface} />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.iconButton} accessibilityLabel="Trợ giúp">
              <Ionicons name="help-circle-outline" size={32} color={COLORS.surface} />
            </TouchableOpacity>
          </View>

          {/* Instructions */}
          <View style={styles.instructionContainer}>
            <View style={styles.instructionPill}>
              <Text style={styles.instructionText}>Chỉ chụp MỘT phép tính trong khung</Text>
            </View>
          </View>

          <ScanFrame />

          {/* Bottom Controls */}
          <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom, SIZES.medium) }]}>
            <TouchableOpacity style={styles.footerAction} onPress={handlePickImage} accessibilityLabel="Thư viện ảnh">
              <Ionicons name="images" size={28} color={COLORS.surface} />
              <Text style={styles.footerActionText}>Thư viện</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.captureButton} onPress={handleCapture} accessibilityLabel="Chụp ảnh">
              <View style={styles.captureInner} />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.footerAction} onPress={toggleFlash} accessibilityLabel="Đèn flash">
              <Ionicons name={flash === 'on' ? "flash" : "flash-off"} size={28} color={COLORS.surface} />
              <Text style={styles.footerActionText}>Đèn</Text>
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
    backgroundColor: '#000',
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
    padding: SIZES.large,
    backgroundColor: COLORS.background,
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: SIZES.small,
  },
  permissionText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: SIZES.xxlarge,
    color: COLORS.textPrimary,
  },
  backButton: {
    marginTop: SIZES.xlarge,
    padding: SIZES.medium,
  },
  backButtonText: {
    fontSize: 16,
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
    padding: 8,
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 24,
  },
  instructionContainer: {
    alignItems: 'center',
    marginTop: SIZES.large,
    zIndex: 20,
  },
  instructionPill: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: SIZES.large,
    paddingVertical: 12,
    borderRadius: 24,
  },
  instructionText: {
    color: COLORS.surface,
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    width: '100%',
    backgroundColor: 'rgba(0,0,0,0.5)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    zIndex: 20,
    paddingTop: SIZES.large,
  },
  footerAction: {
    alignItems: 'center',
    width: 80,
  },
  footerActionText: {
    color: COLORS.surface,
    fontSize: 12,
    marginTop: 4,
    fontWeight: '500',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: COLORS.surface,
  },
});
