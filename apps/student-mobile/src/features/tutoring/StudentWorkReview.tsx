import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import type { TextInputInstance } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { NotebookLine, TutorService, WorkReview, trimWorkReviewLine, workReviewLines } from './api/TutorService';
import { WorkPhotoEvidence } from './WorkPhotoEvidence';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { QuizAfterLearningButton } from '../quiz/QuizInvitation';
import { analyzeRowPresentation, checkIncompleteWork, isWorkReviewIssue } from './workReviewAnalysis';
import { CorrectAnswerFeedback } from './CorrectAnswerFeedback';
import { WorkLineInput } from './WorkLineInput';

type Props = {
  problemText: string;
  workText: string;
  imageUri: string;
  lines: NotebookLine[];
  enabled: boolean;
  disabled?: boolean;
  photoCurrent?: boolean;
  autoStart?: boolean;
  onReviseWork: (work: string) => void;
  onCaptureWork: () => void;
  onSessionExpired?: () => void;
  onReviewReady?: () => void;
};

export function StudentWorkReview(props: Props) {
  // A response belongs to exactly one source, including the privacy-approved photo and its physical regions.
  return <ReviewSession key={JSON.stringify([props.problemText, props.workText, props.imageUri, props.lines, props.enabled, props.disabled, props.photoCurrent])} {...props} />;
}

