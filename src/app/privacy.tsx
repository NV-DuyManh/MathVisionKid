import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, SafeAreaView, PanResponder, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import ViewShot from 'react-native-view-shot';
import { COLORS, SIZES } from '../constants/theme';
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
      initialMask: null as Mask | null
    };

    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt, gestureState) => {
        state.startX = evt.nativeEvent.locationX;
        state.startY = evt.nativeEvent.locationY;
        
        let touchedMask: Mask | null = null;
        setMasks(prev => {
          for (let i = prev.length - 1; i >= 0; i--) {
            const m = prev[i];
            if (state.startX >= m.x && state.startX <= m.x + m.width && state.startY >= m.y && state.startY <= m.y + m.height) {
              touchedMask = m;
              break;
            }
          }
          
          if (touchedMask) {
            state.currentMaskId = touchedMask.id;
            setSelectedMaskId(state.currentMaskId);
            state.initialMask = { ...touchedMask };
            
            if (state.startX >= touchedMask.x + touchedMask.width - 30 && state.startY >= touchedMask.y + touchedMask.height - 30) {
              state.action = 'RESIZE';
            } else {
              state.action = 'MOVE';
            }
            return prev;
          } else {
            state.currentMaskId = Date.now();
            setSelectedMaskId(state.currentMaskId);
            state.action = 'DRAW';
            return [...prev, {
              id: state.currentMaskId,
              x: state.startX,
              y: state.startY,
              width: 0,
              height: 0
            }];
          }
        });
      },
      onPanResponderMove: (evt, gestureState) => {
        if (!state.currentMaskId) return;

        const currentX = evt.nativeEvent.locationX;
        const currentY = evt.nativeEvent.locationY;
        const dx = currentX - state.startX;
        const dy = currentY - state.startY;

        setMasks(prev => prev.map(mask => {
          if (mask.id === state.currentMaskId) {
            if (state.action === 'DRAW') {
              return {
                ...mask,
                x: Math.min(state.startX, currentX),
                y: Math.min(state.startY, currentY),
                width: Math.abs(currentX - state.startX),
                height: Math.abs(currentY - state.startY)
              };
            } else if (state.action === 'MOVE' && state.initialMask) {
              return {
                ...mask,
                x: state.initialMask.x + dx,
                y: state.initialMask.y + dy
              };
            } else if (state.action === 'RESIZE' && state.initialMask) {
              return {
                ...mask,
                width: Math.max(20, state.initialMask.width + dx),
                height: Math.max(20, state.initialMask.height + dy)
              };
            }
          }
          return mask;
        }));
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
      }
    });
  }, []);

  const undoLastMask = () => {
    setMasks(prev => prev.slice(0, -1));
  };

  const handleDone = async () => {
    if (!confirmed) return;
    
    setSelectedMaskId(null);
    await new Promise(r => setTimeout(r, 100)); // wait for selection border to hide

    try {
      if (viewShotRef.current && viewShotRef.current.capture) {
        const sanitizedUri = await viewShotRef.current.capture();
        router.push({ 
          pathname: '/preview' as any, 
          params: { 
            uri: sanitizedUri, 
            originalUri: uri,
            retrySubmissionId
          } 
        });
      }
    } catch (e) {
      console.error('Failed to capture sanitized image', e);
      Alert.alert("Lỗi", "Không thể lưu ảnh đã che.");
    }
  };

  if (!uri) {
    return <View style={styles.container}><Text>No Image Provided</Text></View>;
  }

  return (
    <SafeAreaView style={styles.container}>
      <AppHeader title="Kiểm tra thông tin riêng tư" />
      
      <View style={styles.instructionBox}>
        <Text style={styles.instructionText}>
          Trước khi gửi bài, hãy vuốt trên ảnh để che các thông tin cá nhân xuất hiện trong ảnh (Tên học sinh, tên trường, khuôn mặt...).
        </Text>
      </View>

      <View style={styles.imageContainer}>
        <ViewShot 
          ref={viewShotRef} 
          options={{ format: "jpg", quality: 0.9 }} 
          style={styles.viewShot}
        >
          <View 
            style={styles.imageWrapper}
            {...panResponder.panHandlers}
          >
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
                      borderColor: COLORS.primary,
                    }
                  ]}
                />
              );
            })}
          </View>
        </ViewShot>

        {selectedMaskId && (
          <TouchableOpacity 
            style={styles.deleteButton} 
            onPress={() => {
              setMasks(prev => prev.filter(m => m.id !== selectedMaskId));
              setSelectedMaskId(null);
            }}
          >
            <Ionicons name="trash" size={24} color={COLORS.surface} />
            <Text style={styles.undoText}>Xóa vùng</Text>
          </TouchableOpacity>
        )}

        {masks.length > 0 && (
          <TouchableOpacity style={styles.undoButton} onPress={undoLastMask}>
            <Ionicons name="arrow-undo" size={24} color={COLORS.surface} />
            <Text style={styles.undoText}>Hoàn tác</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.footer}>
        <TouchableOpacity 
          style={styles.checkboxContainer} 
          onPress={() => setConfirmed(!confirmed)}
        >
          <Ionicons 
            name={confirmed ? "checkbox" : "square-outline"} 
            size={24} 
            color={confirmed ? COLORS.primary : COLORS.textSecondary} 
          />
          <Text style={styles.checkboxText}>
            Tôi đã kiểm tra và che thông tin cá nhân trong ảnh.
          </Text>
        </TouchableOpacity>

        <AppButton 
          title="Hoàn tất" 
          onPress={handleDone} 
          disabled={!confirmed}
        />
        <View style={{ height: SIZES.small }} />
        <AppButton 
          title="Chụp lại" 
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
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
    overflow: 'hidden',
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
    backgroundColor: '#000000', // Solid opaque block for irreversible mask
  },
  undoButton: {
    position: 'absolute',
    bottom: SIZES.large,
    right: SIZES.large,
    backgroundColor: 'rgba(0,0,0,0.6)',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 24,
  },
  deleteButton: {
    position: 'absolute',
    bottom: SIZES.large,
    left: SIZES.large,
    backgroundColor: 'rgba(255,59,48,0.8)',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 24,
  },
  undoText: {
    color: COLORS.surface,
    marginLeft: 8,
    fontWeight: '600',
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
    marginBottom: SIZES.large,
    paddingRight: SIZES.large,
  },
  checkboxText: {
    marginLeft: SIZES.small,
    fontSize: 14,
    color: COLORS.textPrimary,
    flexShrink: 1,
  }
});
