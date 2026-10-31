import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
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
import { QuizInvitation } from '../quiz/QuizInvitation';

type Props = { problemText: string; workText: string; imageUri: string; lines: NotebookLine[];
  enabled: boolean; disabled?: boolean; photoCurrent?: boolean; autoStart?: boolean; onReviseWork: (work: string) => void; onCaptureWork: () => void; onSessionExpired?: () => void; onReviewReady?: () => void };

export function StudentWorkReview(props: Props) {
  // A response belongs to exactly one source, including the privacy-approved photo and its physical regions.
  return <ReviewSession key={JSON.stringify([props.problemText, props.workText, props.imageUri, props.lines, props.enabled, props.disabled, props.photoCurrent])} {...props} />;
}

function ReviewSession({ problemText, workText, imageUri, lines, enabled, disabled = false, photoCurrent = true, autoStart = false, onReviseWork, onCaptureWork, onSessionExpired, onReviewReady }: Props) {
  const router = useRouter();
  const [result, setResult] = useState<WorkReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [expired, setExpired] = useState(false);
  const [error, setError] = useState('');
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [hintCount, setHintCount] = useState(0);
  const [showAlternative, setShowAlternative] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showAllLines, setShowAllLines] = useState(false);
  const [showPractice, setShowPractice] = useState(false);
  const [rewrite, setRewrite] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const active = useRef(false);
  const sequence = useRef(0);
  const autoStarted = useRef(false);
  const rewriteInput = useRef<TextInputInstance>(null);
  const rewriteId = useId();
  const alternativeId = useId();
  const disabledNow = disabled || !enabled || expired;
  const stop = useCallback(() => { sequence.current += 1; controller.current?.abort(); controller.current = null; setBusy(false); }, []);
  useFocusEffect(useCallback(() => {
    active.current = true;
    return () => { active.current = false; sequence.current += 1; controller.current?.abort(); controller.current = null; setBusy(false); };
  }, []));
  const editingRewrite = rewrite !== null;
  useEffect(() => { if (editingRewrite) rewriteInput.current?.focus(); }, [editingRewrite]);
  const review = async () => {
    if (disabledNow || controller.current) return;
    const abort = new AbortController(); controller.current = abort;
    const id = ++sequence.current;
    const sourceId = `work_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
    setBusy(true); setError(''); setResult(null); setRewrite(null); setShowAlternative(false); setShowAllLines(false); setHintCount(0);
    try {
      const next = await TutorService.reviewWork({ sourceId, problemText, workText, problemConfirmed: true, workConfirmed: true }, abort.signal);
      if (!active.current || abort.signal.aborted || sequence.current !== id) return;
      setResult(next);
      setShowDetails(next.status !== 'CORRECT');
      onReviewReady?.();
      setSelectedLine((next.rows.find(row => row.status === 'FIX') || next.rows.find(row => row.status === 'UNSURE') || next.rows[0])?.lineIndex ?? null);
    } catch (failure: any) {
      if (!active.current || abort.signal.aborted || sequence.current !== id) return;
      if (failure?.response?.status === 401) { setExpired(true); onSessionExpired?.(); setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.'); }
      else if ([400, 422].includes(failure?.response?.status)) setError('Có chỗ trong đề hoặc bài làm chưa rõ. Em kiểm tra các dòng hoặc chụp lại một phần nhỏ hơn nhé.');
      else setError('Chưa nhận xét được lúc này. Đề và bài làm vẫn ở đây; em thử lại nhé.');
    } finally {
      if (active.current && sequence.current === id) { controller.current = null; setBusy(false); }
    }
  };
  useEffect(() => {
    if (!autoStart || disabledNow || autoStarted.current) return;
    let current = true;
    // Wait until focus effects have mounted; Strict Mode's discarded effect must not submit.
    void Promise.resolve().then(() => {
      if (!current || !active.current || autoStarted.current) return;
      autoStarted.current = true;
      void review();
    });
    return () => { current = false; };
  }, [autoStart, disabledNow]);
  const selected = result?.rows.find(row => row.lineIndex === selectedLine);
  const sourceLines = workReviewLines(workText);
  const rewrittenLine = rewrite === null ? '' : trimWorkReviewLine(rewrite);
  const choose = (index: number) => { setSelectedLine(index); setHintCount(0); setRewrite(null); };
  const applyRewrite = () => {
    if (disabledNow || busy || !selected || rewrite === null || !rewrittenLine || /[\r\n\v\f\x1c-\x1e\x85\u2028\u2029]/.test(rewrite)
      || rewrittenLine === selected.sourceText || rewrite.includes('[?]')) return;
    const updated = sourceLines.map((line, index) => index === selected.lineIndex ? rewrittenLine : line).join('\n');
    if (updated.length <= 6000) onReviseWork(updated);
  };
  return <View style={styles.card}>
    <View style={styles.headingRow}><Ionicons name="checkmark-done-outline" size={22} color={COLORS.primaryDark} accessible={false} />
      <View style={styles.resultCopy}><Text style={styles.caption}>2 · NHẬN XÉT BÀI LÀM</Text><Text accessibilityRole="header" style={styles.title}>{result ? 'Kết quả bài em làm' : 'Cùng kiểm tra bài em làm'}</Text></View></View>
    {imageUri && photoCurrent && (!result || result.status === 'CORRECT') ? <View style={styles.photoFrame}>
      <Image source={{ uri: imageUri }} style={styles.workPhoto} resizeMode="contain" accessibilityLabel="Ảnh bài em đã làm" />
      {result?.status === 'CORRECT' ? <View style={styles.photoBadge} accessibilityLabel="Bài đã được kiểm tra đúng"><Ionicons name="ribbon" size={27} color="#B47C14" /></View> : null}
    </View> : null}
    {imageUri && photoCurrent && result && result.status !== 'CORRECT' ? <WorkPhotoEvidence presentation="photo" issuesOnly imageUri={imageUri} lines={lines} rows={result.rows} selectedLine={selectedLine} onSelectLine={choose} /> : null}
    {!result && !busy ? <Text style={styles.body}>Mình sẽ đối chiếu cách làm, phép tính và đơn vị. Em không cần làm lại cả bài.</Text> : null}
    {!photoCurrent && imageUri ? <Text style={styles.notice}>Em đang sửa bài bằng chữ. Ảnh trước khi sửa vẫn được giữ ở phần bài làm; em chụp lại để xem đánh dấu trên bài mới nhé.</Text> : null}
    {!enabled ? <Text style={styles.notice}>Em xác nhận đề và bài làm đã đọc đúng ở phía trên trước nhé.</Text> : null}
    {!result && !error && !busy ? <AppButton title="Nhận xét bài em làm" disabled={disabledNow} onPress={() => void review()} /> : null}
    {busy ? <View accessibilityLiveRegion="polite" style={styles.panel}>
      <TaskProgress steps={['Bài làm đã xác nhận', 'Đối chiếu từng dòng', 'Mở nhận xét']} activeStep={1} />
      <AppButton title="Dừng chờ, giữ bài làm" variant="secondary" onPress={stop} />
    </View> : null}
    {error ? <RecoveryNotice title="Chưa mở được nhận xét" message={error} actions={[
      { label: 'Thử lại', accessibilityLabel: 'Nhận xét bài em làm', icon: 'refresh-outline', onPress: () => void review(), disabled: disabledNow || busy },
      ...(!expired ? [{ label: 'Chụp lại', accessibilityLabel: 'Chụp lại bài em đã sửa', icon: 'camera-outline' as const, onPress: () => { stop(); onCaptureWork(); }, disabled }] : []),
    ]} /> : null}
    {result && enabled ? <>
      <View style={[styles.panel, result.status === 'CORRECT' ? styles.success : styles.attention]} accessibilityLiveRegion="polite">
        {result.status === 'CORRECT' ? <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={styles.praiseArt} resizeMode="contain" accessible={false} /> : <Ionicons name={result.status === 'NEEDS_REVISION' ? 'create-outline' : 'help-circle-outline'} size={25} color="#98621F" accessible={false} />}
        <View style={[styles.resultCopy, result.status === 'CORRECT' && { flex: 1 }]}>
        <Text style={styles.label}>{result.status === 'CORRECT' ? 'Em làm tốt rồi!' : result.status === 'NEEDS_REVISION' ? 'Cùng sửa từng chỗ nhé' : 'Cần xem lại trước khi kết luận'}</Text>
        {result.status !== 'CORRECT' ? <Text style={styles.body}>{result.summary}</Text> : null}
        {result.praise ? <Text style={styles.praise}>{result.praise}</Text> : null}
        </View>
      </View>
      {result.status === 'CORRECT' ? <AppButton title={showDetails ? 'Thu gọn nhận xét' : 'Xem nhận xét chi tiết'} variant="ghost" onPress={() => setShowDetails(value => !value)} /> : null}
      {showDetails ? <>
      {result.status === 'CORRECT' ? <Text style={styles.body}>{result.summary}</Text> : null}
      <Text style={styles.caption}>Chọn dòng cần xem lại để đọc nhận xét và cách sửa.</Text>
      <WorkPhotoEvidence issuesOnly={!showAllLines && result.status !== 'CORRECT'} presentation={photoCurrent && imageUri ? 'lines' : 'full'} imageUri={photoCurrent ? imageUri : ''} lines={lines} rows={result.rows} selectedLine={selectedLine} onSelectLine={choose} />
      {result.status !== 'CORRECT' && result.rows.some(row => row.status === 'OK') ? <AppButton title={showAllLines ? 'Chỉ xem chỗ cần sửa' : 'Xem tất cả các dòng'} variant="ghost" onPress={() => setShowAllLines(value => !value)} /> : null}
      {selected ? <View style={[styles.panel, styles.detail]} accessibilityLiveRegion="polite">
        <Text style={styles.label}>{`Dòng ${selected.lineIndex + 1} · ${selected.status === 'FIX' ? 'Cần sửa' : selected.status === 'OK' ? 'Phù hợp' : 'Cần xem lại'}`}</Text>
        <MathText style={styles.source}>{selected.sourceText}</MathText>
        <Text style={styles.body}>{selected.feedback}</Text>
        {selected.hints.length ? <AppButton title={hintCount === selected.hints.length ? 'Đã mở đủ gợi ý dòng này' : hintCount ? 'Gợi ý rõ hơn' : 'Gợi ý sửa dòng này'} variant="secondary"
          disabled={hintCount === selected.hints.length}
          onPress={() => setHintCount(count => Math.min(count + 1, selected.hints.length))} /> : null}
        {selected.hints.slice(0, hintCount).map((hint, index) => <View key={index} style={styles.hint}>
          <Text style={styles.label}>{`Gợi ý ${index + 1}`}</Text><Text style={styles.body}>{hint}</Text>
        </View>)}
        {selected.status !== 'OK' ? <>
          <Text style={styles.body}>Em sửa trong vở rồi chụp lại. Nếu chỉ sửa một dòng, em có thể nhập dòng vừa viết để mình xem tiếp.</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Em nhập dòng vừa sửa" aria-expanded={rewrite !== null} aria-controls={rewriteId}
            accessibilityState={{ expanded: rewrite !== null, disabled: disabledNow }} disabled={disabledNow}
            onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
            onPress={() => setRewrite(value => value === null ? selected.sourceText : null)}
            style={({ pressed }) => [styles.toggle, focused && styles.focused, pressed && styles.pressed]}>
            <Text style={styles.link}>Em nhập dòng vừa sửa</Text>
          </Pressable>
          {rewrite !== null ? <View style={styles.hint} nativeID={rewriteId}>
            <Text style={styles.label}>Dòng em vừa sửa</Text>
            <TextInput ref={rewriteInput} accessibilityLabel="Dòng em vừa sửa" value={rewrite} maxLength={500} editable={!disabledNow}
              onChangeText={setRewrite} style={styles.input} />
            <Text style={styles.caption}>Nội dung mới sẽ cần được xác nhận lại. Ảnh cũ giữ nguyên; em chụp lại để vị trí đánh dấu khớp bài vừa sửa.</Text>
            <Text style={styles.caption}>Em nhập một dòng vừa sửa, khác dòng cũ và không còn dấu [?], rồi chọn dùng dòng này nhé.</Text>
            <AppButton title="Dùng dòng em đã sửa" disabled={disabledNow || !rewrittenLine || rewrittenLine === selected.sourceText || rewrite.includes('[?]')
              || /[\r\n\v\f\x1c-\x1e\x85\u2028\u2029]/.test(rewrite) || sourceLines.join('\n').length - selected.sourceText.length + rewrittenLine.length > 6000}
              onPress={applyRewrite} />
          </View> : null}
        </> : null}
      </View> : null}
      <View style={styles.panel}><Text style={styles.label}>Việc em làm tiếp</Text><Text style={styles.body}>{result.nextAction}</Text></View>
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
      <AppButton title={showPractice ? 'Thu gọn luyện thêm' : 'Thử một câu tương tự'} variant="ghost" onPress={() => setShowPractice(value => !value)} />
      {showPractice ? <QuizInvitation sourceType="WORK_REVIEW" sourceId={result.sourceId} /> : null}
    </> : null}
    {result && result.status !== 'CORRECT' ? <AppButton title="Chụp lại bài em đã sửa" variant="secondary" disabled={disabled || expired}
      onPress={() => { stop(); onCaptureWork(); }} />
      : null}
  </View>;
}

const styles = StyleSheet.create({
  card: { padding: 18, borderRadius: 24, borderWidth: 1, borderColor: '#EEE5FB', backgroundColor: COLORS.surface, gap: 14, ...SHADOWS.small },
  photoFrame: { position: 'relative', borderRadius: 18, overflow: 'hidden', backgroundColor: '#F1ECF7', borderWidth: 1, borderColor: '#E8DFF4' },
  workPhoto: { width: '100%', height: 210 }, photoBadge: { position: 'absolute', top: 10, right: 10, borderRadius: 25, width: 48, height: 48, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFE28C', borderWidth: 3, borderColor: '#FFF1C6' },
  praiseArt: { width: 60, height: 67 }, resultCopy: { gap: 8 },
  headingRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { flexShrink: 1, fontSize: 18, lineHeight: 26, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  body: { fontSize: 14, lineHeight: 23, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  label: { fontSize: 16, lineHeight: 24, color: COLORS.textPrimary, fontFamily: FONTS.bold },
  source: { fontSize: 18, lineHeight: 28, color: COLORS.textPrimary, fontFamily: FONTS.bold },
  panel: { borderRadius: 16, padding: 16, gap: 10, backgroundColor: COLORS.surfaceSubdued },
  success: { backgroundColor: '#EDF9F1', borderWidth: 1, borderColor: '#D1ECD9', flexDirection: 'row', alignItems: 'center' }, attention: { backgroundColor: '#FFF8E9' },
  detail: { borderWidth: 1, borderColor: COLORS.border },
  hint: { padding: 12, gap: 8, backgroundColor: COLORS.surface, borderRadius: 12, borderWidth: 1, borderColor: COLORS.border },
  praise: { fontSize: 13, lineHeight: 21, color: '#48765F', fontFamily: FONTS.semiBold },
  error: { fontSize: 15, lineHeight: 24, color: '#963E22', fontFamily: FONTS.semiBold },
  notice: { fontSize: 14, lineHeight: 22, color: '#70441E', fontFamily: FONTS.medium },
  caption: { fontSize: 13, lineHeight: 21, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  toggle: { minHeight: 48, padding: 12, justifyContent: 'center', borderWidth: 2, borderColor: COLORS.border, borderRadius: 14 },
  link: { fontSize: 15, lineHeight: 23, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' }, pressed: { opacity: 0.7 },
  input: { minHeight: 54, padding: 12, borderWidth: 1.5, borderColor: COLORS.primaryDark, borderRadius: 12,
    fontSize: 17, color: COLORS.textPrimary, fontFamily: FONTS.regular, backgroundColor: COLORS.surfaceSubdued },
});
