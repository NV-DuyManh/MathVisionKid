import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
  Image,
  Dimensions,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { submissionDraftStore } from '../../services/draft/submissionDraftStore';
import { OcrPilotService, LineBox } from '../../services/api/OcrPilotService';

const SCREEN_WIDTH = Dimensions.get('window').width;

export default function MultilineReviewScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const draft = submissionDraftStore.getDraft();
  const imageUri = draft?.croppedImageUri || draft?.uri || (params.uri as string) || '';
  const imageSessionId = draft?.imageSessionId || imageUri;

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [origWidth, setOrigWidth] = useState(draft?.width || 800);
  const [origHeight, setOrigHeight] = useState(draft?.height || 600);
  const [displayHeight, setDisplayHeight] = useState(300);
  const [boxes, setBoxes] = useState<LineBox[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const displayWidth = SCREEN_WIDTH - 32;
  const detectRequestIdRef = useRef(0);
  const initialLoadDoneRef = useRef<string | null>(null);

  useEffect(() => {
    console.log('[MULTILINE_PAGE_SOURCE] MULTILINE_PAGE_SOURCE=POST_CROP_ACTIVE_URI', {
      uri: imageUri,
      isMasked: draft?.isMasked,
      rawUriPresent: !!draft?.rawUri,
      draftWidth: draft?.width,
      draftHeight: draft?.height,
      timestamp: new Date().toISOString(),
    });
  }, [imageUri, draft?.isMasked, draft?.rawUri, draft?.width, draft?.height]);

  const loadAutoDetection = useCallback(async (uri: string, force: boolean = false) => {
    const currentReqId = ++detectRequestIdRef.current;
    console.log(`[MULTILINE] Starting loadAutoDetection (reqId=${currentReqId})`, {
      uri,
      force,
      timestamp: new Date().toISOString(),
    });
    try {
      setLoading(true);
      const res = await OcrPilotService.detectLines(uri, true);

      // Stale response guard: ignore if a newer request was dispatched
      if (currentReqId !== detectRequestIdRef.current) {
        console.warn(`[MULTILINE] Discarding stale detection response (reqId=${currentReqId}, active=${detectRequestIdRef.current})`);
        return;
      }

      console.log(`[MULTILINE] Detection response received (reqId=${currentReqId})`, {
        width: res.width,
        height: res.height,
        lineCount: res.lines?.length || 0,
        detectorVersion: (res as any).detector_version,
        lines: res.lines?.map(l => ({ id: l.line_id, y: l.y, height: l.height }))
      });

      if (res.width) setOrigWidth(res.width);
      if (res.height) {
        setOrigHeight(res.height);
        const calculatedH = (res.height / res.width) * displayWidth;
        setDisplayHeight(Math.min(calculatedH, 450));
      }

      const incomingLines = res.lines || [];
      setBoxes((prev) => {
        // Prevent accidental overwrite of valid boxes with 0 on background retry
        if (!force && prev.length > 0 && incomingLines.length === 0) {
          console.warn('[MULTILINE] Preserving existing boxes; ignoring 0-count response on non-force load');
          return prev;
        }
        return incomingLines;
      });

      if (incomingLines.length > 0) {
        setSelectedId(incomingLines[0].line_id);
      } else if (force) {
        setSelectedId(null);
      }
    } catch (err: any) {
      if (currentReqId !== detectRequestIdRef.current) return;
      console.warn('[MULTILINE] Detection warning:', err?.message || err);

      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        Alert.alert('Phiên đăng nhập đã hết hạn', 'Vui lòng đăng nhập lại để tiếp tục.', [
          { text: 'Đăng nhập', onPress: () => router.replace('/login') }
        ]);
      } else {
        Alert.alert('Lỗi nhận diện', 'Không thể tự động phát hiện dòng chữ. Vui lòng thử lại hoặc thêm thủ công.');
      }

      // Empty lines on detection failure only if user explicitly forced refresh or no boxes exist
      setBoxes((prev) => (force ? [] : prev));
      if (force) setSelectedId(null);
    } finally {
      if (currentReqId === detectRequestIdRef.current) {
        setLoading(false);
      }
    }
  }, [displayWidth]);

  useEffect(() => {
    if (!imageUri) {
      Alert.alert('Lỗi', 'Không tìm thấy ảnh để nhận diện.', [
        { text: 'Quay lại', onPress: () => router.back() },
      ]);
      return;
    }

    if (initialLoadDoneRef.current === imageSessionId) return;
    
    // Clear old state before starting new detection on a new image
    if (initialLoadDoneRef.current !== null) {
      setBoxes([]);
      setSelectedId(null);
    }
    
    initialLoadDoneRef.current = imageSessionId;

    // Inspect real image dimensions if not present
    Image.getSize(
      imageUri,
      (w, h) => {
        setOrigWidth(w);
        setOrigHeight(h);
        const calculatedH = (h / w) * displayWidth;
        setDisplayHeight(Math.min(calculatedH, 450));
        loadAutoDetection(imageUri, true);
      },
      () => {
        loadAutoDetection(imageUri, true);
      }
    );
  }, [imageUri, displayWidth, router, loadAutoDetection]);

  const scaleX = displayWidth / (origWidth || 1);
  const scaleY = displayHeight / (origHeight || 1);

  const selectedBox = boxes.find((b) => b.line_id === selectedId);

  const updateSelectedBox = (updater: (prev: LineBox) => LineBox) => {
    if (!selectedId) return;
    setBoxes((prev) => {
      const next = prev.map((b) => (b.line_id === selectedId ? updater(b) : b));
      // Re-sort top-to-bottom and renumber
      next.sort((a, b) => a.y - b.y);
      return next.map((b, idx) => ({ ...b, order: idx + 1 }));
    });
  };

  const handleMove = (dx: number, dy: number) => {
    updateSelectedBox((b) => {
      const stepX = Math.round(origWidth * 0.02) * dx;
      const stepY = Math.round(origHeight * 0.02) * dy;
      const newX = Math.max(0, Math.min(b.x + stepX, origWidth - b.width));
      const newY = Math.max(0, Math.min(b.y + stepY, origHeight - b.height));
      return { ...b, x: newX, y: newY };
    });
  };

  const handleResize = (dw: number, dh: number) => {
    updateSelectedBox((b) => {
      const stepW = Math.round(origWidth * 0.03) * dw;
      const stepH = Math.round(origHeight * 0.02) * dh;
      const newW = Math.max(30, Math.min(b.width + stepW, origWidth - b.x));
      const newH = Math.max(15, Math.min(b.height + stepH, origHeight - b.y));
      return { ...b, width: newW, height: newH };
    });
  };

  const handleDelete = () => {
    if (!selectedId) return;
    setBoxes((prev) => {
      const remaining = prev.filter((b) => b.line_id !== selectedId);
      remaining.sort((a, b) => a.y - b.y);
      const renumbered = remaining.map((b, idx) => ({ ...b, order: idx + 1 }));
      if (renumbered.length > 0) {
        setSelectedId(renumbered[0].line_id);
      } else {
        setSelectedId(null);
      }
      return renumbered;
    });
  };

  const handleAddLine = () => {
    const newId = `line_${Date.now()}`;
    const defaultW = Math.round(origWidth * 0.85);
    const defaultH = Math.round(origHeight * 0.1);
    const defaultX = Math.round((origWidth - defaultW) / 2);
    const defaultY = Math.round(origHeight * 0.4);

    const newBox: LineBox = {
      line_id: newId,
      x: defaultX,
      y: defaultY,
      width: defaultW,
      height: defaultH,
      order: boxes.length + 1,
    };

    setBoxes((prev) => {
      const combined = [...prev, newBox];
      combined.sort((a, b) => a.y - b.y);
      return combined.map((b, idx) => ({ ...b, order: idx + 1 }));
    });
    setSelectedId(newId);
  };

  const handleConfirmLines = async () => {
    if (boxes.length === 0) {
      Alert.alert('Chưa có dòng nào', 'Vui lòng thêm ít nhất 1 dòng chữ trước khi nhận diện.');
      return;
    }

    try {
      setProcessing(true);
      // Deterministically sort top-to-bottom
      const sorted = [...boxes].sort((a, b) => a.y - b.y);
      const renumbered = sorted.map((b, idx) => ({ ...b, order: idx + 1 }));

      const trial = await OcrPilotService.createMultilineTrial(
        imageUri,
        renumbered,
        (draft?.source as any) || 'CAMERA',
        true   // Privacy confirmed
      );

      router.push({
        pathname: '/ocr-pilot/multiline-result' as any,
        params: { trialId: trial.trialId },
      });
    } catch (e: any) {
      setProcessing(false);
      const status = e?.response?.status;
      if (status === 401 || status === 403) {
        console.warn('[MULTILINE] Auth expired, user should log in again.', e?.message);
        Alert.alert('Phiên đăng nhập hết hạn', 'Vui lòng đăng nhập lại để tiếp tục.', [
          { text: 'Đăng nhập', onPress: () => router.replace('/login') }
        ]);
      } else {
        console.error('[MULTILINE] Submit error:', e);
        Alert.alert('Lỗi nhận diện', e?.message || 'Không thể kết nối đến máy chủ nhận diện.');
      }
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Đang tự động phát hiện các dòng chữ...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="Quay lại"
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Chỉnh sửa khung các dòng</Text>
        <TouchableOpacity
          onPress={() => {
            if (boxes.length > 0) {
              Alert.alert(
                'Phát hiện lại',
                'Phát hiện lại sẽ thay thế các khung hiện tại. Bạn có chắc chắn muốn tiếp tục?',
                [
                  { text: 'Hủy', style: 'cancel' },
                  { text: 'Đồng ý', onPress: () => loadAutoDetection(imageUri, true) }
                ]
              );
            } else {
              loadAutoDetection(imageUri, true);
            }
          }}
          style={styles.resetButton}
          accessibilityRole="button"
          accessibilityLabel="Phát hiện lại"
        >
          <Ionicons name="refresh" size={20} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <Text style={styles.instruction}>
        Đã tìm thấy {boxes.length} dòng chữ. Em có thể chạm vào từng khung để điều chỉnh vị trí hoặc xóa bớt:
      </Text>

      {/* Image Overlay Area */}
      <View style={[styles.imageContainer, { width: displayWidth, height: displayHeight }]}>
            <Image
              source={{ uri: imageUri }}
              style={{ width: displayWidth, height: displayHeight }}
              resizeMode="contain"
              onError={(e) => {
                console.error('[MULTILINE] Image load failed:', e.nativeEvent.error);
              }}
            />

        {boxes.map((box) => {
          const isSelected = box.line_id === selectedId;
          const left = box.x * scaleX;
          const top = box.y * scaleY;
          const w = box.width * scaleX;
          const h = box.height * scaleY;

          return (
            <TouchableOpacity
              key={box.line_id}
              activeOpacity={0.9}
              onPress={() => setSelectedId(box.line_id)}
              style={[
                styles.boxOverlay,
                {
                  left,
                  top,
                  width: Math.max(w, 20),
                  height: Math.max(h, 15),
                  borderColor: isSelected ? '#10B981' : '#3B82F6',
                  backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.22)' : 'rgba(59, 130, 246, 0.15)',
                  borderWidth: isSelected ? 2.5 : 1.5,
                },
              ]}
            >
              <View style={[styles.orderTag, { backgroundColor: isSelected ? '#10B981' : '#3B82F6' }]}>
                <Text style={styles.orderTagText}>{box.order}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Box Editing Controls or Blank State Card */}
      {boxes.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="alert-circle-outline" size={40} color={COLORS.textSecondary} style={{ marginBottom: 8 }} />
          <Text style={styles.emptyTitle}>Chưa phát hiện được dòng chữ nào.</Text>
          <Text style={styles.emptySubtitle}>
            Không tìm thấy văn bản trên ảnh, hoặc chữ viết quá mờ/nhỏ. Bạn có thể tự thêm dòng, thử phát hiện lại hoặc chụp/chọn ảnh khác.
          </Text>
          <View style={styles.emptyActions}>
            <TouchableOpacity
              style={styles.emptyBtn}
              onPress={handleAddLine}
              accessibilityRole="button"
              accessibilityLabel="Thêm dòng thủ công"
            >
              <Ionicons name="add-circle" size={18} color="#FFFFFF" />
              <Text style={styles.emptyBtnText}>Thêm dòng thủ công</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.emptyBtn, styles.emptyBtnOutline]}
              onPress={() => loadAutoDetection(imageUri, true)}
              accessibilityRole="button"
              accessibilityLabel="Phát hiện lại"
            >
              <Ionicons name="refresh" size={18} color={COLORS.primary} />
              <Text style={[styles.emptyBtnText, { color: COLORS.primary }]}>Phát hiện lại</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.emptyBtn, styles.emptyBtnOutline]}
              onPress={() => router.back()}
              accessibilityRole="button"
              accessibilityLabel="Chụp hoặc chọn ảnh khác"
            >
              <Ionicons name="camera-outline" size={18} color={COLORS.textSecondary} />
              <Text style={[styles.emptyBtnText, { color: COLORS.textSecondary }]}>Chụp/chọn ảnh khác</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : selectedBox ? (
        <View style={styles.controlCard}>
          <View style={styles.controlHeaderRow}>
            <Text style={styles.controlTitle}>
              Đang chỉnh: <Text style={{ color: COLORS.primary, fontWeight: '700' }}>Dòng [{selectedBox.order}]</Text>
            </Text>
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={handleDelete}
              accessibilityRole="button"
              accessibilityLabel="Xóa dòng này"
            >
              <Ionicons name="trash-outline" size={18} color="#DC2626" />
              <Text style={styles.deleteButtonText}>Xóa dòng</Text>
            </TouchableOpacity>
          </View>

          {/* D-Pad Style Controls */}
          <View style={styles.controlsRow}>
            <View style={styles.controlGroup}>
              <Text style={styles.groupLabel}>Di chuyển:</Text>
              <View style={styles.btnRow}>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleMove(0, -1)}>
                  <Ionicons name="arrow-up" size={18} color={COLORS.textPrimary} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleMove(0, 1)}>
                  <Ionicons name="arrow-down" size={18} color={COLORS.textPrimary} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleMove(-1, 0)}>
                  <Ionicons name="arrow-back" size={18} color={COLORS.textPrimary} />
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleMove(1, 0)}>
                  <Ionicons name="arrow-forward" size={18} color={COLORS.textPrimary} />
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.controlGroup}>
              <Text style={styles.groupLabel}>Kích thước:</Text>
              <View style={styles.btnRow}>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleResize(0, 1)}>
                  <Ionicons name="resize" size={16} color={COLORS.textPrimary} />
                  <Text style={styles.btnSub}>+H</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleResize(0, -1)}>
                  <Ionicons name="remove" size={16} color={COLORS.textPrimary} />
                  <Text style={styles.btnSub}>-H</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleResize(1, 0)}>
                  <Ionicons name="add" size={16} color={COLORS.textPrimary} />
                  <Text style={styles.btnSub}>+W</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctrlBtn} onPress={() => handleResize(-1, 0)}>
                  <Ionicons name="remove" size={16} color={COLORS.textPrimary} />
                  <Text style={styles.btnSub}>-W</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>
      ) : (
        <View style={styles.noSelectCard}>
          <Text style={styles.noSelectText}>Chạm vào một khung chữ trên ảnh để chỉnh sửa.</Text>
        </View>
      )}

      {/* Global Actions */}
      <View style={styles.actionRow}>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={handleAddLine}
          accessibilityRole="button"
          accessibilityLabel="Thêm một khung dòng mới"
        >
          <Ionicons name="add-circle-outline" size={20} color={COLORS.primary} />
          <Text style={styles.secondaryBtnText}>Thêm dòng</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.primaryBtn, (processing || boxes.length === 0) && { opacity: 0.5 }]}
          onPress={handleConfirmLines}
          disabled={processing || boxes.length === 0}
          accessibilityRole="button"
          accessibilityLabel={`Xác nhận ${boxes.length} dòng chữ và nhận diện`}
        >
          {processing ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <>
              <Text style={styles.primaryBtnText}>Xác nhận ({boxes.length} dòng)</Text>
              <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
            </>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.medium,
    paddingTop: 52,
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: COLORS.background,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: SIZES.small,
  },
  backButton: {
    padding: 8,
  },
  resetButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: COLORS.surfaceSubdued,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  instruction: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: SIZES.small,
    lineHeight: 18,
  },
  imageContainer: {
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#F9FAFB',
    alignSelf: 'center',
    marginBottom: SIZES.medium,
    position: 'relative',
  },
  boxOverlay: {
    position: 'absolute',
    borderRadius: 4,
  },
  orderTag: {
    position: 'absolute',
    top: -10,
    left: -2,
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  orderTagText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
  },
  controlCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: SIZES.medium,
    marginBottom: SIZES.medium,
    borderWidth: 1,
    borderColor: COLORS.border,
    ...SHADOWS.small,
  },
  controlHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SIZES.small,
  },
  controlTitle: {
    fontSize: 14,
    color: COLORS.textPrimary,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    backgroundColor: '#FEE2E2',
  },
  deleteButtonText: {
    fontSize: 12,
    color: '#DC2626',
    fontWeight: '600',
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  controlGroup: {
    flex: 1,
  },
  groupLabel: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginBottom: 6,
  },
  btnRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  ctrlBtn: {
    width: 38,
    height: 38,
    borderRadius: 8,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 1,
    borderColor: '#BFDBFE',
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnSub: {
    fontSize: 8,
    color: COLORS.textSecondary,
    fontWeight: '700',
    marginTop: -2,
  },
  noSelectCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: COLORS.surfaceSubdued,
    alignItems: 'center',
    marginBottom: SIZES.medium,
  },
  noSelectText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  secondaryBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    height: 48,
    borderRadius: 12,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  secondaryBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primary,
  },
  primaryBtn: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    height: 48,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    ...SHADOWS.small,
  },
  primaryBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  emptyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 20,
    alignItems: 'center',
    marginBottom: SIZES.medium,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    ...SHADOWS.small,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 6,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 16,
    paddingHorizontal: 8,
  },
  emptyActions: {
    width: '100%',
    gap: 10,
  },
  emptyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    borderRadius: 10,
  },
  emptyBtnOutline: {
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  emptyBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

