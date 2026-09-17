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
        console.log('[OCR-PHYSICAL] Loaded trial:', {
          trialId: res.trialId,
          recognitionEngine: res.recognitionEngine,
          segmentationSource: res.segmentationSource,
          correctionSource: res.correctionSource,
          finalTextSource: res.finalTextSource,
          linesCount: res.lines?.length,
          requestId: res.requestId,
        });
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

      const targetText = verifiedText !== undefined
        ? verifiedText
        : (verdict === 'CORRECT' ? (line.finalText || line.rawOcrText || line.predictedText) : line.predictedText);

      // Immediate optimistic update of local state
      setTrial((prev) => {
        if (!prev) return prev;
        const updatedLines = prev.lines.map((l) => {
          if (l.lineId === line.lineId) {
            return {
              ...l,
              verdict,
              verifiedTextRaw: verifiedText !== undefined ? verifiedText : (verdict === 'CORRECT' ? (l.rawOcrText || l.predictedText) : l.verifiedTextRaw),
              finalText: targetText,
              predictedText: targetText,
            };
          }
          return l;
        });
        return { ...prev, lines: updatedLines };
      });

      const updatedLine = await OcrPilotService.submitLineFeedback(
        trialId,
        line.lineId,
        verdict,
        verifiedText
      );

      // Reconcile with server response
      setTrial((prev) => {
        if (!prev) return prev;
        const updatedLines = prev.lines.map((l) =>
          l.lineId === line.lineId
            ? {
                ...l,
                ...updatedLine,
                finalText: targetText,
                predictedText: targetText,
              }
            : l
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
    setEditText(line.verifiedTextRaw || line.finalText || line.predictedText || '');
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
        <TouchableOpacity
          style={styles.retryBtn}
          onPress={() => router.replace('/(tabs)' as any)}
          accessibilityRole="button"
          accessibilityLabel="Về trang chủ"
        >
          <Text style={styles.retryBtnText}>Về trang chủ</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Current full merged text (Requirement D)
  const currentMergedText = trial.lines
    .map((l) => l.verifiedTextRaw || l.finalText || (l.correctionApplied ? l.correctedText : l.rawOcrText) || l.predictedText || '')
    .join('\n');

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

      {/* Top Combined Text Card (Requirement D: Toàn bộ văn bản hiện tại (N dòng)) */}
      <View style={[styles.card, SHADOWS.small]}>
        <View style={styles.cardHeader}>
          <Ionicons name="document-text" size={20} color={COLORS.primary} />
          <Text style={styles.cardTitle}>
            Toàn bộ văn bản hiện tại ({trial.lines.length} dòng):
          </Text>
        </View>
        <View style={styles.joinedTextBox}>
          <Text style={styles.joinedText}>
            {currentMergedText || '(Chưa nhận diện được chữ nào)'}
          </Text>
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

        const rawText = line.rawOcrText || line.predictedText;
        const currentLineText = line.verifiedTextRaw || line.finalText || (line.correctionApplied ? line.correctedText : rawText) || line.predictedText;

        return (
          <View key={line.lineId} style={[styles.lineCard, SHADOWS.small]}>
            {/* Row Order and Verdict Badge */}
            <View style={styles.lineHeaderRow}>
              <View style={styles.lineOrderBadge}>
                <Text style={styles.lineOrderText}>Dòng {line.lineOrder}</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: badgeBg }]}>
                <Text style={[styles.badgeLabel, { color: badgeColor }]}>{badgeText}</Text>
              </View>
            </View>

            {/* Section A: Raw CRNN OCR (Requirement B) */}
            <View style={styles.sectionABox}>
              <View style={styles.sectionSubHeader}>
                <Text style={styles.sectionALabel}>OCR GỐC (CRNN):</Text>
                {line.rawOcrConfidence != null && (
                  <Text style={styles.confidenceBadge}>
                    Độ tin cậy: {(line.rawOcrConfidence * 100).toFixed(0)}%
                  </Text>
                )}
              </View>
              <Text style={styles.sectionAText}>
                {rawText ? `"${rawText}"` : '(Không nhận diện được ký tự nào)'}
              </Text>
            </View>

            {/* Section B: Groq Suggestion (Requirement B) */}
            {line.correctedText && (
              <View style={styles.sectionBBox}>
                <View style={styles.sectionSubHeader}>
                  <Text style={styles.sectionBLabel}>GỢI Ý HIỆU CHỈNH (AI GROQ):</Text>
                  {line.correctionDecision === 'AUTO_APPLY' || line.correctionApplied ? (
                    <View style={styles.autoApplyBadge}>
                      <Text style={styles.autoApplyBadgeText}>Đề xuất tin cậy cao</Text>
                    </View>
                  ) : line.correctionDecision === 'SUGGEST_ONLY' ? (
                    <View style={styles.suggestOnlyBadge}>
                      <Text style={styles.suggestOnlyBadgeText}>Cần bạn xác nhận</Text>
                    </View>
                  ) : (
                    <View style={styles.keepRawBadge}>
                      <Text style={styles.keepRawBadgeText}>Không đủ chắc chắn</Text>
                    </View>
                  )}
                </View>

                {line.correctionDecision === 'KEEP_RAW' ? (
                  <Text style={styles.keepRawNote}>
                    AI gợi ý giữ nguyên OCR gốc vì chưa đủ độ tin cậy để sửa.
                  </Text>
                ) : (
                  <>
                    <Text style={styles.sectionBText}>{`"${line.correctedText}"`}</Text>
                    {/* Action buttons for suggestion */}
                    {line.correctionDecision === 'SUGGEST_ONLY' && line.verdict !== 'CORRECTED' && !isEditing && (
                      <View style={styles.suggestionActionRow}>
                        <TouchableOpacity
                          style={styles.acceptSuggBtn}
                          accessibilityRole="button"
                          accessibilityLabel="Chấp nhận gợi ý của AI"
                          onPress={() => handleFeedback(line, 'CORRECTED', line.correctedText)}
                        >
                          <Ionicons name="checkmark-circle" size={16} color="#FFFFFF" />
                          <Text style={styles.acceptSuggText}>Chấp nhận gợi ý</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={styles.keepRawBtn}
                          accessibilityRole="button"
                          accessibilityLabel="Giữ OCR gốc"
                          onPress={() => handleFeedback(line, 'CORRECT', rawText)}
                        >
                          <Ionicons name="shield-checkmark-outline" size={16} color={COLORS.textSecondary} />
                          <Text style={styles.keepRawText}>Giữ OCR gốc</Text>
                        </TouchableOpacity>
                      </View>
                    )}
                    {/* If AUTO_APPLIED, allow revert to raw */}
                    {(line.correctionDecision === 'AUTO_APPLY' || line.correctionApplied) && line.verdict !== 'CORRECTED' && !isEditing && (
                      <View style={styles.autoApplyActionRow}>
                        <Text style={styles.autoApplyInfoText}>Đã tự động áp dụng gợi ý này.</Text>
                        <TouchableOpacity
                          style={styles.revertToRawBtn}
                          accessibilityRole="button"
                          accessibilityLabel="Quay về OCR gốc"
                          onPress={() => handleFeedback(line, 'CORRECT', rawText)}
                        >
                          <Text style={styles.revertToRawText}>Quay về OCR gốc</Text>
                        </TouchableOpacity>
                      </View>
                    )}
                  </>
                )}
              </View>
            )}

            {/* Section C: Current Result (Requirement B) */}
            <View style={styles.sectionCBox}>
              <Text style={styles.sectionCLabel}>KẾT QUẢ HIỆN TẠI:</Text>
              <Text style={styles.sectionCText}>
                {currentLineText ? `"${currentLineText}"` : '(Trống)'}
              </Text>
              {line.verdict === 'CORRECTED' && line.verifiedTextRaw && !isEditing && (
                <Text style={styles.userEditedNote}>✎ Đã được bạn chỉnh sửa</Text>
              )}
            </View>

            {/* Inline Editing Form */}
            {isEditing ? (
              <View style={styles.editForm}>
                <Text style={styles.editFormLabel}>Nhập nội dung đúng cho dòng này:</Text>
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
                    accessibilityRole="button"
                    accessibilityLabel="Hủy chỉnh sửa"
                  >
                    <Text style={styles.cancelEditBtnText}>Hủy</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.saveEditBtn, isSubmitting && { opacity: 0.6 }]}
                    disabled={isSubmitting}
                    onPress={() => handleFeedback(line, 'CORRECTED', editText)}
                    accessibilityRole="button"
                    accessibilityLabel="Lưu và xác nhận"
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
              /* Feedback Action Row */
              <View style={styles.feedbackRow}>
                <TouchableOpacity
                  style={[
                    styles.fbBtn,
                    styles.fbCorrectBtn,
                    line.verdict === 'CORRECT' && styles.fbBtnActive,
                  ]}
                  disabled={isSubmitting}
                  onPress={() => handleFeedback(line, 'CORRECT')}
                  accessibilityRole="button"
                  accessibilityLabel="Xác nhận dòng này đúng"
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
                  accessibilityRole="button"
                  accessibilityLabel="Sửa chữ của dòng này"
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
                  accessibilityRole="button"
                  accessibilityLabel="Bỏ qua dòng này"
                >
                  <Ionicons name="close-circle-outline" size={16} color="#64748B" />
                  <Text style={[styles.fbBtnText, { color: '#64748B' }]}>Bỏ qua</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        );
      })}

      {/* Done Button */}
      <TouchableOpacity
        style={styles.doneBtn}
        onPress={() => router.replace('/(tabs)' as any)}
        accessibilityRole="button"
        accessibilityLabel="Nhận diện trang khác"
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
    marginBottom: 12,
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
  sectionSubHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  sectionABox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  sectionALabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    letterSpacing: 0.5,
  },
  confidenceBadge: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '600',
  },
  sectionAText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
  },
  sectionBBox: {
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  sectionBLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#92400E',
    letterSpacing: 0.5,
  },
  sectionBText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#78350F',
    marginBottom: 8,
  },
  autoApplyBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  autoApplyBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#16A34A',
  },
  suggestOnlyBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#F59E0B',
  },
  suggestOnlyBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#B45309',
  },
  keepRawBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  keepRawBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
  },
  keepRawNote: {
    fontSize: 12,
    color: '#64748B',
    fontStyle: 'italic',
    marginTop: 2,
  },
  suggestionActionRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  acceptSuggBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    height: 36,
    borderRadius: 6,
    backgroundColor: '#16A34A',
  },
  acceptSuggText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  keepRawBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    height: 36,
    borderRadius: 6,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  keepRawText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  autoApplyActionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  autoApplyInfoText: {
    fontSize: 12,
    color: '#065F46',
    fontWeight: '600',
  },
  revertToRawBtn: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  revertToRawText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#065F46',
  },
  sectionCBox: {
    backgroundColor: '#EFF6FF',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
    borderWidth: 1.5,
    borderColor: '#93C5FD',
  },
  sectionCLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#1D4ED8',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  sectionCText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1E3A8A',
  },
  userEditedNote: {
    fontSize: 11,
    color: '#2563EB',
    fontWeight: '600',
    marginTop: 4,
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
    marginTop: 4,
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
});
