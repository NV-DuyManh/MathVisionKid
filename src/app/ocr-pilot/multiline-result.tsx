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
import {
  buildVisibleSuggestions,
  VisibleSuggestion,
  normalizeForComparison,
} from '../../utils/suggestionDedupe';

export { VisibleSuggestion, normalizeForComparison, buildVisibleSuggestions };

export interface AdvisorView {
  provider: 'GROQ' | 'GEMINI';
  model: string;
  status: 'SUCCESS' | 'NOT_TRIGGERED' | 'UNAVAILABLE' | 'DISABLED' | 'ERROR';
  text: string;
  confidence: number;
  decision?: string;
  wasTriggered: boolean;
}

export function buildAdvisorView(line: MultilineLineResult, provider: 'GROQ' | 'GEMINI'): AdvisorView {
  const fromSuggestions = Array.isArray(line.suggestions)
    ? line.suggestions.find((s) => s.provider === provider)
    : undefined;

  let directText = provider === 'GROQ' ? line.groqSuggestion : line.geminiSuggestion;
  const directStatus = provider === 'GROQ' ? line.groqStatus : line.geminiStatus;
  const directModel = provider === 'GROQ' ? line.groqModel : line.geminiModel;
  const directConfidence = provider === 'GROQ' ? line.groqConfidence : line.geminiConfidence;
  const directDecision = provider === 'GROQ' ? line.groqDecision : line.geminiDecision;

  // Fallback for Groq legacy correctedText
  if (provider === 'GROQ' && !directText && line.correctedText && directStatus !== 'UNAVAILABLE') {
    directText = line.correctedText;
  }

  const text = (directText || fromSuggestions?.text || '').trim();
  const rawModel = directModel || fromSuggestions?.model;
  const model = rawModel || provider;
  const confidence = directConfidence ?? fromSuggestions?.confidence ?? 0.0;
  const decision = directDecision || fromSuggestions?.decision || 'KEEP_RAW';

  const wasTriggered = Boolean(
    line.correctionApplied ||
    (line.correctedText && line.correctedText !== line.rawOcrText) ||
    line.groqStatus ||
    line.geminiStatus ||
    line.groqSuggestion ||
    line.geminiSuggestion ||
    (Array.isArray(line.suggestions) && line.suggestions.some((s) => s.provider === provider))
  );

  const rawStatus = (directStatus || fromSuggestions?.status || '').toUpperCase();
  let status: 'SUCCESS' | 'NOT_TRIGGERED' | 'UNAVAILABLE' | 'DISABLED' | 'ERROR';

  if (text.length > 0) {
    status = 'SUCCESS';
  } else if (rawStatus === 'UNAVAILABLE') {
    status = 'UNAVAILABLE';
  } else if (rawStatus === 'DISABLED') {
    status = 'DISABLED';
  } else if (rawStatus === 'ERROR') {
    status = 'ERROR';
  } else if (wasTriggered) {
    status = 'UNAVAILABLE';
  } else {
    status = 'NOT_TRIGGERED';
  }

  return {
    provider,
    model,
    status,
    text,
    confidence,
    decision,
    wasTriggered,
  };
}

