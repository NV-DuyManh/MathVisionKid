import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { QualityBadge } from '../components/domain/QualityBadge';
import { Ionicons } from '@expo/vector-icons';
import * as ImageManipulator from 'expo-image-manipulator';

export default function PreviewScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri: string, originalUri?: string, retrySubmissionId?: string }>();
  
  const [imageUri, setImageUri] = useState<string>(params.uri || '');
  const [isChecking, setIsChecking] = useState(true);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsChecking(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  const handleContinue = () => {
    router.replace({ 
      pathname: '/processing' as any, 
      params: { 
        uri: imageUri,
        originalUri: params.originalUri,
        retrySubmissionId: params.retrySubmissionId
      } 
    });
  };

  const handleRotate = async () => {
    try {
      const manipResult = await ImageManipulator.manipulateAsync(
        imageUri,
        [{ rotate: 90 }],
        { compress: 1, format: ImageManipulator.SaveFormat.JPEG }
      );
      setImageUri(manipResult.uri);
    } catch (e) {
      Alert.alert('Lỗi', 'Không thể xoay ảnh. Vui lòng thử lại.');
    }
  };

  const handleCropMock = () => {
    // Phase 1.5 Limitation: Real interactive crop is complex to implement correctly cross-platform in a simple UI.
    // So we use a region-adjustment mock UI state to preserve architecture for later.
    Alert.alert('Chỉnh vùng bài', 'Tính năng cắt ảnh tương tác đang được phát triển.');
  };

  return (
    <View style={styles.container}>
      <AppHeader title="Xem lại bài" showBack />
      
      <View style={styles.content}>
        <View style={styles.imageContainer}>
          <Image source={{ uri: imageUri }} style={styles.image} resizeMode="contain" />
          
          <View style={styles.qualityOverlay}>
            {isChecking ? (
              <Text style={styles.checkingText}>Đang kiểm tra chất lượng ảnh...</Text>
            ) : (
              <View style={styles.badgeRow}>
                <QualityBadge label="Ảnh đủ sáng" isGood={true} />
                <QualityBadge label="Bài nằm trong khung" isGood={true} />
                <QualityBadge label="Một bài trong ảnh" isGood={true} />
              </View>
            )}
          </View>
        </View>

        <View style={styles.toolsRow}>
          <TouchableOpacity style={styles.toolButton} onPress={handleRotate}>
            <Ionicons name="refresh" size={24} color={COLORS.primary} />
            <Text style={styles.toolText}>Xoay</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.toolButton} onPress={handleCropMock}>
            <Ionicons name="crop" size={24} color={COLORS.primary} />
            <Text style={styles.toolText}>Chỉnh vùng bài</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.actionSection}>
          <AppButton 
            title="KIỂM TRA BÀI" 
            onPress={handleContinue} 
            disabled={isChecking}
          />
          <View style={{ height: SIZES.medium }} />
          <AppButton 
            title="Chụp lại" 
            variant="secondary"
            onPress={() => router.back()} 
          />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    padding: SIZES.medium,
  },
  imageContainer: {
    flex: 1,
    backgroundColor: '#000',
    borderRadius: SIZES.cardRadius,
    overflow: 'hidden',
    marginBottom: SIZES.medium,
  },
  image: {
    flex: 1,
  },
  qualityOverlay: {
    position: 'absolute',
    bottom: 0,
    width: '100%',
    padding: SIZES.medium,
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  checkingText: {
    textAlign: 'center',
    color: COLORS.textSecondary,
    fontStyle: 'italic',
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
  },
  toolsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: SIZES.xlarge,
    gap: SIZES.large,
  },
  toolButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    paddingHorizontal: SIZES.medium,
    paddingVertical: 10,
    borderRadius: SIZES.buttonRadius,
    elevation: 2,
    shadowColor: COLORS.primaryDark,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  toolText: {
    marginLeft: 8,
    color: COLORS.textPrimary,
    fontWeight: '600',
  },
  actionSection: {
    paddingBottom: SIZES.large,
  }
});
