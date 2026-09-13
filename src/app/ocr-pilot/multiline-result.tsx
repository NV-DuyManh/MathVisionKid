import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { OcrPilotService, MultilineTrialResult, MultilineLineResult } from '../../services/api/OcrPilotService';
import { logFlowDomain } from '../../services/draft/submissionDraftStore';

export default function MultilineResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const trialId = params.trialId as string;

  const [loading, setLoading] = useState(true);
  const [trial, setTrial] = useState<MultilineTrialResult | null>(null);
  const [editingLineId, setEditingLineId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [submittingLineId, setSubmittingLineId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const fetchTrial = async () => {
      if (!trialId) {
        Alert.alert('Lỗi', 'Không tìm thấy mã bài nhận diện.', [
          { text: 'Quay lại', onPress: () => router.replace('/(tabs)' as any) },
        ]);
        return;
      }
      try {
        const res = await OcrPilotService.getMultilineTrial(trialId);
        if (!active) return;
        logFlowDomain('RESULT', 'HANDWRITING_TEXT');
        setTrial(res);
      } catch (e: any) {
        if (!active) return;
        Alert.alert('Lỗi', e?.message || 'Không thể tải kết quả nhận diện.');
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchTrial();

    return () => {
      active = false;
    };
  }, [trialId, router]);

  const handleFeedback = async (
    line: MultilineLineResult,
    verdict: 'CORRECT' | 'CORRECTED' | 'SKIPPED',
    verifiedText?: string
  ) => {
    try {
      setSubmittingLineId(line.lineId);
      const updatedLine = await OcrPilotService.submitLineFeedback(
        trialId,
        line.lineId,
        verdict,
        verifiedText
      );

      // Update local state
      setTrial((prev) => {
        if (!prev) return prev;
        const updatedLines = prev.lines.map((l) =>
          l.lineId === line.lineId ? updatedLine : l
        );
        return { ...prev, lines: updatedLines };
      });

      if (verdict === 'CORRECTED') {
        setEditingLineId(null);
        setEditText('');
      }
    } catch (e: any) {
      Alert.alert('Lỗi phản hồi', e?.message || 'Không thể lưu phản hồi.');
    } finally {
      setSubmittingLineId(null);
    }
  };

  const startEditLine = (line: MultilineLineResult) => {
    setEditingLineId(line.lineId);
    setEditText(line.verifiedTextRaw || line.predictedText || '');
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Đang tải kết quả các dòng...</Text>
      </View>
    );
  }

  if (!trial) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Không thể hiển thị kết quả bài nhận diện.</Text>
        <TouchableOpacity style={styles.retryBtn} onPress={() => router.replace('/(tabs)' as any)}>
          <Text style={styles.retryBtnText}>Về trang chủ</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const joinedText = trial.lines.map((l) => l.predictedText).join('\n');

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.replace('/(tabs)' as any)}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="Về trang chủ"
        >
          <Ionicons name="home-outline" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Kết quả nhận diện nhiều dòng</Text>
        <View style={{ width: 32 }} />
      </View>

      {/* Combined Text Preview */}
      <View style={[styles.card, SHADOWS.small]}>
        <View style={styles.cardHeader}>
          <Ionicons name="document-text" size={20} color={COLORS.primary} />
          <Text style={styles.cardTitle}>Toàn bộ văn bản ghép lại ({trial.lines.length} dòng):</Text>
        </View>
        <View style={styles.joinedTextBox}>
          <Text style={styles.joinedText}>{joinedText || '(Chưa nhận diện được chữ nào)'}</Text>
        </View>
      </View>

      {/* Per-Line Feedback Section */}
      <Text style={styles.sectionTitle}>Xác nhận & sửa từng dòng chữ:</Text>
      <Text style={styles.sectionSubtitle}>
        Em hãy kiểm tra từng dòng dưới đây và sửa lại nếu AI đọc chưa chuẩn nhé:
      </Text>

      {trial.lines.map((line) => {
        const isEditing = editingLineId === line.lineId;
        const isSubmitting = submittingLineId === line.lineId;

        let badgeBg = '#FEF3C7';
        let badgeColor = '#D97706';
        let badgeText = 'Chưa xác nhận';

        if (line.verdict === 'CORRECT') {
          badgeBg = '#DCFCE7';
          badgeColor = '#16A34A';
          badgeText = 'Đúng ✓';
        } else if (line.verdict === 'CORRECTED') {
          badgeBg = '#DBEAFE';
          badgeColor = '#2563EB';
          badgeText = 'Đã sửa ✎';
        } else if (line.verdict === 'SKIPPED') {
          badgeBg = '#F1F5F9';
          badgeColor = '#64748B';
          badgeText = 'Đã bỏ qua';
        }

        return (
          <View key={line.lineId} style={[styles.lineCard, SHADOWS.small]}>
            <View style={styles.lineHeaderRow}>
              <View style={styles.lineOrderBadge}>
                <Text style={styles.lineOrderText}>Dòng {line.lineOrder}</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: badgeBg }]}>
                <Text style={[styles.badgeLabel, { color: badgeColor }]}>{badgeText}</Text>
              </View>
            </View>

            {/* Prediction text display - NO FAKE CONFIDENCE */}
            <View style={styles.predictBox}>
              <Text style={styles.predictLabel}>MathVision đọc được:</Text>
              <Text style={styles.predictText}>
                {line.predictedText ? `"${line.predictedText}"` : '(Không đọc được ký tự nào)'}
              </Text>
            </View>

            {/* Show verified text if corrected */}
            {line.verdict === 'CORRECTED' && line.verifiedTextRaw && !isEditing && (
              <View style={styles.correctedBox}>
                <Text style={styles.correctedLabel}>Chữ chuẩn của em:</Text>
                <Text style={styles.correctedText}>{`"${line.verifiedTextRaw}"`}</Text>
              </View>
            )}

            {/* Inline Editing Form */}
            {isEditing ? (
              <View style={styles.editForm}>
                <Text style={styles.editFormLabel}>Nhập chữ đúng của dòng này:</Text>
                <TextInput
                  style={styles.editInput}
                  value={editText}
                  onChangeText={setEditText}
                  placeholder="Nhập nội dung đúng..."
                  placeholderTextColor={COLORS.textMuted}
                  autoFocus
                />
                <View style={styles.editActionRow}>
                  <TouchableOpacity
                    style={styles.cancelEditBtn}
                    onPress={() => setEditingLineId(null)}
                  >
                    <Text style={styles.cancelEditBtnText}>Hủy</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.saveEditBtn, isSubmitting && { opacity: 0.6 }]}
                    disabled={isSubmitting}
                    onPress={() => handleFeedback(line, 'CORRECTED', editText)}
                  >
                    {isSubmitting ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <Text style={styles.saveEditBtnText}>Lưu & Xác nhận</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              /* Feedback Buttons */
              <View style={styles.feedbackRow}>
                <TouchableOpacity
                  style={[
                    styles.fbBtn,
                    styles.fbCorrectBtn,
                    line.verdict === 'CORRECT' && styles.fbBtnActive,
                  ]}
                  disabled={isSubmitting}
                  onPress={() => handleFeedback(line, 'CORRECT')}
                >
                  <Ionicons
                    name="checkmark-circle"
                    size={16}
                    color={line.verdict === 'CORRECT' ? '#FFFFFF' : '#16A34A'}
                  />
                  <Text
                    style={[
                      styles.fbBtnText,
                      { color: line.verdict === 'CORRECT' ? '#FFFFFF' : '#16A34A' },
                    ]}
                  >
                    Đúng
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[
                    styles.fbBtn,
                    styles.fbEditBtn,
                    line.verdict === 'CORRECTED' && styles.fbBtnActiveBlue,
                  ]}
                  disabled={isSubmitting}
                  onPress={() => startEditLine(line)}
                >
                  <Ionicons
                    name="pencil"
                    size={16}
                    color={line.verdict === 'CORRECTED' ? '#FFFFFF' : '#2563EB'}
                  />
                  <Text
                    style={[
                      styles.fbBtnText,
                      { color: line.verdict === 'CORRECTED' ? '#FFFFFF' : '#2563EB' },
                    ]}
                  >
                    Sửa
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.fbBtn, styles.fbSkipBtn]}
                  disabled={isSubmitting}
                  onPress={() => handleFeedback(line, 'SKIPPED')}
                >
                  <Ionicons name="close-circle-outline" size={16} color="#64748B" />
                  <Text style={[styles.fbBtnText, { color: '#64748B' }]}>Bỏ qua</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        );
      })}

      {__DEV__ && trial && (
        <View style={styles.devBox} testID="dev-diagnostic-panel">
          <Text style={styles.devTitle}>DEV Diagnostic (Multiline OCR)</Text>
          <Text style={styles.devText}>flowDomain: HANDWRITING_TEXT</Text>
          <Text style={styles.devText}>trialId: {trial.trialId}</Text>
          <Text style={styles.devText}>lineCount: {trial.lines.length}</Text>
          <Text style={styles.devText}>ocrInvoked: true</Text>
          <Text style={styles.devText}>recognizedTextLength: {joinedText.length}</Text>
          <Text style={styles.devText}>
            perLineStatus: {trial.lines.map((l) => `L${l.lineOrder}:${l.predictedText ? 'OK' : 'EMPTY'}`).join(', ')}
          </Text>
        </View>
      )}

      {/* Done Button */}
      <TouchableOpacity
        style={styles.doneBtn}
        onPress={() => router.replace('/(tabs)' as any)}
      >
        <Ionicons name="checkmark-done" size={20} color="#FFFFFF" />
        <Text style={styles.doneBtnText}>Nhận diện trang khác</Text>
      </TouchableOpacity>
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
  errorText: {
    fontSize: 15,
    color: COLORS.errorText,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryBtn: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    backgroundColor: COLORS.primary,
  },
  retryBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: SIZES.medium,
  },
  backButton: {
    padding: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: SIZES.medium,
    marginBottom: SIZES.large,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: SIZES.small,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  joinedTextBox: {
    backgroundColor: COLORS.surfaceSubdued,
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  joinedText: {
    fontSize: 15,
    lineHeight: 22,
    color: COLORS.textPrimary,
    fontFamily: 'System',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: SIZES.medium,
    lineHeight: 18,
  },
  lineCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: SIZES.medium,
    marginBottom: SIZES.medium,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  lineHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  lineOrderBadge: {
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: 6,
    backgroundColor: COLORS.primaryLight,
  },
  lineOrderText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  badge: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  badgeLabel: {
    fontSize: 11,
    fontWeight: '700',
  },
  predictBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  predictLabel: {
    fontSize: 11,
    color: COLORS.textMuted,
    marginBottom: 4,
  },
  predictText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  correctedBox: {
    backgroundColor: '#EFF6FF',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  correctedLabel: {
    fontSize: 11,
    color: COLORS.primary,
    marginBottom: 4,
  },
  correctedText: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.primaryDark,
  },
  editForm: {
    marginTop: 8,
    padding: 10,
    borderRadius: 10,
    backgroundColor: COLORS.surfaceSubdued,
  },
  editFormLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 6,
  },
  editInput: {
    height: 44,
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    paddingHorizontal: 12,
    fontSize: 14,
    color: COLORS.textPrimary,
    marginBottom: 10,
  },
  editActionRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
  },
  cancelEditBtn: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 6,
    backgroundColor: '#E2E8F0',
  },
  cancelEditBtnText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  saveEditBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    backgroundColor: COLORS.primary,
  },
  saveEditBtnText: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  feedbackRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 6,
  },
  fbBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    height: 38,
    borderRadius: 8,
    borderWidth: 1,
  },
  fbCorrectBtn: {
    borderColor: '#86EFAC',
    backgroundColor: '#F0FDF4',
  },
  fbEditBtn: {
    borderColor: '#93C5FD',
    backgroundColor: '#EFF6FF',
  },
  fbSkipBtn: {
    borderColor: '#CBD5E1',
    backgroundColor: '#F8FAFC',
  },
  fbBtnActive: {
    backgroundColor: '#16A34A',
    borderColor: '#16A34A',
  },
  fbBtnActiveBlue: {
    backgroundColor: '#2563EB',
    borderColor: '#2563EB',
  },
  fbBtnText: {
    fontSize: 13,
    fontWeight: '700',
  },
  doneBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    height: 50,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    marginTop: 12,
    marginBottom: 20,
    ...SHADOWS.small,
  },
  doneBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  devBox: {
    marginTop: SIZES.large,
    marginBottom: SIZES.small,
    padding: SIZES.medium,
    backgroundColor: '#1E293B',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  devTitle: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  devText: {
    color: '#94A3B8',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    lineHeight: 16,
  },
});
