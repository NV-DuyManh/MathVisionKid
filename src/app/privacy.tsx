import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, SafeAreaView, PanResponder, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import ViewShot from 'react-native-view-shot';
import { COLORS, SIZES, SHADOWS } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { Ionicons } from '@expo/vector-icons';

interface Mask {
  id: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export default function PrivacyGateScreen() {
  const router = useRouter();
  const { uri, retrySubmissionId } = useLocalSearchParams<{ uri: string, retrySubmissionId?: string }>();
  const [masks, setMasks] = useState<Mask[]>([]);
  const [selectedMaskId, setSelectedMaskId] = useState<number | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const viewShotRef = useRef<any>(null);

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
    await new Promise(r => setTimeout(r, 100));

    try {
      if (viewShotRef.current && viewShotRef.current.capture) {
        const sanitizedUri = await viewShotRef.current.capture();
        router.push({
          pathname: '/preview' as any,
          params: {
            uri: sanitizedUri,
            originalUri: uri,
            retrySubmissionId,
          },
        });
      }
    } catch {
      Alert.alert('Lỗi', 'Không thể lưu ảnh đã che.');
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
          options={{ format: 'jpg', quality: 0.9 }}
          style={styles.viewShot}
        >
          <View style={styles.imageWrapper} {...panResponder.panHandlers}>
            <Image source={{ uri }} style={styles.image} resizeMode="contain" />

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

        {/* Floating Mask Control Buttons with >= 48dp touch targets */}
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
          disabled={!confirmed}
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
    width: '100%',
    height: '100%',
  },
  imageWrapper: {
    width: '100%',
    height: '100%',
  },
  image: {
    width: '100%',
    height: '100%',
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