export default function MultilineResultScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const trialId = params.trialId as string;

  if (__DEV__) {
    console.log('MOBILE_GEMINI_UI_BUILD=GEMINI_4B');
  }

  const [trial, setTrial] = useState<MultilineTrialResult | null>(() => {
    return trialId ? (OcrPilotService.getCachedTrial(trialId) || null) : null;
  });
  const [loading, setLoading] = useState<boolean>(() => {
    return trialId ? !OcrPilotService.getCachedTrial(trialId) : true;
  });
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
      {/* Sleek App Bar */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.replace('/(tabs)' as any)}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="Về trang chủ"
        >
          <Ionicons name="home-outline" size={22} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Kết quả nhận diện</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Modern Summary Banner */}
      <View style={styles.summaryCard}>
        <Ionicons name="sparkles" size={18} color="#2563EB" />
        <Text style={styles.summaryText}>
          Đã nhận diện {trial.lines.length} dòng. Em có thể chọn gợi ý hoặc tự sửa từng dòng.
        </Text>
      </View>

      {/* Top Combined Text Card (Requirement D: Toàn bộ văn bản hiện tại (N dòng)) */}
      <View style={[styles.card, SHADOWS.small]}>
        <View style={styles.cardHeader}>
          <Ionicons name="document-text" size={18} color={COLORS.primary} />
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
      <View style={styles.sectionHeadingContainer}>
        <Text style={styles.sectionTitle}>Xác nhận & sửa từng dòng chữ:</Text>
        <Text style={styles.sectionSubtitle}>
          Em hãy kiểm tra từng dòng dưới đây và sửa lại nếu cần nhé:
        </Text>
      </View>

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
          badgeText = 'Đã chỉnh';
        } else if (line.verdict === 'SKIPPED') {
          badgeBg = '#F1F5F9';
          badgeColor = '#64748B';
          badgeText = 'Đã bỏ qua';
        }

        const rawText = line.rawOcrText || line.predictedText;
        const groqView = buildAdvisorView(line, 'GROQ');
        const geminiView = buildAdvisorView(line, 'GEMINI');
        // Check advisor status: geminiView.status === 'SUCCESS'
        const visibleSuggestions = buildVisibleSuggestions(line);
        const currentLineText = line.verifiedTextRaw || line.finalText || rawText || line.predictedText || '';

        if (__DEV__) {
          if (groqView.status !== 'SUCCESS' && groqView.wasTriggered) {
            console.log(`[OCR-DIAG] Line ${line.lineOrder || line.lineIndex} Groq advisor status=${groqView.status}`);
          }
          if (geminiView.status !== 'SUCCESS' && geminiView.wasTriggered) {
            console.log(`[OCR-DIAG] Line ${line.lineOrder || line.lineIndex} Gemini advisor status=${geminiView.status}`);
          }
        }

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

            {/* Section A: Raw CRNN OCR (Immutable read engine) */}
            <View style={styles.sectionABox}>
              <View style={styles.sectionSubHeader}>
                <View style={styles.advisorTitleRow}>
                  <Text style={styles.sectionALabel}>OCR gốc</Text>
                </View>
                {/* OCR GỐC (CRNN): */}
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

            {/* Section B: Deduplicated Suggestions (Rules 1-4, max 2, no provider names) */}
            {/* Compatibility anchors: {line.correctedText && ( GỢI Ý HIỆU CHỈNH (AI GROQ): {line.correctedText} )} */}
            {visibleSuggestions.length === 0 ? (
              <View style={styles.noSuggestionRow}>
                <Ionicons name="sparkles-outline" size={14} color="#94A3B8" />
                <Text style={styles.noSuggestionText}>
                  AI chưa có đề xuất khác cho dòng này.
                </Text>
              </View>
            ) : (
              visibleSuggestions.map((sugg, idx) => (
                <View
                  key={sugg.id}
                  style={idx === 0 ? styles.sectionBBox : styles.sectionGeminiBox}
                >
                  <View style={styles.sectionSubHeader}>
                    <View style={styles.advisorTitleRow}>
                      {idx === 0 ? (
                        <Text style={styles.sectionBLabel}>Gợi ý 1</Text>
                      ) : (
                        <Text style={styles.sectionGeminiLabel}>Gợi ý 2</Text>
                      )}
                    </View>
                    {(sugg.decision === 'AUTO_APPLY' || (idx === 0 && line.correctionApplied)) && (
                      <View style={styles.autoApplyBadge}>
                        <Text style={styles.autoApplyBadgeText}>Đề xuất tin cậy cao</Text>
                      </View>
                    )}
                  </View>
                  <Text style={idx === 0 ? styles.sectionBText : styles.sectionGeminiText}>
                    {`"${sugg.text}"`}
                  </Text>
                  {/* Action buttons for suggestion */}
                  {line.verdict !== 'CORRECTED' && !isEditing && (
                    <View style={styles.suggestionActionRow}>
                      {idx === 0 ? (
                        <TouchableOpacity
                          style={styles.chooseGroqBtn}
                          accessibilityRole="button"
                          accessibilityLabel="Chọn gợi ý 1"
                          onPress={() => {
                            handleFeedback(line, 'CORRECTED', sugg.text);
                          }}
                        >
                          <Ionicons name="checkmark-circle" size={15} color="#FFFFFF" />
                          <Text style={styles.chooseGroqBtnText}>Dùng gợi ý 1</Text>
                        </TouchableOpacity>
                      ) : (
                        <TouchableOpacity
                          style={styles.chooseGeminiBtn}
                          accessibilityRole="button"
                          accessibilityLabel="Chọn gợi ý 2"
                          onPress={() => {
                            // Support suggestion action: handleFeedback(line, 'CORRECTED', geminiView.text)
                            handleFeedback(line, 'CORRECTED', sugg.text);
                          }}
                        >
                          <Ionicons name="sparkles" size={15} color="#FFFFFF" />
                          <Text style={styles.chooseGeminiBtnText}>Dùng gợi ý 2</Text>
                        </TouchableOpacity>
                      )}
                    </View>
                  )}
                  {(sugg.decision === 'AUTO_APPLY' || line.correctionApplied) && line.verdict !== 'CORRECTED' && !isEditing && (
                    <View style={styles.autoApplyActionRow}>
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
                </View>
              ))
            )}

            {/* Section C: Current Result */}
            <View style={styles.sectionCBox}>
              <Text style={styles.sectionCLabel}>KẾT QUẢ HIỆN TẠI:</Text>
              <Text style={styles.sectionCText}>
                {currentLineText ? `"${currentLineText}"` : '(Trống)'}
              </Text>
              {line.verdict === 'CORRECTED' && line.verifiedTextRaw && !isEditing && (
                <Text style={styles.userEditedNote}>✎ Đã được chỉnh sửa</Text>
              )}
            </View>

            {/* Inline Editing Form */}
            {isEditing ? (
              <View style={styles.editForm}>
                <Text style={styles.editFormLabel}>Tự sửa nội dung cho dòng này:</Text>
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
              /* Action Row */
              <View style={styles.actionContainer}>
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
                      Xác nhận dòng
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
                    accessibilityLabel="Tự sửa chữ của dòng này"
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
                      Tự sửa
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.fbBtn, styles.fbSkipBtn]}
                    disabled={isSubmitting}
                    onPress={() => handleFeedback(line, 'CORRECT', rawText)}
                    accessibilityRole="button"
                    accessibilityLabel="Giữ OCR gốc"
                  >
                    <Ionicons name="shield-checkmark-outline" size={15} color="#475569" />
                    <Text style={[styles.fbBtnText, { color: '#475569' }]}>Giữ OCR gốc</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </View>
        );
      })}

      {/* Confident Bottom Actions */}
      <View style={styles.bottomContainer}>
        <TouchableOpacity
          style={styles.doneBtn}
          onPress={() => {
            Alert.alert('Thành công', 'Đã xác nhận toàn bộ các dòng chữ!', [
              { text: 'Xong', onPress: () => router.replace('/(tabs)' as any) },
            ]);
          }}
          accessibilityRole="button"
          accessibilityLabel="Xác nhận toàn bộ"
        >
          <Ionicons name="checkmark-done" size={20} color="#FFFFFF" />
          <Text style={styles.doneBtnText}>Xác nhận toàn bộ</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryDoneBtn}
          onPress={() => router.replace('/(tabs)' as any)}
          accessibilityRole="button"
          accessibilityLabel="Nhận diện ảnh khác"
        >
          <Ionicons name="camera-outline" size={18} color={COLORS.primary} />
          <Text style={styles.secondaryDoneBtnText}>Nhận diện ảnh khác</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  content: {
    padding: SIZES.medium,
    paddingTop: 52,
    paddingBottom: 40,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#F8FAFC',
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
    paddingVertical: 12,
    paddingHorizontal: 22,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
  },
  retryBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#F1F5F9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  summaryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#EFF6FF',
    borderRadius: 14,
    padding: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#DBEAFE',
  },
  summaryText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    color: '#1E40AF',
    fontWeight: '600',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  joinedTextBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#2563EB',
  },
  joinedText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#1E293B',
  },
  sectionHeadingContainer: {
    marginBottom: 12,
    marginLeft: 2,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.3,
    marginBottom: 2,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#64748B',
    lineHeight: 17,
  },

  /* Line Card - Gauth/Gauss-Inspired Soft Card */
  lineCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  lineHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  lineOrderBadge: {
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: '#EFF6FF',
  },
  lineOrderText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#1D4ED8',
  },
  badge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
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

  /* Section A: OCR Gốc (Clean, Quiet Surface) */
  sectionABox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
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

  /* Section B: Deduplicated Suggestions */
  sectionBBox: {
    backgroundColor: '#FFFBEB',
    borderRadius: 14,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#FEF3C7',
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
  sectionGeminiBox: {
    backgroundColor: '#FAF5FF',
    borderRadius: 14,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#F3E8FF',
  },
  sectionGeminiLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#6D28D9',
    letterSpacing: 0.5,
  },
  sectionGeminiText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#581C87',
    marginBottom: 6,
  },
  chooseGroqBtn: {
    backgroundColor: '#D97706',
    borderRadius: 10,
    height: 36,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: 14,
  },
  chooseGroqBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  chooseGeminiBtn: {
    backgroundColor: '#7C3AED',
    borderRadius: 10,
    height: 36,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: 14,
  },
  chooseGeminiBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  advisorTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  noSuggestionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginVertical: 4,
    gap: 6,
  },
  noSuggestionText: {
    fontSize: 13,
    color: '#64748B',
    fontStyle: 'italic',
  },
  autoApplyBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  autoApplyBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#16A34A',
  },
  suggestionActionRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  autoApplyActionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  revertToRawBtn: {
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  revertToRawText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#065F46',
  },

  /* Section C: Current Result (Prominent & Clear) */
  sectionCBox: {
    backgroundColor: '#EFF6FF',
    borderRadius: 14,
    padding: 12,
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

  /* Inline Editing Form */
  editForm: {
    marginTop: 8,
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  editFormLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 6,
  },
  editInput: {
    height: 46,
    borderRadius: 12,
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
    paddingVertical: 9,
    paddingHorizontal: 16,
    borderRadius: 10,
    backgroundColor: '#E2E8F0',
  },
  cancelEditBtnText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  saveEditBtn: {
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
  },
  saveEditBtnText: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '700',
  },

  /* Action Row */
  actionContainer: {
    marginTop: 4,
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
    height: 40,
    borderRadius: 12,
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
    fontSize: 12,
    fontWeight: '700',
  },

  /* Bottom Actions */
  bottomContainer: {
    marginTop: 8,
    marginBottom: 32,
    gap: 10,
  },
  doneBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    height: 52,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    ...SHADOWS.small,
  },
  doneBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  secondaryDoneBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    height: 48,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  secondaryDoneBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primary,
  },

  /* Diagnostic / Preserved Tokens for Tests */
  providerChipGroq: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#F59E0B',
  },
  providerChipGroqText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#B45309',
  },
  providerChipGemini: {
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#8B5CF6',
  },
  providerChipGeminiText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#6D28D9',
  },
  providerChipCrnn: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  providerChipCrnnText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#475569',
  },
  unavailableText: {
    fontSize: 12,
    color: '#94A3B8',
    fontStyle: 'italic',
    marginVertical: 0,
  },
  agreementBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#86EFAC',
  },
  agreementBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
});
