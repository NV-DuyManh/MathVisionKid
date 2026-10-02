import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, ActivityIndicator, Alert } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { RecognitionService, MultilineTrialResult, MultilineLineResult, normalizeOcrError } from '../../features/recognition/api/RecognitionService';
import { logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { buildVisibleSuggestions, buildAdvisorView, VisibleSuggestion, normalizeForComparison, getLineReviewStatus, resolveLineDisplayState } from '../../features/recognition/utils/lineReview';
import { isAdvisorPending, mergeTrialWithAdvisorUpdate } from '../../features/recognition/utils/advisorUpdates';
import { getRawOcrConfidence } from '../../features/recognition/utils/ocrConfidence';
import { recognitionAnalyticsStore } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { evaluateMathSolution, MathSolutionEvaluationResult } from '../../utils/mathSolutionEvaluator';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';
export function getDecisionExplanation(state: ReturnType<typeof resolveLineDisplayState>, line: MultilineLineResult): string {
    const src = (state.selectedSource || '').toUpperCase();
    const reason = state.selectionReason;
    if (src === 'MANUAL_EDIT' || src === 'MANUAL') {
        return 'Đã tự sửa bởi người dùng.';
    }
    if (src === 'SUGGESTION_1' || src === 'SUGGESTION_2') {
        if (reason === 'USER_EXPLICIT_SELECTION') {
            return 'Gợi ý AI được người dùng chọn.';
        }
        if (reason === 'MULTI_PROVIDER_CONSENSUS') {
            return 'Gợi ý AI được tự động chọn vì các mô hình AI độc lập cùng đồng thuận xác nhận lỗi chính tả.';
        }
        if (reason === 'GARBLED_OCR_DETERMINISTIC_CORRECTION') {
            return 'Gợi ý AI được tự động chọn vì OCR gốc chứa mẫu âm vị tiếng Việt không hợp lệ và từ sửa đổi đạt chuẩn từ điển.';
        }
        return 'Gợi ý AI được chọn theo độ tin cậy mô hình.';
    }
    // OCR
    if (state.isAiConfirmed) {
        return 'Giữ OCR gốc vì mô hình AI đã xác nhận nội dung trùng khớp chính xác.';
    }
    if (reason === 'USER_EXPLICIT_SELECTION') {
        return 'Giữ OCR gốc theo lựa chọn của người dùng.';
    }
    return 'Giữ OCR gốc vì độ tin cậy cao và không có đề xuất sửa đổi mạnh hơn.';
}
export { VisibleSuggestion, normalizeForComparison, buildVisibleSuggestions, getLineReviewStatus, resolveLineDisplayState, isAdvisorPending, mergeTrialWithAdvisorUpdate, };
export { buildAdvisorView, type AdvisorView } from '../../features/recognition/utils/lineReview';
export default function MultilineResultScreen() {
    const router = useRouter();
    const params = useLocalSearchParams();
    const trialId = params.trialId as string;
    if (__DEV__) {
        console.log('MOBILE_GEMINI_UI_BUILD=GEMINI_4B');
    }
    const [trial, setTrial] = useState<MultilineTrialResult | null>(() => {
        return trialId ? (RecognitionService.getCachedTrial(trialId) || null) : null;
    });
    const [loading, setLoading] = useState<boolean>(() => {
        return trialId ? !RecognitionService.getCachedTrial(trialId) : true;
    });
    const [editingLineId, setEditingLineId] = useState<string | null>(null);
    const [editText, setEditText] = useState('');
    const [submittingLineId, setSubmittingLineId] = useState<string | null>(null);
    useEffect(() => {
        let active = true;
        const fetchTrial = async () => {
            if (!trialId) {
                Alert.alert('Lỗi', 'Không tìm thấy mã bài nhận diện.', [
                    { text: 'Quay lại', onPress: () => router.replace('/(tabs)' as any) }
                ]);
                return;
            }
            try {
                const res = await RecognitionService.getMultilineTrial(trialId);
                if (!active)
                    return;
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
                {
                    const analytics = recognitionAnalyticsStore.computeTrialAnalytics(res, false);
                    recognitionAnalyticsStore.setCurrentTrialAnalytics(analytics);
                }
            }
            catch (e: any) {
                if (!active)
                    return;
                Alert.alert('Lỗi', e?.message || 'Không thể tải kết quả nhận diện.');
            }
            finally {
                if (active)
                    setLoading(false);
            }
        };
        fetchTrial();
        return () => {
            active = false;
        };
    }, [trialId, router]);
    const advisorPending = isAdvisorPending(trial);
    const mathSolutionEval: MathSolutionEvaluationResult | null = React.useMemo(() => {
        if (!trial?.lines || trial.lines.length === 0)
            return null;
        return evaluateMathSolution(trial.lines);
    }, [trial?.lines]);
    // Section 7: Async background advisor polling
    // Polls every 1000ms while advisors are pending, stops when complete/failed or after 8 polls.
    // Safely merges suggestions without overwriting user selections or manual edits.
    useEffect(() => {
        let mounted = true;
        if (!trialId || !trial)
            return;
        if (!advisorPending)
            return;
        let pollCount = 0;
        const maxPolls = 8;
        const pollIntervalMs = 1000;
        const timer = setInterval(async () => {
            if (!mounted)
                return;
            pollCount++;
            if (pollCount > maxPolls) {
                clearInterval(timer);
                return;
            }
            try {
                const fresh = await RecognitionService.getMultilineTrial(trialId);
                if (!mounted)
                    return;
                setTrial((prev) => {
                    if (!prev)
                        return fresh;
                    return mergeTrialWithAdvisorUpdate(prev, fresh, editingLineId);
                });
                if (!isAdvisorPending(fresh)) {
                    clearInterval(timer);
                }
            }
            catch (e) {
                console.warn('[MULTILINE_ASYNC_POLL] Background advisor poll check error:', e);
                if (pollCount >= maxPolls)
                    clearInterval(timer);
            }
        }, pollIntervalMs);
        return () => {
            mounted = false;
            clearInterval(timer);
        };
    }, [trialId, trial, advisorPending, editingLineId]);
    const handleFeedback = async (line: MultilineLineResult, verdict: 'CORRECT' | 'CORRECTED' | 'SKIPPED', verifiedText?: string) => {
        try {
            setSubmittingLineId(line.lineId);
            const targetText = verifiedText !== undefined
                ? verifiedText
                : (verdict === 'CORRECT' ? (line.finalText || line.rawOcrText || line.predictedText) : line.predictedText);
            const isTextDifferent = verifiedText !== undefined && verifiedText !== line.predictedText;
            const effectiveVerdict: 'CORRECT' | 'CORRECTED' | 'SKIPPED' = isTextDifferent ? 'CORRECTED' : verdict;
            const effectiveVerifiedText = effectiveVerdict === 'CORRECTED' ? (verifiedText || targetText) : undefined;
            // Immediate optimistic update of local state
            setTrial((prev) => {
                if (!prev)
                    return prev;
                const updatedLines = prev.lines.map((l) => {
                    if (l.lineId === line.lineId) {
                        return {
                            ...l,
                            verdict: effectiveVerdict,
                            verifiedTextRaw: verifiedText !== undefined ? verifiedText : (effectiveVerdict === 'CORRECT' ? (l.rawOcrText || l.predictedText) : l.verifiedTextRaw),
                            finalText: targetText,
                            predictedText: targetText,
                        };
                    }
                    return l;
                });
                return { ...prev, lines: updatedLines };
            });
            const updatedLine = await RecognitionService.submitLineFeedback(trialId, line.lineId, effectiveVerdict, effectiveVerifiedText);
            // Reconcile with server response
            setTrial((prev) => {
                if (!prev)
                    return prev;
                const updatedLines = prev.lines.map((l) => l.lineId === line.lineId
                    ? {
                        ...l,
                        ...updatedLine,
                        finalText: targetText,
                        predictedText: targetText,
                    }
                    : l);
                return { ...prev, lines: updatedLines };
            });
            if (effectiveVerdict === 'CORRECTED') {
                setEditingLineId(null);
                setEditText('');
            }
        }
        catch (e: any) {
            setTrial(prev => prev ? { ...prev, lines: prev.lines.map(current => current.lineId === line.lineId ? line : current) } : prev);
            Alert.alert('Chưa thể lưu phản hồi', normalizeOcrError(e).message);
        }
        finally {
            setSubmittingLineId(null);
        }
    };
    const startEditLine = (line: MultilineLineResult) => {
        setEditingLineId(line.lineId);
        setEditText(line.verifiedTextRaw || line.finalText || line.predictedText || '');
    };
    const handleFinish = async () => {
        try {
            const saved = await RecognitionService.getMultilineTrial(trialId);
            const pending = saved.lines.filter(line => !['CORRECT', 'CORRECTED', 'SKIPPED'].includes(line.verdict));
            if (pending.length > 0) {
                Alert.alert('Còn dòng cần kiểm tra', `Em hãy xác nhận hoặc sửa ${pending.length} dòng còn lại trước khi lưu bài.`);
                return;
            }
            await recognitionAnalyticsStore.completeTrial(saved);
            router.push({ pathname: '/recognition/trial-analytics', params: { trialId } });
        } catch (error) {
            Alert.alert('Chưa thể lưu bài', normalizeOcrError(error).message);
        }
    };
    if (loading) {
        return (<View style={styles.centerContainer}>
        <RecognitionProgress title="Đang mở kết quả" description="Bài nhận dạng của em sẽ hiện ngay khi tải xong." onCancel={() => router.back()} />
      </View>);
    }
    if (!trial) {
        return (<View style={styles.centerContainer}>
        <Text style={styles.errorText}>Không thể hiển thị kết quả bài nhận diện.</Text>
        <TouchableOpacity style={styles.retryBtn} onPress={() => router.replace('/(tabs)' as any)} accessibilityRole="button" accessibilityLabel="Về trang chủ">
          <Text style={styles.retryBtnText}>Về trang chủ</Text>
        </TouchableOpacity>
      </View>);
    }
    // Current full merged text strictly matching resolved per-line selections
    const currentMergedText = trial.lines
        .map((l) => resolveLineDisplayState(l).currentText)
        .join('\n');
    return (<ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Sleek App Bar */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.replace('/(tabs)' as any)} style={styles.backButton} accessibilityRole="button" accessibilityLabel={'Về trang chủ'}>
          <Ionicons name="home-outline" size={22} color={COLORS.textPrimary}/>
        </TouchableOpacity>
        <Text style={styles.title}>
          {'Kết quả nhận diện'}
        </Text>
        <View style={{ width: 40 }}/>
      </View>

      {/* Modern Summary Banner */}
      <View style={styles.summaryCard}>
        <Ionicons name="sparkles" size={18} color="#2563EB"/>
        <Text style={styles.summaryText}>
          {`Đã nhận diện ${trial.lines.length} dòng. Em có thể chọn gợi ý hoặc tự sửa từng dòng.`}
        </Text>
      </View>

      {/* Math Solution Holistic Evaluation Card */}
      {mathSolutionEval && mathSolutionEval.summary.totalLines > 0 && (<View style={[styles.mathSolutionCard, SHADOWS.small]}>
          <View style={styles.mathSolutionHeader}>
            <View style={styles.mathSolutionTitleRow}>
              <View style={[styles.mathVerdictIconBadge, { backgroundColor: mathSolutionEval.summary.badgeColor }]}>
                <Ionicons name={mathSolutionEval.summary.verdict === 'ALL_CORRECT'
                ? 'checkmark-done-circle'
                : mathSolutionEval.summary.verdict === 'HAS_CALCULATION_ERROR'
                    ? 'alert-circle'
                    : 'school'} size={22} color="#FFFFFF"/>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.mathSolutionTitleText}>{mathSolutionEval.summary.title}</Text>
                <Text style={styles.mathSolutionHintText}>{mathSolutionEval.summary.hint}</Text>
              </View>
            </View>
          </View>

          {/* Quick Metrics Bar: Lời giải | Phép tính | Đáp số */}
          <View style={styles.mathMetricsBar}>
            <View style={styles.mathMetricItem}>
              <Text style={styles.mathMetricValue}>{mathSolutionEval.summary.explanationCount}</Text>
              <Text style={styles.mathMetricLabel}>Dòng lời giải</Text>
            </View>
            <View style={styles.mathMetricDivider}/>
            <View style={styles.mathMetricItem}>
              <Text style={[
                styles.mathMetricValue,
                {
                    color: mathSolutionEval.summary.incorrectEquations > 0
                        ? '#DC2626'
                        : mathSolutionEval.summary.equationCount > 0
                            ? '#16A34A'
                            : COLORS.textPrimary,
                }
            ]}>
                {mathSolutionEval.summary.equationCount > 0
                ? `${mathSolutionEval.summary.correctEquations}/${mathSolutionEval.summary.equationCount}`
                : '0'}
              </Text>
              <Text style={styles.mathMetricLabel}>Phép tính đúng</Text>
            </View>
            <View style={styles.mathMetricDivider}/>
            <View style={styles.mathMetricItem}>
              <Text style={[styles.mathMetricValue, { color: mathSolutionEval.summary.hasAnswer ? '#7C3AED' : '#94A3B8' }]}>
                {mathSolutionEval.summary.hasAnswer ? 'Có ✓' : 'Chưa'}
              </Text>
              <Text style={styles.mathMetricLabel}>Đáp số</Text>
            </View>
          </View>

          {/* Multi-step logic chaining banner */}
          {mathSolutionEval.summary.multiStepChain?.isChained && (<View style={styles.mathChainBanner}>
              <Ionicons name="git-commit-outline" size={15} color="#2563EB"/>
              <Text style={styles.mathChainText}>
                {mathSolutionEval.summary.multiStepChain.chainDescription}
              </Text>
            </View>)}

          {/* Answer line validation feedback */}
          {mathSolutionEval.summary.answerValidation && mathSolutionEval.summary.hasAnswer && (<View style={[
                    styles.mathAnswerStatusRow,
                    mathSolutionEval.summary.answerValidation.status === 'PERFECT'
                        ? styles.mathAnswerStatusValid
                        : styles.mathAnswerStatusWarning
                ]}>
              <Ionicons name={mathSolutionEval.summary.answerValidation.status === 'PERFECT'
                    ? 'checkmark-circle'
                    : 'alert-circle'} size={15} color={mathSolutionEval.summary.answerValidation.status === 'PERFECT'
                    ? '#15803D'
                    : '#D97706'}/>
              <Text style={[
                    styles.mathAnswerStatusText,
                    {
                        color: mathSolutionEval.summary.answerValidation.status === 'PERFECT'
                            ? '#15803D'
                            : '#B45309',
                    }
                ]}>
                {mathSolutionEval.summary.answerValidation.message}
              </Text>
            </View>)}
        </View>)}

      {/* Top Combined Text Card (Requirement D: Toàn bộ văn bản hiện tại (N dòng)) */}
      <View style={[styles.card, SHADOWS.small]}>
        <View style={styles.cardHeader}>
          <Ionicons name="document-text" size={18} color={COLORS.primary}/>
          <Text style={styles.cardTitle}>
            {`Toàn bộ văn bản hiện tại (${trial.lines.length} dòng):`}
          </Text>
        </View>
        <View style={styles.joinedTextBox}>
          <Text style={styles.joinedText}>
            {currentMergedText || ('(Chưa nhận diện được chữ nào)')}
          </Text>
        </View>
      </View>

      {/* Per-Line Feedback Section */}
      <View style={styles.sectionHeadingContainer}>
        <Text style={styles.sectionTitle}>
          {'Xác nhận & sửa từng dòng chữ:'}
        </Text>
        <Text style={styles.sectionSubtitle}>
          {'Em hãy kiểm tra từng dòng dưới đây và sửa lại nếu cần nhé:'}
        </Text>
      </View>

      {trial.lines.map((line, lineIndex) => {
            const analyzedLine = mathSolutionEval?.lines[lineIndex];
            const isEditing = editingLineId === line.lineId;
            const isSubmitting = submittingLineId === line.lineId;
            let badgeBg = '#FEF3C7';
            let badgeColor = '#D97706';
            let badgeText = 'Chưa xác nhận';
            if (line.verdict === 'CORRECT') {
                badgeBg = '#DCFCE7';
                badgeColor = '#16A34A';
                badgeText = 'Đúng ✓';
            }
            else if (line.verdict === 'CORRECTED') {
                badgeBg = '#DBEAFE';
                badgeColor = '#2563EB';
                badgeText = 'Đã chỉnh';
            }
            else if (line.verdict === 'SKIPPED') {
                badgeBg = '#F1F5F9';
                badgeColor = '#64748B';
                badgeText = 'Đã bỏ qua';
            }
            const displayState = resolveLineDisplayState(line);
            const { ocrText, aiSuggestions, currentText, selectedSource, isAiConfirmed } = displayState;
            const rawText = line.rawOcrText || line.predictedText;
            const reviewStatus = getLineReviewStatus(line);
            const rawOcrConf = getRawOcrConfidence(line);
            const rawOcrConfText = rawOcrConf != null ? `${(rawOcrConf * 100).toFixed(0)}%` : null;
            // Smart Suggestion Logic for MathVision OCR (Phase 4):
            const firstCandidate = aiSuggestions[0];
            const normRaw = normalizeForComparison(ocrText);
            const hasCandidateText = Boolean(firstCandidate && firstCandidate.text && firstCandidate.text.trim().length > 0);
            const normCandidate = hasCandidateText ? normalizeForComparison(firstCandidate.text) : '';
            const isCandidateIdenticalToRaw = hasCandidateText && normCandidate === normRaw;
            const isCandidateDistinct = hasCandidateText && !isCandidateIdenticalToRaw;
            const hasAiConfirmedOcr = isAiConfirmed || isCandidateIdenticalToRaw;
            const sourceLabel = selectedSource === 'MANUAL_EDIT' || selectedSource === 'manual_edit'
                ? 'MANUAL'
                : selectedSource === 'SUGGESTION_1' || selectedSource === 'suggestion_1'
                    ? 'AI'
                    : 'OCR';
            // Required internal debug log (never toasted to student UI):
            console.log(`[LINE_RENDER_DEBUG] lineId=${line.lineId} lineOrder=${line.lineOrder} rawText="${rawText}" ` +
                `ocrText="${ocrText}" suggestions=[${aiSuggestions.map((s) => `"${s.text}"`).join(', ')}] ` +
                `selectedSource=${selectedSource} currentText="${currentText}" reviewStatus=${reviewStatus} isAiConfirmed=${isAiConfirmed}`);
            return (<View key={line.lineId} style={[styles.lineCard, SHADOWS.small]}>
            {/* Row Order, Confidence, and Verdict Badge */}
            <View style={styles.lineHeaderRow}>
              <View style={styles.lineOrderBadge}>
                <Text style={styles.lineOrderText}>
                  {`Dòng ${line.lineOrder}`}
                </Text>
              </View>
              <View style={styles.lineHeaderRight}>
                
                <View style={[styles.badge, { backgroundColor: badgeBg }]}>
                  <Text style={[styles.badgeLabel, { color: badgeColor }]}>{badgeText}</Text>
                </View>
              </View>
            </View>

            {/* Math Solution Line Role Badge */}
            {analyzedLine && (<View style={styles.mathRoleRow}>
                <View style={[styles.mathRoleBadge, { backgroundColor: analyzedLine.roleBadgeColor + '15', borderColor: analyzedLine.roleBadgeColor }]}>
                  <Text style={[styles.mathRoleBadgeText, { color: analyzedLine.roleBadgeColor }]}>
                    {analyzedLine.roleBadgeText}
                  </Text>
                </View>
              </View>)}

            {/* Arithmetic Calculation Assessment Box (If line is an equation) */}
            {analyzedLine?.equationValidation && (<View style={[
                        styles.mathEquationBox,
                        analyzedLine.equationValidation.isValid ? styles.mathEquationBoxValid : styles.mathEquationBoxInvalid
                    ]}>
                <View style={styles.mathEquationHeader}>
                  <Ionicons name={analyzedLine.equationValidation.isValid ? 'checkmark-circle' : 'close-circle'} size={16} color={analyzedLine.equationValidation.isValid ? '#15803D' : '#DC2626'}/>
                  <Text style={[
                        styles.mathEquationTitle,
                        { color: analyzedLine.equationValidation.isValid ? '#15803D' : '#DC2626' }
                    ]}>
                    {analyzedLine.equationValidation.isValid
                        ? 'Phép tính chính xác'
                        : 'Phép tính chưa chính xác'}
                  </Text>
                </View>
                {analyzedLine.equationValidation.isValid ? (<Text style={styles.mathEquationValidText}>
                    {analyzedLine.equationValidation.leftExpr} = {analyzedLine.equationValidation.expectedResult}
                    {analyzedLine.equationValidation.unit ? ` (${analyzedLine.equationValidation.unit})` : ''}
                  </Text>) : (<View style={styles.mathEquationErrorContainer}>
                    <Text style={styles.mathEquationErrorDetail}>
                      {analyzedLine.equationValidation.errorDetail}
                    </Text>
                    {analyzedLine.equationValidation.hint && (<Text style={styles.mathEquationHintText}>
                        💡 {analyzedLine.equationValidation.hint}
                      </Text>)}
                  </View>)}
              </View>)}

            {(
                /* Original MathVision Kids Content */
                <>
                {/* Section A: Raw CRNN OCR (Immutable read engine) */}
                <View style={styles.sectionABox}>
                  <View style={styles.sectionSubHeader}>
                    <View style={styles.advisorTitleRow}>
                      <Text style={styles.sectionALabel}>OCR gốc</Text>
                    </View>
                    {rawOcrConf != null && (<Text style={styles.confidenceBadge}>
                        Độ tin cậy: {(rawOcrConf! * 100).toFixed(0)}%
                      </Text>)}
                  </View>
                  <Text style={styles.sectionAText}>
                    {ocrText ? `"${ocrText}"` : '(Không nhận diện được ký tự nào)'}
                  </Text>
                </View>

                {/* Section B: Deduplicated Suggestions & Review Status */}
                {(() => {
                        const geminiView = buildAdvisorView(line, 'GEMINI');
                        return (aiSuggestions.length === 0 ? (reviewStatus === 'AI_CONFIRMED' ? (<View style={styles.aiConfirmedRow}>
                          <Ionicons name="checkmark-circle" size={16} color="#16A34A"/>
                          <Text style={styles.aiConfirmedText}>
                            AI xác nhận nội dung chính xác ✓
                          </Text>
                        </View>) : (<View style={styles.aiConfirmedRow}>
                          <Ionicons name="document-text-outline" size={16} color="#64748B"/>
                          <Text style={[styles.aiConfirmedText, { color: '#64748B' }]}>
                            Bản hiện tại (Chưa thể kiểm tra thêm lúc này.)
                          </Text>
                        </View>)) : (aiSuggestions.map((sugg, idx) => (<View key={sugg.id} style={idx === 0 ? styles.sectionBBox : styles.sectionGeminiBox}>
                          <View style={styles.sectionSubHeader}>
                            <View style={styles.advisorTitleRow}>
                              {idx === 0 ? (<Text style={styles.sectionBLabel}>Gợi ý 1</Text>) : (<Text style={styles.sectionGeminiLabel}>Gợi ý 2</Text>)}
                            </View>
                            {(sugg.decision === 'AUTO_APPLY' || (idx === 0 && line.correctionApplied)) && !sugg.isAiConfirmed && (<View style={styles.autoApplyBadge}>
                                <Text style={styles.autoApplyBadgeText}>
                                  {sugg.badge || (line.decisionReason === 'MULTI_PROVIDER_CONSENSUS' ? 'Đề xuất tin cậy cao' : 'Gợi ý AI')}
                                </Text>
                              </View>)}
                            {sugg.isAiConfirmed && (<View style={styles.aiConfirmedBadge}>
                                <Ionicons name="checkmark-circle" size={13} color="#16A34A"/>
                                <Text style={styles.aiConfirmedBadgeText}>AI xác nhận ✓</Text>
                              </View>)}
                          </View>
                          <Text style={idx === 0 ? styles.sectionBText : styles.sectionGeminiText}>
                            {`"${sugg.text}"`}
                          </Text>
                          {/* Action buttons for suggestion */}
                          {sugg.isAiConfirmed ? (<View style={styles.confirmedNoticeRow}>
                              <Ionicons name="checkmark-done" size={14} color="#16A34A"/>
                              <Text style={styles.confirmedNoticeText}>AI đã kiểm tra và xác nhận nội dung chính xác</Text>
                            </View>) : (line.verdict !== 'CORRECTED' && !isEditing && (<View style={styles.suggestionActionRow}>
                                {idx === 0 ? (<TouchableOpacity style={styles.chooseGroqBtn} accessibilityRole="button" accessibilityLabel="Chọn gợi ý 1" onPress={() => {
                                        handleFeedback(line, 'CORRECTED', sugg.text);
                                    }}>
                                    <Ionicons name="checkmark-circle" size={15} color="#FFFFFF"/>
                                    <Text style={styles.chooseGroqBtnText}>Dùng gợi ý 1</Text>
                                  </TouchableOpacity>) : ((geminiView.status === 'SUCCESS' || sugg.text) && (<TouchableOpacity style={styles.chooseGeminiBtn} accessibilityRole="button" accessibilityLabel="Chọn gợi ý 2" onPress={() => {
                                        handleFeedback(line, 'CORRECTED', geminiView.text);
                                    }}>
                                      <Ionicons name="sparkles" size={15} color="#FFFFFF"/>
                                      <Text style={styles.chooseGeminiBtnText}>Dùng gợi ý 2</Text>
                                    </TouchableOpacity>))}
                              </View>))}
                          {(sugg.decision === 'AUTO_APPLY' || line.correctionApplied) && line.verdict !== 'CORRECTED' && !isEditing && (<View style={styles.autoApplyActionRow}>
                              <TouchableOpacity style={styles.revertToRawBtn} accessibilityRole="button" accessibilityLabel="Quay về OCR gốc" onPress={() => handleFeedback(line, 'CORRECT', ocrText)}>
                                <Text style={styles.revertToRawText}>Quay về OCR gốc</Text>
                              </TouchableOpacity>
                            </View>)}
                        </View>))));
                    })()}

                {/* Section C: Current Result strictly from resolveLineDisplayState */}
                <View style={styles.sectionCBox}>
                  <View style={styles.sectionCHeaderRow}>
                    <Text style={styles.sectionCLabel}>KẾT QUẢ HIỆN TẠI:</Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <View style={[
                        styles.sourceBadge,
                        (selectedSource === 'MANUAL_EDIT' || selectedSource === 'manual_edit') && styles.sourceBadgeManual,
                        (selectedSource.toLowerCase().startsWith('suggestion')) && styles.sourceBadgeSuggestion,
                        (selectedSource === 'OCR' || selectedSource === 'ocr') && styles.sourceBadgeOcr
                    ]}>
                        <Text style={styles.sourceBadgeText}>
                          {selectedSource === 'MANUAL_EDIT' || selectedSource === 'manual_edit'
                        ? '✎ Đã tự sửa'
                        : selectedSource === 'SUGGESTION_1' || selectedSource === 'suggestion_1'
                            ? 'Gợi ý 1'
                            : selectedSource === 'SUGGESTION_2' || selectedSource === 'suggestion_2'
                                ? 'Gợi ý 2'
                                : 'OCR gốc'}
                        </Text>
                      </View>
                      {isAiConfirmed && (<View style={styles.aiConfirmedBadge}>
                          <Ionicons name="checkmark-circle" size={12} color="#16A34A"/>
                          <Text style={styles.aiConfirmedBadgeText}>AI xác nhận</Text>
                        </View>)}
                    </View>
                  </View>
                  <Text style={styles.sectionCText}>
                    {currentText ? `"${currentText}"` : '(Trống)'}
                  </Text>
                </View>

                {/* Inline Editing Form */}
                {isEditing ? (<View style={styles.editForm}>
                    <Text style={styles.editFormLabel}>Tự sửa nội dung cho dòng này:</Text>
                    <TextInput style={styles.editInput} value={editText} onChangeText={setEditText} placeholder="Nhập nội dung đúng..." placeholderTextColor={COLORS.textMuted} autoFocus/>
                    <View style={styles.editActionRow}>
                      <TouchableOpacity style={styles.cancelEditBtn} onPress={() => setEditingLineId(null)} accessibilityRole="button" accessibilityLabel="Hủy chỉnh sửa">
                        <Text style={styles.cancelEditBtnText}>Hủy</Text>
                      </TouchableOpacity>
                      <TouchableOpacity style={[styles.saveEditBtn, isSubmitting && { opacity: 0.6 }]} disabled={isSubmitting} onPress={() => handleFeedback(line, 'CORRECTED', editText)} accessibilityRole="button" accessibilityLabel="Lưu và xác nhận">
                        {isSubmitting ? (<ActivityIndicator size="small" color="#FFFFFF"/>) : (<Text style={styles.saveEditBtnText}>Lưu & Xác nhận</Text>)}
                      </TouchableOpacity>
                    </View>
                  </View>) : (
                    /* Action Row */
                    <View style={styles.actionContainer}>
                    <View style={styles.feedbackRow}>
                      <TouchableOpacity style={[
                            styles.fbBtn,
                            styles.fbCorrectBtn,
                            line.verdict === 'CORRECT' && styles.fbBtnActive
                        ]} disabled={isSubmitting} onPress={() => handleFeedback(line, 'CORRECT')} accessibilityRole="button" accessibilityLabel="Xác nhận dòng này đúng">
                        <Ionicons name="checkmark-circle" size={16} color={line.verdict === 'CORRECT' ? '#FFFFFF' : '#16A34A'}/>
                        <Text style={[
                            styles.fbBtnText,
                            { color: line.verdict === 'CORRECT' ? '#FFFFFF' : '#16A34A' }
                        ]}>
                          Xác nhận dòng
                        </Text>
                      </TouchableOpacity>

                      <TouchableOpacity style={[
                            styles.fbBtn,
                            styles.fbEditBtn,
                            line.verdict === 'CORRECTED' && styles.fbBtnActiveBlue
                        ]} disabled={isSubmitting} onPress={() => startEditLine(line)} accessibilityRole="button" accessibilityLabel="Tự sửa chữ của dòng này">
                        <Ionicons name="pencil" size={16} color={line.verdict === 'CORRECTED' ? '#FFFFFF' : '#2563EB'}/>
                        <Text style={[
                            styles.fbBtnText,
                            { color: line.verdict === 'CORRECTED' ? '#FFFFFF' : '#2563EB' }
                        ]}>
                          Tự sửa
                        </Text>
                      </TouchableOpacity>

                      <TouchableOpacity style={[styles.fbBtn, styles.fbSkipBtn]} disabled={isSubmitting} onPress={() => handleFeedback(line, 'CORRECT', ocrText)} accessibilityRole="button" accessibilityLabel="Giữ OCR gốc">
                        <Ionicons name="shield-checkmark-outline" size={15} color="#475569"/>
                        <Text style={[styles.fbBtnText, { color: '#475569' }]}>Giữ OCR gốc</Text>
                      </TouchableOpacity>
                    </View>
                  </View>)}
              </>)}
          </View>);
        })}

      {/* Confident Bottom Actions */}
      <View style={styles.bottomContainer}>
        <TouchableOpacity style={styles.doneBtn} onPress={handleFinish} disabled={submittingLineId !== null} accessibilityRole="button" accessibilityLabel="Hoàn tất kiểm tra">
          <Ionicons name="checkmark-done" size={20} color="#FFFFFF"/>
          <Text style={styles.doneBtnText}>
            Hoàn tất kiểm tra
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.analyticsBtn} onPress={() => router.push('/recognition/analytics')} accessibilityRole="button" accessibilityLabel="Xem lịch sử nhận dạng">
          <Ionicons name="stats-chart" size={18} color={COLORS.surface} />
          <Text style={styles.analyticsBtnText}>Lịch sử nhận dạng</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.secondaryDoneBtn} onPress={() => router.replace('/(tabs)' as any)} accessibilityRole="button" accessibilityLabel={'Nhận diện ảnh khác'}>
          <Ionicons name="camera-outline" size={18} color={COLORS.primary}/>
          <Text style={styles.secondaryDoneBtnText}>
            {'Nhận diện ảnh khác'}
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>);
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
    aiConfirmedRow: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#F0FDF4',
        borderRadius: 12,
        paddingHorizontal: 12,
        paddingVertical: 9,
        marginVertical: 4,
        gap: 8,
        borderWidth: 1,
        borderColor: '#DCFCE7',
    },
    aiConfirmedText: {
        fontSize: 13,
        fontWeight: '600',
        color: '#15803D',
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
    sectionCHeaderRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 6,
    },
    sectionCLabel: {
        fontSize: 11,
        fontWeight: '700',
        color: '#1D4ED8',
        letterSpacing: 0.5,
    },
    sourceBadge: {
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 6,
        backgroundColor: '#DBEAFE',
    },
    sourceBadgeManual: {
        backgroundColor: '#EDE9FE',
    },
    sourceBadgeSuggestion: {
        backgroundColor: '#DCFCE7',
    },
    sourceBadgeOcr: {
        backgroundColor: '#F1F5F9',
    },
    sourceBadgeText: {
        fontSize: 10,
        fontWeight: '700',
        color: '#1E40AF',
    },
    sectionCText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#1E3A8A',
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
    analyticsBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        height: 48,
        borderRadius: 8,
        backgroundColor: '#123B7A',
        ...SHADOWS.small,
    },
    analyticsBtnText: {
        fontSize: 14,
        fontWeight: '700',
        color: '#FFFFFF',
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
    aiConfirmedBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#DCFCE7',
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: '#86EFAC',
        gap: 4,
    },
    aiConfirmedBadgeText: {
        fontSize: 11,
        fontWeight: '700',
        color: '#15803D',
    },
    confirmedNoticeRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginTop: 6,
        paddingTop: 4,
    },
    confirmedNoticeText: {
        fontSize: 12,
        color: '#15803D',
        fontWeight: '500',
    },
    lineHeaderRight: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    // Math Solution Grading Styles
    mathSolutionCard: {
        backgroundColor: '#FFFFFF',
        borderRadius: 14,
        padding: SIZES.medium,
        marginBottom: SIZES.medium,
        borderWidth: 1,
        borderColor: '#E2E8F0',
    },
    mathSolutionHeader: {
        marginBottom: SIZES.small,
    },
    mathSolutionTitleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    mathVerdictIconBadge: {
        width: 40,
        height: 40,
        borderRadius: 20,
        alignItems: 'center',
        justifyContent: 'center',
    },
    mathSolutionTitleText: {
        fontSize: 16,
        fontWeight: '700',
        color: COLORS.textPrimary,
    },
    mathSolutionHintText: {
        fontSize: 13,
        color: COLORS.textSecondary,
        marginTop: 2,
        lineHeight: 18,
    },
    mathMetricsBar: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-around',
        backgroundColor: '#F8FAFC',
        borderRadius: 10,
        paddingVertical: 10,
        marginTop: 8,
        borderWidth: 1,
        borderColor: '#E2E8F0',
    },
    mathMetricItem: {
        alignItems: 'center',
        flex: 1,
    },
    mathMetricValue: {
        fontSize: 16,
        fontWeight: '800',
        color: COLORS.textPrimary,
    },
    mathMetricLabel: {
        fontSize: 11,
        color: '#64748B',
        marginTop: 2,
        fontWeight: '600',
    },
    mathMetricDivider: {
        width: 1,
        height: 24,
        backgroundColor: '#CBD5E1',
    },
    mathRoleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    mathRoleBadge: {
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 6,
        borderWidth: 1,
    },
    mathRoleBadgeText: {
        fontSize: 11,
        fontWeight: '700',
    },
    mathEquationBox: {
        borderRadius: 8,
        padding: 10,
        marginBottom: 10,
        borderWidth: 1,
    },
    mathEquationBoxValid: {
        backgroundColor: '#F0FDF4',
        borderColor: '#86EFAC',
    },
    mathEquationBoxInvalid: {
        backgroundColor: '#FEF2F2',
        borderColor: '#FECACA',
    },
    mathEquationHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 4,
    },
    mathEquationTitle: {
        fontSize: 13,
        fontWeight: '700',
    },
    mathEquationValidText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#166534',
        paddingLeft: 22,
    },
    mathEquationErrorContainer: {
        paddingLeft: 22,
        gap: 3,
    },
    mathEquationErrorDetail: {
        fontSize: 13,
        fontWeight: '600',
        color: '#991B1B',
    },
    mathEquationHintText: {
        fontSize: 12,
        color: '#B45309',
        lineHeight: 16,
        fontWeight: '500',
    },
    mathChainBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        backgroundColor: '#EFF6FF',
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 8,
        marginTop: 10,
        borderWidth: 1,
        borderColor: '#BFDBFE',
    },
    mathChainText: {
        flex: 1,
        fontSize: 12,
        color: '#1D4ED8',
        fontWeight: '600',
        lineHeight: 16,
    },
    mathAnswerStatusRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 8,
        marginTop: 8,
        borderWidth: 1,
    },
    mathAnswerStatusValid: {
        backgroundColor: '#F0FDF4',
        borderColor: '#86EFAC',
    },
    mathAnswerStatusWarning: {
        backgroundColor: '#FFFBEB',
        borderColor: '#FDE68A',
    },
    mathAnswerStatusText: {
        flex: 1,
        fontSize: 12,
        fontWeight: '600',
        lineHeight: 16,
    },
});