function ReviewSession({
  problemText,
  workText,
  imageUri,
  lines,
  enabled,
  disabled = false,
  photoCurrent = true,
  autoStart = false,
  onReviseWork,
  onCaptureWork,
  onSessionExpired,
  onReviewReady,
}: Props) {
  const router = useRouter();
  const [result, setResult] = useState<WorkReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [expired, setExpired] = useState(false);
  const [error, setError] = useState('');
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [hintCount, setHintCount] = useState(0);
  const [showAlternative, setShowAlternative] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [rewrite, setRewrite] = useState<Record<number, string> | null>(null);
  const [focused, setFocused] = useState(false);
  const [sessionFocused, setSessionFocused] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const active = useRef(false);
  const sequence = useRef(0);
  const autoStarted = useRef(false);
  const rewriteInput = useRef<TextInputInstance>(null);
  const rewriteId = useId();
  const alternativeId = useId();
  const disabledNow = disabled || !enabled || expired;

  const stop = useCallback(() => {
    sequence.current += 1;
    controller.current?.abort();
    controller.current = null;
    setBusy(false);
  }, []);

  useFocusEffect(useCallback(() => {
    active.current = true;
    setSessionFocused(true);
    return () => {
      active.current = false;
      setSessionFocused(false);
      sequence.current += 1;
      controller.current?.abort();
      controller.current = null;
      setBusy(false);
    };
  }, []));

  const editingRewrite = rewrite !== null;
  useEffect(() => {
    if (editingRewrite) rewriteInput.current?.focus();
  }, [editingRewrite]);

  const review = useCallback(async () => {
    if (disabledNow || controller.current) return;
    const abort = new AbortController();
    controller.current = abort;
    const id = ++sequence.current;
    const sourceId = `work_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
    setBusy(true);
    setError('');
    setRewrite(null);
    setShowAlternative(false);
    setHintCount(0);
    try {
      const next = await TutorService.reviewWork({ sourceId, problemText, workText, problemConfirmed: true, workConfirmed: true }, abort.signal);
      if (!active.current || abort.signal.aborted || sequence.current !== id) return;
      setResult(next);
      setShowDetails(next.status !== 'CORRECT');
      onReviewReady?.();
      const firstIssue = next.rows.find(isWorkReviewIssue);
      setSelectedLine(firstIssue?.lineIndex ?? null);
    } catch (failure: any) {
      if (!active.current || abort.signal.aborted || sequence.current !== id) return;
      if (failure?.response?.status === 401) {
        setExpired(true);
        onSessionExpired?.();
        setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.');
      } else if ([400, 422].includes(failure?.response?.status)) {
        setError('Có chỗ trong đề hoặc bài làm chưa rõ. Em xem lại đề và bài làm rồi thử lại nhé.');
      } else if (failure?.response?.status === 429 || failure?.response?.data?.error?.code === 'TUTOR_RATE_LIMITED') {
        setError('Mình cần chờ một chút trước khi nhận xét tiếp. Đề và bài làm vẫn được giữ; em thử lại sau nhé.');
      } else {
        setError('Chưa nhận xét được lúc này. Đề và bài làm vẫn ở đây; em thử lại nhé.');
      }
    } finally {
      if (active.current && sequence.current === id) {
        controller.current = null;
        setBusy(false);
      }
    }
  }, [disabledNow, problemText, workText, onReviewReady, onSessionExpired]);

  useEffect(() => {
    if (!autoStart || !sessionFocused || disabledNow || autoStarted.current) return;
    let current = true;
    void Promise.resolve().then(() => {
      if (!current || !active.current || autoStarted.current) return;
      autoStarted.current = true;
      void review();
    });
    return () => { current = false; };
  }, [autoStart, sessionFocused, disabledNow, review]);

  const selected = result?.rows.find(row => row.lineIndex === selectedLine);
  const editRows = result?.rows.filter(isWorkReviewIssue) ?? [];
  const hasCorrections = editRows.length > 0;
  const multipleEdits = editRows.length > 1;
  const sourceLines = workReviewLines(workText);
  const revisedWork = rewrite && sourceLines.map((line, index) => index in rewrite ? trimWorkReviewLine(rewrite[index]) : line).join('\n');
  const canSave = !!(revisedWork && revisedWork.length <= 6000 && editRows.every(row => {
    const value = rewrite?.[row.lineIndex] ?? '';
    const trimmed = trimWorkReviewLine(value);
    return trimmed && trimmed !== row.sourceText && value.length <= 500 && !value.includes('[?]')
      && !/[\r\n\v\f\x1c-\x1e\x85\u2028\u2029]/.test(value);
  }));

  const choose = (index: number) => {
    setSelectedLine(index);
    setHintCount(0);
  };

  const applyRewrite = () => {
    if (!disabledNow && !busy && canSave && revisedWork) onReviseWork(revisedWork);
  };

  // Analyze whether the work is incomplete (missing subsequent steps)
  const incompleteInfo = result
    ? checkIncompleteWork(result)
    : null;
  const arithmeticOnly = result?.status !== 'CORRECT' && result?.arithmeticVerified === true && !hasCorrections;
  const hasVerifiedCalculation = result?.rows.some(row => row.arithmeticCorrect === true);
  const unresolved = result?.rows.filter(row => row.status === 'UNSURE'
    && row.rowKind != null && row.rowKind !== 'HEADING') ?? [];

  return <View style={styles.card}>
    <View style={styles.headingRow}>
      <Ionicons name="checkmark-done-outline" size={22} color={COLORS.primaryDark} accessible={false} />
      <View style={styles.resultCopy}>
        <Text style={styles.caption}>2 · NHẬN XÉT BÀI LÀM</Text>
        <Text accessibilityRole="header" style={styles.title}>{result ? 'Kết quả bài em làm' : 'Cùng kiểm tra bài em làm'}</Text>
      </View>
    </View>

    {imageUri && photoCurrent && (!result || result.status === 'CORRECT') ? <View style={styles.photoFrame}>
      <Image source={{ uri: imageUri }} style={styles.workPhoto} resizeMode="contain" accessibilityLabel="Ảnh bài em đã làm" />
      {result?.status === 'CORRECT' ? <View style={styles.photoBadge} accessibilityLabel="Bài đã được kiểm tra đúng"><Ionicons name="ribbon" size={27} color="#B47C14" /></View> : null}
    </View> : null}

    {imageUri && photoCurrent && result && result.status !== 'CORRECT' ? (
      <WorkPhotoEvidence
        presentation="photo"
        issuesOnly
        imageUri={imageUri}
        lines={lines}
        rows={result.rows}
        selectedLine={selectedLine}
        onSelectLine={choose}
        problemText={problemText}
        incompleteInfo={incompleteInfo}
      />
    ) : null}

    {!result && !busy ? <Text style={styles.body}>Mình sẽ kiểm tra các phép tính em đã viết.</Text> : null}
    {!enabled ? <Text style={styles.notice}>Em xác nhận đề và bài làm đã đọc đúng ở phía trên trước nhé.</Text> : null}
    {!result && !error && !busy ? <AppButton title="Nhận xét bài em làm" disabled={disabledNow} onPress={() => void review()} /> : null}

    {busy ? <View accessibilityLiveRegion="polite" style={styles.panel}>
      <TaskProgress steps={['Bài làm đã xác nhận', 'Kiểm tra phép tính', 'Mở nhận xét']} activeStep={1} />
      <AppButton title="Dừng chờ, giữ bài làm" variant="secondary" onPress={stop} />
    </View> : null}

    {error ? <RecoveryNotice title="Chưa mở được nhận xét" message={error} actions={[
      { label: 'Thử lại', accessibilityLabel: 'Nhận xét bài em làm', icon: 'refresh-outline', onPress: () => void review(), disabled: disabledNow || busy },
      ...(!expired && photoCurrent ? [{ label: 'Chụp lại', accessibilityLabel: 'Chụp lại bài em đã sửa', icon: 'camera-outline' as const, onPress: () => { stop(); onCaptureWork(); }, disabled }] : []),
    ]} /> : null}

    {result && enabled ? <>
      {/* Result Status Banner: Correct (Green), Incomplete (Orange), Revision (Red/Amber) */}
      {result.status === 'CORRECT' ? (
        <CorrectAnswerFeedback message="Em làm đúng rồi!" detail={result.praise} />
      ) : incompleteInfo?.isIncomplete ? (
        // INCOMPLETE WORK: displayed prominently in ORANGE as requested by the user
        <View style={styles.incompleteContainer} accessibilityLiveRegion="polite">
          <View style={[styles.panel, styles.incompleteBanner]}>
            <Ionicons name="time" size={26} color="#EA580C" accessible={false} />
            <View style={styles.resultCopy}>
              <Text style={styles.incompleteTitle}>Bài làm thiếu · Chưa làm xong</Text>
            <Text style={styles.body}>{arithmeticOnly ? 'Các phép tính em đã viết đều đúng.' : 'Em làm tiếp phần còn thiếu bên dưới nhé.'}</Text>
            </View>
          </View>
          <View style={styles.missingPanel}>
            <View style={styles.missingHeaderRow}>
              <Ionicons name="alert-circle" size={20} color="#EA580C" />
              <Text style={styles.missingTitle}>Em đang thiếu phần này:</Text>
            </View>
            <Text style={styles.missingBody}>{incompleteInfo.missingDescription}</Text>
          </View>
        </View>
      ) : arithmeticOnly ? (
        <View style={[styles.panel, styles.arithmeticSuccess]} accessibilityLiveRegion="polite">
          <Text style={styles.label}>Các phép tính em viết đều đúng</Text>
          <Text style={styles.body}>{result.summary}</Text>
        </View>
      ) : (
        <View style={[styles.panel, hasCorrections ? styles.revision : styles.attention]} accessibilityLiveRegion="polite">
          <Ionicons name={hasCorrections ? 'create-outline' : 'help-circle-outline'} size={25}
            color={hasCorrections ? '#B91C1C' : '#98621F'} accessible={false} />
          <View style={styles.resultCopy}>
            <Text style={styles.label}>{hasCorrections ? 'Các phép tính em cần sửa'
              : hasVerifiedCalculation ? 'Đã kiểm tra một phần bài làm' : 'Chưa kiểm tra được phép tính'}</Text>
            <Text style={styles.body}>{hasCorrections ? 'Em xem các dòng được đánh dấu bên dưới nhé.' : result.summary}</Text>
          </View>
        </View>
      )}

      {unresolved.map(row => <View key={row.lineIndex} style={styles.panel}>
        <Text style={styles.label}>{`Dòng ${row.lineIndex + 1}`}</Text>
        <MathText style={styles.body}>{row.sourceText}</MathText>
        {row.arithmeticCorrect === true && !arithmeticOnly ? <Text style={styles.caption}>Phép tính ở dòng này đúng.</Text> : null}
        <Text style={styles.caption}>{row.feedback}</Text>
      </View>)}
      {result.status === 'NEEDS_REVIEW' && result.complete !== false ? <AppButton
        title="Thử nhận xét lại" variant="secondary" disabled={disabledNow || busy} onPress={() => void review()} /> : null}

      {result.status === 'CORRECT' ? <AppButton title={showDetails ? 'Thu gọn nhận xét' : 'Xem nhận xét chi tiết'} variant="ghost" onPress={() => setShowDetails(value => !value)} /> : null}

      {showDetails ? <>
        {result.status === 'CORRECT' ? <Text style={styles.body}>{result.summary}</Text> : null}
        {result.status !== 'CORRECT' && selected ? <>
          <Text style={styles.caption}>Chọn dòng cần xem lại để mở gợi ý.</Text>
          <WorkPhotoEvidence issuesOnly showFeedback={multipleEdits} presentation="lines" imageUri=""
            lines={lines} rows={result.rows} selectedLine={selectedLine} onSelectLine={choose} problemText={problemText} />
        </> : null}

        {selected && (!multipleEdits || selected.hints.length) ? (() => {
          const analysis = analyzeRowPresentation(
            selected.sourceText,
            problemText,
            selected.status,
            selected.feedback,
            selected.hints,
            selected.errorKind
          );

          return (
            <View
              style={[
                styles.panel,
                styles.detail,
                {
                  borderColor: analysis.badgeBorder,
                  backgroundColor: analysis.badgeBg,
                },
              ]}
              accessibilityLiveRegion="polite"
            >
              {multipleEdits ? <Text style={styles.label}>{`Gợi ý cho dòng ${selected.lineIndex + 1}`}</Text> : <>
              <View style={styles.selectedRowHeader}>
                <View style={[styles.selectedTag, { backgroundColor: analysis.badgeColor }]}>
                  <Text style={styles.selectedTagText}>{analysis.label}</Text>
                </View>
                <Text style={styles.selectedLineNumber}>{`Dòng ${selected.lineIndex + 1}`}</Text>
              </View>

              <MathText style={styles.source}>{selected.sourceText}</MathText>
              <Text style={[styles.body, { color: COLORS.textPrimary, fontFamily: FONTS.medium }]}>
                {analysis.detailedFeedback}
              </Text>
              </>}

              {analysis.hints.length ? <AppButton
                title={hintCount === analysis.hints.length ? 'Đã mở đủ gợi ý dòng này' : hintCount ? 'Gợi ý rõ hơn' : 'Gợi ý sửa dòng này'}
                variant="secondary"
                disabled={hintCount === analysis.hints.length}
                onPress={() => setHintCount(count => Math.min(count + 1, analysis.hints.length))}
              /> : null}

              {analysis.hints.slice(0, hintCount).map((hint, index) => <View key={index} style={styles.hint}>
                <Text style={styles.label}>{`Gợi ý ${index + 1}`}</Text>
                <Text style={styles.body}>{hint}</Text>
              </View>)}

            </View>
          );
        })() : null}

        {hasCorrections || result.status === 'CORRECT' ? <View style={styles.panel}>
          <Text style={styles.label}>Việc em làm tiếp</Text>
          <Text style={styles.body}>{hasCorrections ? 'Em sửa các phép tính được đánh dấu, rồi gửi lại bài nhé.' : result.nextAction}</Text>
        </View> : null}

        {hasCorrections || (photoCurrent && result.status !== 'CORRECT' && !arithmeticOnly) ? <View style={styles.resultCopy}>
          {editRows.length ? <Pressable accessibilityRole="button" accessibilityLabel={multipleEdits ? 'Em nhập các dòng vừa sửa' : 'Em nhập dòng vừa sửa'}
            aria-expanded={editingRewrite} aria-controls={rewriteId}
            accessibilityState={{ expanded: editingRewrite, disabled: disabledNow }} disabled={disabledNow}
            onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
            onPress={() => setRewrite(value => value === null
              ? Object.fromEntries(editRows.map(row => [row.lineIndex, row.sourceText])) : null)}
            style={({ pressed }) => [styles.toggle, focused && styles.focused, pressed && styles.pressed]}>
            <Text style={styles.link}>{multipleEdits ? 'Em nhập các dòng vừa sửa' : 'Em nhập dòng vừa sửa'}</Text>
          </Pressable> : null}
          <AppButton title="Chụp lại bài em đã sửa" variant="secondary" disabled={disabledNow}
            onPress={() => { stop(); onCaptureWork(); }} />
          {rewrite ? <View style={styles.hint} nativeID={rewriteId}>
            {editRows.map((row, index) => {
              const label = multipleEdits ? `Dòng ${row.lineIndex + 1} em vừa sửa` : 'Dòng em vừa sửa';
              return <View key={row.lineIndex} style={styles.resultCopy}>
                <Text style={styles.label}>{label}</Text>
                <WorkLineInput key={row.sourceText} inputRef={index === 0 ? rewriteInput : undefined} label={label}
                  value={rewrite[row.lineIndex]} disabled={disabledNow}
                  onChange={value => setRewrite(current => current && { ...current, [row.lineIndex]: value })} />
              </View>;
            })}
            <AppButton title="Nhận xét lại bài" disabled={disabledNow || !canSave}
              onPress={applyRewrite} />
          </View> : null}
        </View> : null}

        {result.status === 'CORRECT' && result.alternative ? <>
          <Pressable accessibilityRole="button" accessibilityLabel="Khám phá thêm một cách nghĩ" aria-expanded={showAlternative} aria-controls={alternativeId}
            accessibilityState={{ expanded: showAlternative }} onPress={() => setShowAlternative(value => !value)} style={styles.toggle}>
            <Text style={styles.link}>Khám phá thêm một cách nghĩ</Text>
          </Pressable>
          {showAlternative ? <View style={styles.hint} nativeID={alternativeId}><Text style={styles.body}>{result.alternative}</Text></View> : null}
        </> : null}
      </> : null}
    </> : null}

    {result?.status === 'CORRECT' && enabled && !disabled && !expired ? <>
      <AppButton title="Hoàn tất nhận xét" onPress={() => router.replace('/(tabs)')} />
      <QuizAfterLearningButton sourceType="WORK_REVIEW" sourceId={result.sourceId} />
    </> : null}

  </View>;
}

const styles = StyleSheet.create({
  card: { padding: 18, borderRadius: 24, borderWidth: 1, borderColor: '#EEE5FB', backgroundColor: COLORS.surface, gap: 14, ...SHADOWS.small },
  photoFrame: { position: 'relative', borderRadius: 18, overflow: 'hidden', backgroundColor: '#F1ECF7', borderWidth: 1, borderColor: '#E8DFF4' },
  workPhoto: { width: '100%', height: 210 },
  photoBadge: { position: 'absolute', top: 10, right: 10, borderRadius: 25, width: 48, height: 48, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFE28C', borderWidth: 3, borderColor: '#FFF1C6' },
  resultCopy: { gap: 6, flex: 1 },
  headingRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { flexShrink: 1, fontSize: 18, lineHeight: 26, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  body: { fontSize: 14, lineHeight: 23, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  label: { fontSize: 16, lineHeight: 24, color: COLORS.textPrimary, fontFamily: FONTS.bold },
  source: { fontSize: 18, lineHeight: 28, color: COLORS.textPrimary, fontFamily: FONTS.bold },
  panel: { borderRadius: 16, padding: 16, gap: 10, backgroundColor: COLORS.surfaceSubdued },
  revision: { backgroundColor: '#FEF2F2', borderWidth: 1, borderColor: '#FCA5A5' },
  arithmeticSuccess: { backgroundColor: '#ECF8F0', borderWidth: 1, borderColor: '#D0EBD9' },
  attention: { backgroundColor: '#FFF8E9', borderWidth: 1, borderColor: '#FDE68A' },
  incompleteContainer: { gap: 10 },
  incompleteBanner: {
    backgroundColor: '#FFF7ED',
    borderWidth: 1.5,
    borderColor: '#FB923C',
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  incompleteTitle: { fontSize: 16, lineHeight: 24, color: '#C2410C', fontFamily: FONTS.extraBold },
  missingPanel: {
    backgroundColor: '#FFF7ED',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#F97316',
    padding: 14,
    gap: 8,
  },
  missingHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  missingTitle: { fontSize: 15, lineHeight: 22, color: '#EA580C', fontFamily: FONTS.bold },
  missingBody: { fontSize: 14, lineHeight: 22, color: '#9A3412', fontFamily: FONTS.medium },
  detail: { borderWidth: 2 },
  selectedRowHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  selectedTag: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  selectedTagText: { color: '#FFFFFF', fontFamily: FONTS.bold, fontSize: 13, lineHeight: 18 },
  selectedLineNumber: { color: COLORS.textPrimary, fontFamily: FONTS.bold, fontSize: 15 },
  hint: { padding: 12, gap: 8, backgroundColor: COLORS.surface, borderRadius: 12, borderWidth: 1, borderColor: COLORS.border },
  error: { fontSize: 15, lineHeight: 24, color: '#963E22', fontFamily: FONTS.semiBold },
  notice: { fontSize: 14, lineHeight: 22, color: '#70441E', fontFamily: FONTS.medium },
  caption: { fontSize: 13, lineHeight: 21, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  toggle: { minHeight: 48, padding: 12, justifyContent: 'center', borderWidth: 2, borderColor: COLORS.border, borderRadius: 14 },
  link: { fontSize: 15, lineHeight: 23, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' },
  pressed: { opacity: 0.7 },
});
