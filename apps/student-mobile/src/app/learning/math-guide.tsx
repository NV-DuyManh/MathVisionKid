import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Image, Keyboard, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import type { ScrollViewInstance, TextInputInstance, ViewInstance } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { ImageDraft, recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';
import { divisionText, savedDivision, CompletedLessonStep, LessonResponse, NotebookLine, NotebookRead, TutorService, trimWorkReviewLine, workReviewLines } from '../../features/tutoring/api/TutorService';
import { DivisionReview } from '../../features/tutoring/DivisionReview';
import { AuthContext } from '../../context/AuthContext';
import { saveLesson } from '../../features/tutoring/learningHistory';
import { MathText } from '../../components/domain/MathText';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';
import { FractionExplorer, fractionsInProblem } from '../../features/tutoring/FractionExplorer';
import { HintCheckIn } from '../../features/tutoring/HintCheckIn';
import { ProblemSummary } from '../../features/tutoring/ProblemSummary';
import { StudentWorkReview } from '../../features/tutoring/StudentWorkReview';
import { LessonListening } from '../../features/tutoring/LessonListening';
import { LessonCalculation } from '../../features/tutoring/LessonCalculation';
import { completedNarration, stepNarration } from '../../features/tutoring/narration';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { LessonQuestion } from '../../features/tutoring/LessonQuestion';
import { LessonProblem } from '../../features/tutoring/LessonProblem';
import { NarrationPreparation, useNarrationPreparation } from '../../features/tutoring/NarrationPreparation';

const MASCOT = require('../../../assets/illustrations/mathvision-star.png');

function SolutionLine({ item }: { item: CompletedLessonStep }) {
  return <View style={styles.completedStep}>
    <MathText style={styles.question}>{item.solutionSentence || `${item.title} là:`}</MathText>
    <MathText style={styles.body}>{`${item.expression} = ${item.answer}${item.unit ? ` (${item.unit})` : ''}`}</MathText>
    {item.calculationDetails?.map((detail, index) => <MathText key={index} style={styles.body}>{detail}</MathText>)}
  </View>;
}

type GuideParams = { problemText?: string; workText?: string; lessonId?: string; reflection?: string };

export default function MathGuideScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  const params = useLocalSearchParams<GuideParams>();
  const [draftSource, setDraftSource] = useState(() => ({ owner, draft: recognitionDraftStore.getDraft() }));
  const draftOwner = useRef(owner);
  useFocusEffect(useCallback(() => {
    if (draftOwner.current !== owner) {
      recognitionDraftStore.clearDraft();
      draftOwner.current = owner;
    }
    setDraftSource({ owner, draft: recognitionDraftStore.getDraft() });
  }, [owner]));
  const draft = draftSource.owner === owner ? draftSource.draft : null;
  // Remount also aborts pending requests: answers/exploration belong to one source and account.
  const sourceKey = JSON.stringify([owner, params.problemText, params.workText, params.lessonId, params.reflection, draft]);
  return <NarrationPreparation key={sourceKey}><MathGuideLesson owner={owner} params={params} sourceDraft={draft} /></NarrationPreparation>;
}

function MathGuideLesson({ owner, params, sourceDraft }: { owner?: string; params: GuideParams; sourceDraft: ImageDraft | null }) {
  const router = useRouter();
  const { width, fontScale } = useWindowDimensions();
  const spacious = width >= 1100 && fontScale <= 1.3;
  const supplied = typeof params.problemText === 'string' ? params.problemText.slice(0, 4000) : '';
  const suppliedWork = typeof params.workText === 'string' ? params.workText.slice(0, 6000) : '';
  const draft = supplied || suppliedWork ? null : sourceDraft;
  const context = draft?.lessonContext;
  const imageUri = draft?.mode === 'MATH_TUTOR' ? draft.croppedImageUri ?? '' : '';
  const photoAllowed = !!imageUri && draft?.privacyConfirmed === true && !!draft.privacyImageUri;
  const [reading, setReading] = useState<NotebookRead | null>(supplied || suppliedWork ? {
    kind: suppliedWork ? 'MIXED' : 'PROBLEM', problemText: supplied,
    lines: savedDivision(suppliedWork) ? [{ text: suppliedWork, box: null, uncertain: true, division: savedDivision(suppliedWork) }] : [], needsProblem: !supplied,
  } : null);
  const [problem, setProblem] = useState(supplied || context?.problemText || '');
  const [work, setWork] = useState(suppliedWork || context?.workText || '');
  const [workImage, setWorkImage] = useState(context?.workImageUri || '');
  const [workImageCurrent, setWorkImageCurrent] = useState(context?.workImageCurrent !== false);
  const [workLines, setWorkLines] = useState<NotebookLine[]>(context?.workLines || reading?.lines || []);
  const [problemImage, setProblemImage] = useState(context?.problemImageUri || '');
  const [uncertainWork, setUncertainWork] = useState(context?.uncertainWork || false);
  const [problemConfirmed, setProblemConfirmed] = useState(context?.problemConfirmed === true);
  const [workConfirmed, setWorkConfirmed] = useState(context?.workConfirmed === true);
  const [lesson, setLesson] = useState<LessonResponse | null>(null);
  const [attempt, setAttempt] = useState('');
  const [answerEdited, setAnswerEdited] = useState(false);
  const [hintCount, setHintCount] = useState(0);
  const [hintText, setHintText] = useState('');
  const [hintExhausted, setHintExhausted] = useState(false);
  const [focusedChoice, setFocusedChoice] = useState<string | null>(null);
  const [reviewedStep, setReviewedStep] = useState<CompletedLessonStep | null>(null);
  const [fractionInput, setFractionInput] = useState(false);
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [tool, setTool] = useState<'audio' | 'ask' | 'menu' | 'work' | 'summary' | 'visual' | 'hint' | null>(null);
  const [visualIndex, setVisualIndex] = useState(0);
  const [busy, setBusy] = useState<'read' | 'lesson' | 'answer' | null>(null);
  const [finishing, setFinishing] = useState<{ kind: 'read' | 'lesson'; id: number } | null>(null);
  const [error, setError] = useState('');
  const [expired, setExpired] = useState(false);
  const [editing, setEditing] = useState<'problem' | 'work' | null>(null);
  const [showWork, setShowWork] = useState(false);
  const [reviewFocused, setReviewFocused] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lessonId] = useState(() => context?.lessonId || (typeof params.lessonId === 'string' ? params.lessonId : `lesson_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`));
  const requestId = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const running = useRef(false);
  const active = useRef(true);
  const initialized = useRef(false);
  const scroll = useRef<ScrollViewInstance>(null);
  const answerInput = useRef<TextInputInstance>(null);
  const firstChoice = useRef<ViewInstance>(null);
  const questionPosition = useRef(0);
  const lessonPosition = useRef(0);
  const invalidPhoto = reading && ['MULTIPLE', 'UNREADABLE'].includes(reading.kind);
  const preparationWork = workConfirmed && !work.includes('[?]') ? work : '';
  useEffect(() => {
    if (!owner || lesson || editing || busy || invalidPhoto || problem.trim().length < 3 || problem.includes('[?]')) return;
    const abort = new AbortController();
    // Private preparation starts while the pupil reviews the transcription.
    // It returns no lesson; the normal Start action still requires confirmation.
    void TutorService.prepareLesson(problem.trim(), preparationWork, abort.signal).catch(() => {});
    return () => abort.abort();
  }, [owner, problem, preparationWork, editing, invalidPhoto, lesson, busy]);
  const divisionLines = workLines.filter(line => line.division);
  const divisionLine = !invalidPhoto && divisionLines.length === 1 ? divisionLines[0] : null;
  const division = divisionLine?.division;
  const step = lesson?.step;
  const lessonSessionId = lesson?.sessionId;
  const lessonStepIndex = lesson?.stepIndex;
  const narrationParts = reviewedStep ? completedNarration([reviewedStep]) : step ? stepNarration(step, hintText)
    : lesson ? completedNarration(lesson.completed.filter(item => item.kind !== 'UNDERSTAND')) : [];
  useNarrationPreparation(owner && lesson ? { sessionId: lesson.sessionId, revision: lesson.revision } : null, narrationParts);
  useEffect(() => {
    if (!lessonSessionId) return;
    const frame = requestAnimationFrame(() => scroll.current?.scrollTo({ y: 0, animated: false }));
    return () => cancelAnimationFrame(frame);
  }, [lessonSessionId, lessonStepIndex]);
  const cancel = () => {
    requestId.current += 1; controller.current?.abort(); controller.current = null; running.current = false; setBusy(null); setFinishing(null);
  };
  const failureMessage = useCallback((failure: any) => {
    if (failure?.response?.status === 401) {
      setExpired(true); setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.');
    } else if ([409, 410].includes(failure?.response?.status)) {
      setLesson(null); setError('Bài học đã hết phiên. Đề và bài làm vẫn ở đây; em bắt đầu lại nhé.');
    } else if ([400, 422].includes(failure?.response?.status)) {
      setError('Đề bài còn thiếu hoặc có chỗ chưa rõ. Em kiểm tra lại lời văn, số và câu hỏi nhé.');
    } else if (failure?.code === 'ECONNABORTED' || failure?.response?.data?.error?.code === 'TUTOR_TIMEOUT') {
      setError('Phần hướng dẫn chưa kịp chuẩn bị trong thời gian chờ. Đề và bài làm vẫn được giữ; em thử lại nhé.');
    } else if (failure?.response?.status === 503 || failure?.response?.status === 429) {
      const code = failure?.response?.data?.error?.code;
      setError(code === 'TUTOR_RATE_LIMITED' || code === 'TUTOR_BUSY' || failure?.response?.status === 429
        ? 'Đang có nhiều yêu cầu. Em chờ một chút rồi thử lại; đề và bài làm vẫn được giữ.'
        : code === 'LESSON_VALIDATION_FAILED'
          ? 'Bản hướng dẫn vừa tạo chưa đạt kiểm tra nên mình chưa mở cho em. Đề và bài làm vẫn được giữ; em thử lại nhé.'
          : 'Mình chưa chuẩn bị được hướng dẫn lúc này. Bài của em vẫn ở đây; em thử lại nhé.');
    } else setError('Chưa kết nối được lúc này. Bài của em vẫn ở đây, em thử lại nhé.');
  }, []);
  const run = useCallback(async <T,>(kind: 'read' | 'lesson' | 'answer', task: (signal: AbortSignal) => Promise<T>, apply: (value: T) => void) => {
    if (running.current || expired) return;
    const id = ++requestId.current; const abort = new AbortController();
    controller.current = abort; running.current = true; setBusy(kind); setFinishing(null); setError('');
    try {
      const result = await task(abort.signal);
      if (active.current && id === requestId.current) {
        apply(result);
        if (kind === 'read') setFinishing({ kind, id });
      }
    } catch (failure) {
      if (active.current && id === requestId.current && !abort.signal.aborted) failureMessage(failure);
    } finally {
      if (active.current && id === requestId.current) { running.current = false; controller.current = null; setBusy(null); }
    }
  }, [expired, failureMessage]);
  const inspectPhoto = useCallback(async () => {
    if (!photoAllowed) return;
    await run('read', signal => TutorService.inspect(imageUri, true, signal), result => {
      setReading(result); setLesson(null);
      if (['MULTIPLE', 'UNREADABLE'].includes(result.kind)) return;
      const workRead = result.kind === 'WORK' || result.kind === 'MIXED';
      const text = workRead ? result.lines.map(row => row.text).join('\n') : '';
      if (context?.purpose === 'ADD_PROBLEM') {
        // A worked page is not silently treated as an original question.
        if (!result.problemText.trim()) { setError('Ảnh này chưa có đề bài. Em chụp phần câu hỏi nhé.'); return; }
        setProblem(result.problemText); setProblemImage(imageUri); setProblemConfirmed(false);
      } else if (context?.purpose === 'ADD_WORK') {
        if (!workRead) { setError('Ảnh này chưa có phần em đã làm. Em chụp bài làm nhé.'); return; }
        setWork(text); setWorkImage(imageUri); setWorkImageCurrent(true); setWorkLines(result.lines); setUncertainWork(result.lines.some(row => row.uncertain)); setWorkConfirmed(false);
      } else {
        setProblem(draft?.problemText || result.problemText);
        setProblemConfirmed(false); setWorkConfirmed(false);
        setWork(text); setWorkLines(workRead ? result.lines : []); setUncertainWork(workRead && result.lines.some(row => row.uncertain));
        if (workRead) { setWorkImage(imageUri); setWorkImageCurrent(true); }
        if (result.problemText) setProblemImage(imageUri);
      }
    });
  }, [photoAllowed, imageUri, context?.purpose, draft?.problemText, run]);

  useFocusEffect(useCallback(() => {
    active.current = true;
    if (!initialized.current && photoAllowed) { initialized.current = true; void inspectPhoto(); }
    return () => { active.current = false; requestId.current += 1; controller.current?.abort(); running.current = false; };
  }, [photoAllowed, inspectPhoto]));

  const capture = (purpose?: 'ADD_PROBLEM' | 'ADD_WORK') => {
    cancel();
    if (purpose) {
      const pending: ImageDraft = { rawUri: '', uri: '', width: 0, height: 0, mimeType: 'image/jpeg', filename: 'pending.jpg', mode: 'MATH_TUTOR',
        lessonContext: { purpose, problemText: problem, workText: work, workImageUri: workImage, workImageCurrent, workLines, problemImageUri: problemImage,
          lessonId, uncertainWork, problemConfirmed, workConfirmed } };
      recognitionDraftStore.setDraft(pending);
    } else recognitionDraftStore.clearDraft();
    router.push({ pathname: '/camera' as any, params: { mode: 'MATH_TUTOR' } });
  };
  const start = () => {
    if (problem.trim().length < 3 || problem.includes('[?]') || !problemConfirmed) return;
    setTool(null);
    Keyboard.dismiss();
    const confirmedWork = workConfirmed && !work.includes('[?]') ? work : '';
    void run('lesson', signal => TutorService.startLesson(problem.trim(), confirmedWork,
      { problemConfirmed, workConfirmed: !!confirmedWork, guidedUnderstanding: true, startWithReading: true }, signal), result => {
      setLesson(result); setReviewedStep(null); setAttempt(''); setAnswerEdited(false); setSaved(false);
      setHintCount(0); setFractionInput(!!result.step?.expression && /phân số|mấy phần/i.test(result.step.question));
      setHintText(''); setHintExhausted(false); setFocusedChoice(null);
    });
  };
  const answer = (value: string, hint = false) => {
    if (!lesson || (hint && hintExhausted)) return;
    void run('answer', signal => TutorService.answerLesson(lesson, value, hint, signal), result => {
      setLesson(result);
      setAnswerEdited(false);
      if (hint && result.status === 'HINT') {
        const repeated = !!hintText && result.feedback === hintText;
        setHintExhausted(repeated);
        if (!repeated) setHintCount(value => value + 1);
        setHintText(result.feedback);
      }
      if (result.stepIndex !== lesson.stepIndex) {
        setAttempt(''); setHintCount(0); setHintText(''); setHintExhausted(false); setFocusedChoice(null);
        setFractionInput(!!result.step?.expression && /phân số|mấy phần/i.test(result.step.question));
        if (result.status !== 'COMPLETE') setReviewedStep(result.completed[result.completed.length - 1]);
      }
      setSaved(false);
    });
  };
  const archive = async () => {
    if (saving || (!problem.trim() && !work)) return;
    setSaving(true);
    try {
      await saveLesson(owner, { id: lessonId, timestamp: Date.now(), problemText: problem, workText: work,
        reflection: lesson?.completed.filter(row => row.expression).map(row => `${row.solutionSentence || row.title}\n${row.expression} = ${row.answer} ${row.unit}`).join('\n').slice(0, 2000) || '',
        reviewedSteps: lesson?.completed.length ?? 0 });
      if (active.current) setSaved(true);
    } catch { if (active.current) setError('Chưa lưu được bài. Em thử lại nhé.'); }
    finally { if (active.current) setSaving(false); }
  };
  const edit = (field: 'problem' | 'work') => {
    cancel(); setError(''); setEditing(field); setLesson(null); setSaved(false); setReviewFocused(false);
    if (field === 'problem') setProblemConfirmed(false); else { setWorkConfirmed(false); setWorkLines([]); setWorkImageCurrent(false); }
  };
  const sourceRows = workReviewLines(work);
  // A changed/flattened transcription cannot reuse physical boxes from an older image reading.
  const boundLines = workLines.length === sourceRows.length && workLines.every((line, index) => trimWorkReviewLine(line.text) === sourceRows[index] && !line.division)
    ? workLines : sourceRows.map(text => ({ text, box: null, uncertain: text.includes('[?]') }));
  // The pupil has explicitly checked these readable symbols; keep the original OCR flags in workLines.
  const evidenceLines = workConfirmed && !work.includes('[?]') ? boundLines.map(line => ({ ...line, uncertain: false })) : boundLines;

  const preparing = busy === 'read' || busy === 'lesson' ? busy : finishing?.kind;
  if (preparing) return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <View style={styles.preparing} testID={preparing === 'read' ? 'lesson-reading-screen' : 'lesson-preparation-screen'} accessibilityLiveRegion="polite">
      <RecognitionProgress
        title={preparing === 'read' ? 'Mình đang đọc bài của em' : 'Chuẩn bị các bước học'}
        description={preparing === 'read' ? 'Giữ cả đề và phần bài làm để cùng học nhé.' : 'Mỗi bước sẽ có một việc rõ ràng để em thử.'}
        steps={preparing === 'read' ? ['Ảnh đã chọn', 'Đọc đề và bài làm', 'Mở phần kiểm tra'] : ['Đề đã xác nhận', 'Chuẩn bị các bước học', 'Mở bài học']}
        activeStep={1}
        complete={!!finishing}
        onComplete={() => setFinishing(previous => previous?.id === finishing?.id ? null : previous)}
        imageUri={preparing === 'read' ? imageUri : undefined}
        onCancel={cancel} cancelLabel={preparing === 'read' ? 'Dừng chờ, giữ ảnh' : 'Dừng chờ'} />
    </View>
  </SafeAreaView>;

  return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <View style={[styles.header, spacious && styles.headerWide]}><AppHeader title={reviewFocused ? 'Bài làm của em' : lesson ? 'Bài học' : division ? 'Kiểm tra phép chia' : work ? 'Cùng xem bài làm' : 'Cùng em tìm cách giải'} showBack
      rightIcon="calculator-outline" rightAccessibilityLabel="Mở máy tính bỏ túi" onRightPress={() => setCalculatorOpen(true)} /></View>
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
    <View style={[styles.learningBody, spacious && styles.learningBodyWide]}>
    {spacious && lesson ? <ScrollView style={styles.lessonSidebar} contentContainerStyle={styles.lessonSidebarContent} showsVerticalScrollIndicator={false}>
      <Text style={styles.sidebarEyebrow}>HÀNH TRÌNH CỦA EM</Text><Text style={styles.sidebarTitle}>Hiểu từng bước</Text>
      {lesson.outline.map((title, index) => <View key={`${index}:${title}`} style={[styles.outlineRow, index === lesson.stepIndex && styles.outlineCurrent]} accessible
        accessibilityLabel={`Bước ${index + 1}: ${title}. ${index < lesson.stepIndex ? 'Đã hoàn thành' : index === lesson.stepIndex ? 'Đang học' : 'Sắp tới'}`}>
        <View style={[styles.outlineNumber, index <= lesson.stepIndex && styles.outlineNumberActive]}>{index < lesson.stepIndex ? <Ionicons name="checkmark" size={16} color="#FFF" /> : <Text style={[styles.outlineNumberText, index === lesson.stepIndex && { color: '#FFF' }]}>{index + 1}</Text>}</View>
        <Text style={[styles.outlineText, index === lesson.stepIndex && { color: COLORS.primaryDark }]}>{title}</Text>
      </View>)}
      <AppIllustration source={MASCOT} style={styles.sidebarMascot} accessible={false} /><Text style={styles.sidebarCaption}>Cứ thử từng ý nhỏ. Sao nhỏ luôn ở đây cùng em.</Text>
    </ScrollView> : null}
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      {lesson && !editing && problem ? <View style={[styles.reference, spacious && styles.referenceWide]}>
        <LessonProblem key={lesson.sessionId} problem={problem} imageUri={problemImage} onEdit={() => { setTool(null); edit('problem'); }} />
      </View> : null}
      <ScrollView ref={scroll} testID="lesson-working-area" contentContainerStyle={[styles.content, spacious && styles.contentWide]} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        {reviewFocused && !lesson ? <Pressable accessibilityRole="button" accessibilityLabel="Xem lại đề và bài làm" style={styles.reviewBack} onPress={() => setReviewFocused(false)}>
          <Ionicons name="chevron-back" size={18} color={COLORS.primaryDark} /><Text style={styles.link}>Xem lại đề và bài làm</Text></Pressable> : null}
        {!lesson && !reviewFocused ? <LinearGradient colors={['#EEE7FF', '#F5F0FF']} style={styles.hero}>
          <View style={styles.flex}><Text style={styles.eyebrow}>HỌC CÙNG MATHVISIONKID</Text>
            <Text style={styles.title}>{division ? 'Cùng kiểm tra phép chia' : !problem && work ? 'Thêm đề, hiểu trọn bài' : work ? 'Cùng nhìn lại bài em làm' : 'Hiểu cách làm, tự tìm lời giải'}</Text>
            <Text style={styles.body}>{division ? 'Đối chiếu với ảnh → kiểm tra → tự sửa chỗ chưa đúng.' : !problem && work ? 'Mình giữ bài em đã viết. Có đề gốc, mình mới đối chiếu được cách làm.' : work ? 'Đọc đúng đề và bài làm → nhận xét từng dòng → em tự sửa và kiểm tra lại.' : 'Hiểu đề → chọn cách làm → tự tính → kiểm tra lại.'}</Text></View>
          <AppIllustration source={MASCOT} style={styles.mascot} accessible={false} />
        </LinearGradient> : null}

        {error ? <View style={styles.errorCard} accessibilityRole="alert"><Text style={styles.error}>{error}</Text>
          {expired ? <AppButton title="Đăng nhập lại" onPress={() => router.push('/login' as any)} /> : null}
        </View> : null}

        {!!imageUri && !photoAllowed ? <View style={styles.card}><Text style={styles.body}>Em kiểm tra thông tin cá nhân trên ảnh trước nhé.</Text>
          <AppButton title="Kiểm tra thông tin cá nhân trên ảnh" onPress={() => router.replace('/privacy' as any)} /></View> : null}
        {photoAllowed && !reading ? <AppButton title="Đọc lại ảnh" variant="secondary" onPress={() => void inspectPhoto()} /> : null}

        {invalidPhoto ? <View style={styles.card}>
          <Text style={styles.heading}>{reading?.needsCrop ? 'Chọn một vùng nhỏ hơn nhé' : reading?.kind === 'MULTIPLE' ? 'Mỗi lần một bài nhé' : 'Mình chưa đọc rõ bài toán'}</Text>
          <Text style={styles.body}>{reading?.needsCrop ? 'Ảnh có nhiều nội dung. Em chia thành từng phần để mình đọc đủ, rồi cùng xem từng bài nhé.' : 'Em chọn trọn một bài, gồm lời văn, số và hình vẽ nếu có.'}</Text>
          <AppButton title="Chọn lại vùng bài toán" onPress={() => router.push('/crop' as any)} />
          <Pressable style={styles.linkButton} accessibilityRole="button" onPress={() => edit('problem')}><Text style={styles.link}>Em muốn nhập đề bằng chữ</Text></Pressable>
        </View> : null}

        {!!(workImage || problemImage) && !lesson && !division && !reviewFocused && <View style={styles.photos}>
          {problemImage ? <View style={styles.photoCard}><Image source={{ uri: problemImage }} style={styles.photo} resizeMode="contain" accessibilityLabel="Ảnh đề bài đã che thông tin" /><Text style={styles.caption}>Đề bài</Text></View> : null}
          {workImage && workImage !== problemImage ? <View style={styles.photoCard}><Image source={{ uri: workImage }} style={styles.photo} resizeMode="contain" accessibilityLabel={workImageCurrent ? 'Ảnh bài em đã làm' : 'Ảnh bài làm trước khi sửa bằng chữ'} /><Text style={styles.caption}>{workImageCurrent ? 'Bài em làm' : 'Ảnh trước khi sửa'}</Text></View> : null}
        </View>}

        {division && !editing && !lesson ? <DivisionReview division={division} imageUri={workImage || imageUri}
          uncertain={divisionLine?.uncertain ?? false} onChange={value => {
            const text = divisionText(value);
            const lines = workLines.map(line => line === divisionLine ? { ...line, division: value, text, box: null } : line);
            setWorkLines(lines); setWorkImageCurrent(false);
            setWork(lines.map(line => line.text).join('\n')); setWorkConfirmed(false); setSaved(false);
          }} /> : null}
        {division && workLines.some(line => !line.division) ? <View style={styles.card}>
          <Text style={styles.heading}>Nội dung đi kèm</Text>
          <Text style={styles.body}>{workLines.filter(line => !line.division).map(line => line.text).join('\n')}</Text>
        </View> : null}

        {!problem && work && !invalidPhoto && !division && editing !== 'problem' ? <View style={styles.card}>
          <Text style={styles.heading}>Cần thêm đề bài</Text>
          <Text style={styles.body}>Bài làm chưa cho biết đầy đủ câu hỏi và dữ kiện. Em chụp thêm đề để mình cùng kiểm tra nhé.</Text>
          <AppButton title="Chụp thêm đề bài" onPress={() => capture('ADD_PROBLEM')} icon={<Ionicons name="camera" size={20} color="white" />} />
          <Pressable style={styles.linkButton} accessibilityRole="button" accessibilityLabel="Nhập đề bài" onPress={() => edit('problem')}><Text style={styles.link}>Hoặc nhập đề bằng chữ</Text></Pressable>
        </View> : null}

        {editing || (!problem && !work && !imageUri) ? <View style={styles.card}>
          <Text style={styles.heading}>{editing === 'work' ? 'Chỗ em đã viết' : 'Đề bài của em'}</Text>
          <TextInput accessibilityLabel={editing === 'work' ? 'Nội dung bài làm' : 'Nội dung đề bài'} value={editing === 'work' ? work : problem}
            onChangeText={editing === 'work' ? setWork : setProblem} maxLength={editing === 'work' ? 6000 : 4000} multiline style={styles.input} placeholder="Nhập nội dung ở đây nhé…" />
          <AppButton title="Dùng nội dung này" disabled={(editing === 'work' ? work : problem).trim().length < 3} onPress={() => {
            if (editing === 'work') { setWorkLines([]); setUncertainWork(work.includes('[?]')); setWorkConfirmed(!work.includes('[?]')); }
            else setProblemConfirmed(!problem.includes('[?]'));
            setReading({ kind: work ? 'MIXED' : 'PROBLEM', problemText: problem, lines: [], needsProblem: !problem });
            setEditing(null);
          }} />
        </View> : null}

        {!!problem && !editing && !lesson && !reviewFocused ? <View style={styles.card}>
          <View style={styles.problemHeader}>
            <View style={styles.problemToggle}>
              <View style={styles.problemIcon}><Ionicons name="document-text-outline" size={21} color={COLORS.primaryDark} /></View>
              <Text style={[styles.problemTitle, styles.flex]}>Đề bài của em</Text>
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh đề bài" onPress={() => edit('problem')}
              style={({ pressed }) => [styles.problemEdit, pressed && styles.problemPressed]}><Ionicons name="create-outline" size={20} color={COLORS.primaryDark} /></Pressable>
          </View>
          <View style={styles.problemContent}><MathText style={styles.body}>{problem}</MathText></View>
          {!lesson ? <>
            {Platform.OS === 'web' && problem.includes('[?]') ? <Text style={styles.error} accessibilityRole="alert">Có chỗ chưa chắc trong đề. Em chọn chỉnh đề, đối chiếu với ảnh và bỏ dấu [?] sau khi sửa nhé.</Text> : null}
            <Text style={styles.body}>Em kiểm tra lời văn, các số và đơn vị. Nếu chưa giống ảnh, chọn chỉnh đề trước nhé.</Text>
            <Pressable accessibilityRole="checkbox" accessibilityLabel="Em đã kiểm tra đề bài và các số"
              aria-checked={problemConfirmed} accessibilityState={{ checked: problemConfirmed, disabled: !!busy || problem.includes('[?]') }}
              disabled={!!busy || problem.includes('[?]')} style={styles.confirm}
              onPress={() => setProblemConfirmed(value => !value)}>
              <Ionicons name={problemConfirmed ? 'checkbox' : 'square-outline'} size={26} color={COLORS.primaryDark} />
              <Text style={[styles.body, styles.flex]}>Em đã kiểm tra đề bài và các số</Text>
            </Pressable>
          </> : null}
          {problem.includes('[?]') ? <Text style={styles.error}>Có dữ kiện chưa rõ. Em chỉnh lại chỗ đánh dấu trước nhé.</Text> : !lesson && !busy ? <AppButton title={work ? 'Cùng hiểu và đối chiếu bài' : 'Bắt đầu từng bước'} onPress={start} disabled={expired || !!invalidPhoto || !problemConfirmed} /> : null}
          {!work && !lesson ? <Pressable style={styles.linkButton} accessibilityRole="button" accessibilityLabel="Chụp thêm bài làm" onPress={() => capture('ADD_WORK')}><Text style={styles.link}>Em đã làm rồi? Chụp thêm bài làm</Text></Pressable> : null}
        </View> : null}

        {!!work && !editing && !division && !lesson && !reviewFocused ? <View style={styles.workCard}>
          <Pressable style={[styles.row, styles.workToggle]} accessibilityRole="button" accessibilityLabel="Xem bài em đã viết" aria-expanded={showWork} onPress={() => setShowWork(v => !v)}>
            <Ionicons name="book-outline" size={21} color={COLORS.primaryDark} /><Text style={[styles.link, styles.flex]}>Bài em đã viết</Text><Ionicons name={showWork ? 'chevron-up' : 'chevron-down'} size={18} color={COLORS.primaryDark} />
          </Pressable>
          {uncertainWork && !workConfirmed ? <Text style={styles.body}>Có chỗ trong ảnh chưa đọc rõ. Em đối chiếu từng số và dấu phép tính trước khi dùng bài làm nhé.</Text> : null}
          {!workConfirmed && !lesson ? <Text style={styles.body}>Bài làm chưa được xác nhận. Mình có thể hướng dẫn từ đề đã kiểm tra; chỉ đối chiếu cách làm sau khi em xác nhận bài viết.</Text> : null}
          {showWork || (!workConfirmed && !lesson) ? <>
            {workImage ? <><Image source={{ uri: workImage }} style={styles.photo} resizeMode="contain" accessibilityLabel={workImageCurrent ? 'Ảnh bài em đã làm' : 'Ảnh bài làm trước khi sửa bằng chữ'} />
              {!workImageCurrent ? <Text style={styles.caption}>Ảnh trước khi sửa bằng chữ. Em chụp lại để ảnh khớp bài mới nhé.</Text> : null}</> : null}
            <MathText style={styles.body}>{work}</MathText>
            <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh chỗ chưa đọc đúng" style={styles.linkButton} onPress={() => edit('work')}><Text style={styles.link}>Chỉnh chỗ chưa đọc đúng</Text></Pressable>
            {!lesson ? <Pressable accessibilityRole="checkbox" accessibilityLabel="Em đã đối chiếu bài làm với ảnh"
              aria-checked={workConfirmed} accessibilityState={{ checked: workConfirmed, disabled: !!busy || work.includes('[?]') }}
              disabled={!!busy || work.includes('[?]')} style={styles.confirm} onPress={() => setWorkConfirmed(value => !value)}>
              <Ionicons name={workConfirmed ? 'checkbox' : 'square-outline'} size={26} color={COLORS.primaryDark} />
              <Text style={[styles.body, styles.flex]}>Em đã đối chiếu bài làm với ảnh</Text>
            </Pressable> : null}
            {work.includes('[?]') ? <Text style={styles.error}>Em sửa chỗ có dấu [?] trước khi xác nhận bài làm nhé.</Text> : null}
          </> : null}
        </View> : null}

        {problem && work && !editing && !division && !invalidPhoto && !lesson ? <StudentWorkReview
          problemText={problem} workText={work} imageUri={workImage} photoCurrent={workImageCurrent} lines={evidenceLines}
          enabled={problemConfirmed && workConfirmed && !problem.includes('[?]') && !work.includes('[?]')}
          disabled={!!busy || expired} onCaptureWork={() => capture('ADD_WORK')}
          onReviewReady={() => { setReviewFocused(true); requestAnimationFrame(() => scroll.current?.scrollTo({ y: 0, animated: false })); }}
          onSessionExpired={() => { setExpired(true); setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.'); }}
          onReviseWork={text => { cancel(); setReviewFocused(false); setWork(text); setWorkLines([]); setWorkImageCurrent(false); setWorkConfirmed(false); setUncertainWork(text.includes('[?]')); setShowWork(true); setSaved(false); }} /> : null}

        {lesson && !editing ? <>
          <View style={styles.progressRow}><View style={styles.rail} accessible accessibilityRole="progressbar" accessibilityLabel="Tiến trình bài học"
            accessibilityValue={{ min: 0, max: lesson.outline.length, now: lesson.stepIndex, text: `Đã hoàn thành ${lesson.stepIndex} trên ${lesson.outline.length} bước` }}>
            {lesson.outline.map((_, index) => <View key={index} style={[styles.railStep, index < lesson.stepIndex && styles.railActive]} />)}
          </View><Text style={styles.progressCount}>{Math.min(lesson.stepIndex + 1, lesson.outline.length)}/{lesson.outline.length}</Text></View>
          {lesson.preparingMath ? <Text style={styles.caption}>Em đọc đề trước nhé, phần hướng dẫn đang được chuẩn bị.</Text> : null}
          {lesson.status === 'CORRECT' && lesson.feedback && !reviewedStep ? <View style={styles.explanation}>
            <Text style={styles.caption}>BƯỚC TRƯỚC ĐÃ HOÀN THÀNH</Text><Text style={styles.feedback}>{lesson.feedback}</Text>
          </View> : null}
          {reviewedStep ? <View style={styles.card} accessibilityLiveRegion="polite" onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.eyebrow}>{reviewedStep.kind === 'UNDERSTAND' ? 'CÙNG HIỂU ĐỀ' : `ĐÃ KIỂM TRA BƯỚC ${lesson.stepIndex - (lesson.understandingSteps || 0)}`}</Text>
            <Text style={styles.feedback}>{lesson.feedback}</Text>
            <Text style={styles.heading}>{reviewedStep.kind === 'UNDERSTAND' ? 'Em đã hiểu điều này' : 'Viết vào bài giải'}</Text>
            {reviewedStep.expression ? <SolutionLine item={reviewedStep} /> : <Text style={styles.body}>{reviewedStep.answer}</Text>}
            {reviewedStep.kind === 'UNDERSTAND' && lesson.stepIndex === lesson.understandingSteps ? <ProblemSummary lesson={lesson} compact /> : null}
            <AppButton title={reviewedStep.kind === 'UNDERSTAND' && lesson.stepIndex === lesson.understandingSteps ? 'Bắt đầu giải' : 'Tiếp tục bước tiếp theo'} onPress={() => { setReviewedStep(null); scroll.current?.scrollTo({ y: 0, animated: false }); }} />
          </View> : step ? <View style={[styles.card, styles.activeStep]} accessibilityLiveRegion="polite" onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.eyebrow}>{step.kind === 'UNDERSTAND' ? 'HIỂU ĐỀ' : 'CÙNG GIẢI'} · BƯỚC {step.kind === 'UNDERSTAND' ? lesson.stepIndex + 1 : lesson.stepIndex + 1 - (lesson.understandingSteps || 0)} / {step.kind === 'UNDERSTAND' ? lesson.understandingSteps : lesson.outline.length - (lesson.understandingSteps || 0)}</Text>
            <View style={styles.stepPrompt}><Text style={styles.heading}>{step.title}</Text>
            {step.kind === 'UNDERSTAND' ? <Text style={styles.stepCaption}>Hiểu đề trước khi tính</Text> : <Text style={styles.stepCaption}>Cùng giải bài toán này nhé!</Text>}</View>
            {step.kind === 'UNDERSTAND' ? <MathText style={styles.body}>{step.explanation}</MathText> : null}
            {step.workExcerpt ? <View style={styles.workCard}><Text style={styles.caption}>TRONG BÀI EM VIẾT</Text><MathText style={styles.body}>{step.workExcerpt}</MathText></View> : null}
            <View onLayout={event => { questionPosition.current = event.nativeEvent.layout.y; }}><MathText style={styles.question}>{step.question}</MathText></View>
            {step.expression && hintCount > 0 ? <LessonCalculation expression={step.expression} /> : null}
            {step.kind !== 'UNDERSTAND' ? <View style={styles.stepNote}><Ionicons name="bulb-outline" size={18} color="#AC8C42" /><View style={styles.flex}><MathText style={styles.stepNoteText}>{step.explanation}</MathText></View></View> : null}
            {step.choices.length ? step.choices.map((choice, index) => <Pressable key={choice} ref={index === 0 ? firstChoice : undefined} accessibilityRole="button" accessibilityLabel={choice} disabled={!!busy || expired}
              aria-pressed={attempt === choice} accessibilityState={Platform.OS === 'web' ? { disabled: !!busy || expired } : { selected: attempt === choice, disabled: !!busy || expired }}
              onFocus={() => setFocusedChoice(choice)} onBlur={() => setFocusedChoice(null)}
              style={[styles.choice, attempt === choice && styles.choiceSelected, focusedChoice === choice && styles.choiceFocused]} onPress={() => { setAttempt(choice); setAnswerEdited(true); answer(choice); }}>
              <Text style={styles.choiceText}>{choice}</Text><Ionicons name="chevron-forward" size={18} color={COLORS.primaryDark} />
            </Pressable>) : <><View style={styles.answerRow}>
              {fractionInput ? <View style={styles.fractionAnswer}>
                <TextInput ref={answerInput} style={styles.fractionNumber} accessibilityLabel="Tử số câu trả lời" value={attempt.split('/')[0]} keyboardType="numbers-and-punctuation" maxLength={13}
                  placeholder="Tử số" editable={!busy && !expired} onChangeText={value => { setAttempt(`${value}/${attempt.split('/')[1] || ''}`); setAnswerEdited(true); }} />
                <View style={styles.fractionBar} />
                <TextInput style={styles.fractionNumber} accessibilityLabel="Mẫu số câu trả lời" value={attempt.split('/')[1] || ''} keyboardType="number-pad" maxLength={12}
                  placeholder="Mẫu số" editable={!busy && !expired} onChangeText={value => { setAttempt(`${attempt.split('/')[0]}/${value}`); setAnswerEdited(true); }} />
              </View> : <TextInput ref={answerInput} style={styles.numberInput} accessibilityLabel="Câu trả lời của em" value={attempt} onChangeText={value => { setAttempt(value); setAnswerEdited(true); }} keyboardType="decimal-pad"
                maxLength={30} placeholder="Em tính được…" placeholderTextColor={COLORS.textMuted} editable={!busy && !expired} onSubmitEditing={() => answer(attempt)} />
              }
              <Text style={styles.unit}>{step.unit}</Text>
              {step.expression ? <Pressable style={styles.fractionToggle} accessibilityRole="button" accessibilityLabel={fractionInput ? 'Nhập số thường' : 'Nhập kết quả phân số'} disabled={!!busy || expired}
                  onPress={() => { setFractionInput(value => !value); setAttempt(''); setAnswerEdited(true); }}>
                  <Text style={styles.link}>{fractionInput ? '123' : 'a/b'}</Text>
                </Pressable> : null}</View>
              {fractionInput ? <Text style={styles.caption}>Em nhập tử và mẫu; không làm tròn số thập phân.</Text> : null}
              <AppButton title="Kiểm tra bước này" style={styles.stepButton} onPress={() => answer(attempt)} disabled={!attempt.trim() || (fractionInput && !/^-?\d+\/[1-9]\d*$/.test(attempt)) || !!busy || expired} loading={busy === 'answer'} /></>}
            <AppButton title={hintExhausted ? 'Đã mở đủ gợi ý bước này' : hintCount ? 'Gợi ý rõ hơn' : 'Gợi ý cách làm bước này'} style={styles.stepButton} variant="secondary" onPress={() => answer('', true)} disabled={hintExhausted || !!busy || expired} />
            {hintExhausted ? <Text style={styles.caption}>Em đọc lại gợi ý rồi thử trả lời. Gợi ý rõ hơn vẫn được giữ ở đây.</Text> : null}
            {hintText ? <View style={styles.hintCard}>
              <MathText style={styles.stepNoteText}>{hintText}</MathText>
              {step.kind === 'UNDERSTAND' || /[+\-−×*÷/:]/.test(step.expression) ? <AppButton title="Em muốn hiểu gợi ý rõ hơn" variant="ghost" onPress={() => setTool('hint')} /> : null}
            </View> : null}
            {lesson.status === 'TRY_AGAIN' && !answerEdited && lesson.feedback ? <Text accessibilityRole="alert" style={styles.error}>{lesson.feedback}</Text> : null}
          </View> : <View style={styles.card} onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.heading}>Bài giải</Text><Text style={styles.body}>Đây là các bước em đã tự tính và kiểm tra. Em có thể viết lại vào vở.</Text>
            {lesson.feedback ? <Text style={styles.feedback}>{lesson.feedback}</Text> : null}
            {lesson.completed.filter(item => item.expression).map((item, index) => <SolutionLine key={index} item={item} />)}
            {lesson.conclusion ? <MathText style={styles.question}>{lesson.conclusion}</MathText> : null}
            {work ? <Text style={styles.body}>Em đối chiếu những bước vừa học với bài trong ảnh. Các phép tính vừa nhập đã được kiểm tra; nét chữ và hình vẽ vẫn cần nhìn lại.</Text> : null}
          </View>}
        </> : null}
        {lesson && !editing ? <View style={styles.tools}>
          {([['audio', 'volume-high-outline', 'Nghe giảng'], ['ask', 'mic-outline', 'Hỏi bài'], ['menu', 'ellipsis-horizontal', 'Xem thêm']] as const).map(([value, icon, label]) => <Pressable
            key={value} accessibilityRole="button" accessibilityLabel={label} disabled={!!busy || expired} accessibilityState={{ disabled: !!busy || expired }} style={({ pressed }) => [styles.tool, pressed && { backgroundColor: '#F0E8FF' }, (!!busy || expired) && { opacity: .5 }]} onPress={() => setTool(value)}>
            <Ionicons name={icon} size={22} color={COLORS.primaryDark} accessible={false} /><Text style={styles.toolLabel}>{label}</Text>
          </Pressable>)}
        </View> : null}
        {lesson && !step && !reviewedStep && !editing ? <AppButton title={work ? 'Chụp lại bài làm để nhận xét' : 'Chụp bài em đã làm để nhận xét'} variant="secondary"
          onPress={() => capture('ADD_WORK')} disabled={expired} /> : null}
        {error && problem && !lesson && !expired ? <AppButton title="Bắt đầu lại bài học" variant="secondary" onPress={start} /> : null}
        {!!(problem || work) && (!lesson || (!step && !reviewedStep)) && !editing && !busy ? <AppButton title={saved ? 'Đã lưu bài của em' : 'Lưu bài để học tiếp'} variant="secondary" loading={saving} disabled={saved || saving} onPress={() => void archive()} /> : null}
        {!lesson ? <Pressable style={styles.linkButton} accessibilityRole="button" accessibilityLabel="Chụp bài khác" onPress={() => capture()}><Text style={styles.link}>Chụp bài khác</Text></Pressable> : null}
      </ScrollView>
    </KeyboardAvoidingView></View>
    {lesson && tool && !busy && !expired && !editing ? <LessonSheet title={{ audio: 'Nghe giảng', ask: 'Hỏi bài', menu: 'Em cần gì thêm?', work: 'Bài em đã viết', summary: 'Tóm tắt đề', visual: 'Cùng nhìn phân số', hint: 'Cùng hiểu gợi ý' }[tool]} onClose={() => setTool(null)}>
      {tool === 'hint' && step ? <><MathText style={styles.body}>{hintText}</MathText>
        <HintCheckIn key={`${lesson.sessionId}:${lesson.stepIndex}:${hintCount}`} expression={step.expression} reading={step.kind === 'UNDERSTAND'} depth={hintCount}
          onReady={() => { setTool(null); if (step.choices.length) firstChoice.current?.focus(); else answerInput.current?.focus(); }} /></> : null}
      {tool === 'audio' ? <LessonListening scope={JSON.stringify([owner, lesson.sessionId, lesson.stepIndex, lesson.revision, hintCount, !!reviewedStep])}
        sessionId={lesson.sessionId} revision={lesson.revision} stepIndex={Math.max(0, lesson.stepIndex - (reviewedStep || !step ? 1 : 0))} step={reviewedStep || step}
        onReturn={() => { setTool(null); if (step?.choices.length) firstChoice.current?.focus(); else answerInput.current?.focus(); }}
        paragraphs={narrationParts} /> : null}
      {tool === 'ask' ? <LessonQuestion onReturn={() => { setTool(null); if (step?.choices.length) firstChoice.current?.focus(); else answerInput.current?.focus(); }} key={`${owner}:${lesson.sessionId}:${lesson.revision}:${!!reviewedStep}`} scope={`${owner}:${lesson.sessionId}:${lesson.revision}:${!!reviewedStep}`}
        sessionId={lesson.sessionId} revision={lesson.revision} stepIndex={Math.max(0, lesson.stepIndex - (reviewedStep || !step ? 1 : 0))} /> : null}
      {tool === 'summary' ? <ProblemSummary lesson={lesson} compact /> : null}
      {tool === 'work' ? <>{workImage ? <Image source={{ uri: workImage }} style={[styles.photo, { height: 220 }]} resizeMode="contain" accessibilityLabel={workImageCurrent ? 'Ảnh bài em đã làm' : 'Ảnh bài làm trước khi sửa bằng chữ'} /> : null}
        {!workConfirmed ? <Text style={styles.error}>Bài làm chưa được xác nhận; mình đang hướng dẫn từ đề đã kiểm tra. Có chỗ chưa đọc rõ, em đối chiếu lại với ảnh nhé.</Text> : null}
        <MathText style={styles.body}>{work}</MathText>
        <AppButton title="Chỉnh chỗ chưa đọc đúng" variant="secondary" onPress={() => { setTool(null); edit('work'); }} /></> : null}
      {tool === 'visual' ? <><Text style={styles.caption}>HÌNH {visualIndex + 1} / {fractionsInProblem(problem).length}</Text>
        {fractionsInProblem(problem)[visualIndex] ? <FractionExplorer key={visualIndex} {...fractionsInProblem(problem)[visualIndex]} label="Phân số trong đề bài của em" /> : null}
        <View style={styles.row}><AppButton title="Hình trước" variant="secondary" disabled={visualIndex === 0} onPress={() => setVisualIndex(value => value - 1)} />
          <AppButton title="Hình tiếp" variant="secondary" disabled={visualIndex >= fractionsInProblem(problem).length - 1} onPress={() => setVisualIndex(value => value + 1)} /></View></> : null}
      {tool === 'menu' ? <>
        {work ? <AppButton title="Xem bài em đã viết" variant="secondary" onPress={() => setTool('work')} /> : null}
        {lesson.understandingSteps === 3 && lesson.stepIndex >= 2 ? <AppButton title="Xem lại tóm tắt đề" variant="secondary" onPress={() => setTool('summary')} /> : null}
        {step?.kind !== 'UNDERSTAND' && fractionsInProblem(problem).length ? <AppButton title="Xem hình phân số" variant="secondary" onPress={() => { setVisualIndex(0); setTool('visual'); }} /> : null}
        <AppButton title={saved ? 'Đã lưu bài của em' : 'Lưu bài để học tiếp'} variant="secondary" disabled={saved || saving} loading={saving} onPress={() => void archive()} />
        <AppButton title="Chụp bài em đã làm để nhận xét" variant="secondary" onPress={() => { setTool(null); capture('ADD_WORK'); }} />
        <AppButton title="Chụp bài khác" variant="ghost" onPress={() => { setTool(null); capture(); }} /></> : null}
    </LessonSheet> : null}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  preparing: { flex: 1, justifyContent: 'center', padding: 20 },
  header: { width: '100%', maxWidth: 740, alignSelf: 'center' }, headerWide: { maxWidth: 1180 },
  learningBody: { flex: 1, width: '100%', alignSelf: 'center' }, learningBodyWide: { maxWidth: 1180, flexDirection: 'row', gap: 10, paddingHorizontal: 18 },
  lessonSidebar: { width: 244, flexGrow: 0, flexShrink: 0, marginVertical: 18, borderRadius: 24, backgroundColor: '#F0EAFB', borderWidth: 1, borderColor: '#E4D9F8' },
  lessonSidebarContent: { padding: 22 }, sidebarEyebrow: { fontFamily: FONTS.extraBold, fontSize: 10, letterSpacing: 1.2, color: '#9581B4' }, sidebarTitle: { fontFamily: FONTS.extraBold, fontSize: 22, color: COLORS.textPrimary, marginTop: 9, marginBottom: 25 },
  outlineRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 15, paddingHorizontal: 8, borderRadius: 13, marginBottom: 7 }, outlineCurrent: { backgroundColor: '#FFF' },
  outlineNumber: { width: 29, height: 29, borderRadius: 15, backgroundColor: '#E2D7F4', alignItems: 'center', justifyContent: 'center' }, outlineNumberActive: { backgroundColor: '#8A60E9' }, outlineNumberText: { fontFamily: FONTS.extraBold, color: '#8C72B0', fontSize: 13 }, outlineText: { flex: 1, fontFamily: FONTS.bold, fontSize: 13, lineHeight: 20, color: '#8B7B9E' },
  sidebarMascot: { height: 142, width: '100%', marginTop: 24 }, sidebarCaption: { fontFamily: FONTS.regular, color: '#847399', fontSize: 13, lineHeight: 21, textAlign: 'center', marginTop: 15 },
  screen: { flex: 1, backgroundColor: COLORS.background }, flex: { flex: 1 },
  content: { flexGrow: 1, padding: 16, paddingBottom: 24, gap: 12, width: '100%', maxWidth: 680, alignSelf: 'center' }, contentWide: { maxWidth: 820, paddingHorizontal: 24 },
  reference: { width: '100%', maxWidth: 680, alignSelf: 'center', paddingHorizontal: 16, paddingTop: 4, paddingBottom: 0 }, referenceWide: { maxWidth: 820, paddingHorizontal: 24 },
  tools: { flexDirection: 'row', gap: 8, padding: 6, borderRadius: 20, backgroundColor: '#F1EAFB' },
  tool: { flex: 1, minHeight: 52, justifyContent: 'center', alignItems: 'center', gap: 4, borderRadius: 14, backgroundColor: '#FFFFFF' },
  toolLabel: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark },
  hero: { padding: 22, borderRadius: 26, flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderColor: '#E8DEF7', minHeight: 181 },
  mascot: { width: 94, height: 112 }, eyebrow: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold, fontSize: 11, letterSpacing: 1 },
  title: { fontSize: 23, lineHeight: 29, fontFamily: FONTS.extraBold, color: COLORS.textPrimary, marginVertical: 8 },
  heading: { fontSize: 17, lineHeight: 23, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  stepPrompt: { borderRadius: 12, padding: 12, gap: 3, backgroundColor: '#F1EAFF' }, stepCaption: { fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 18, color: COLORS.textSecondary },
  body: { fontSize: 14, lineHeight: 21, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  card: { backgroundColor: COLORS.surface, borderRadius: 18, padding: 14, gap: 12, borderWidth: 1, borderColor: '#EAE2F7', ...SHADOWS.small },
  activeStep: { gap: 10 }, stepNote: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, borderRadius: 13, backgroundColor: '#FFF9ED', padding: 10 },
  reviewBack: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 7 },
  stepNoteText: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: '#79698C' }, stepButton: { minHeight: 48, paddingVertical: 11, borderRadius: 16 },
  errorCard: { backgroundColor: '#FFF3ED', padding: 16, borderRadius: 18, gap: 12 },
  error: { color: '#963E22', fontSize: 15, lineHeight: 22, fontFamily: FONTS.semiBold },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  problemHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  problemToggle: { flex: 1, minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 14 },
  problemIcon: { width: 40, height: 40, borderRadius: 13, backgroundColor: COLORS.surfaceSubdued, alignItems: 'center', justifyContent: 'center' },
  problemTitle: { fontSize: 17, lineHeight: 23, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  problemEdit: { width: 48, height: 48, borderRadius: 15, borderWidth: 1, borderColor: '#E8E1F4', alignItems: 'center', justifyContent: 'center' },
  problemPressed: { backgroundColor: COLORS.surfaceSubdued },
  problemContent: { borderTopWidth: 1, borderColor: '#EEE8F7', paddingTop: 14 },
  photos: { flexDirection: 'row', gap: 12 }, photoCard: { flex: 1, backgroundColor: COLORS.surface, borderRadius: 18, padding: 8, gap: 5 },
  photo: { width: '100%', height: 120, borderRadius: 12, backgroundColor: '#F1EEF8' },
  caption: { fontSize: 12, color: COLORS.textSecondary, fontFamily: FONTS.bold },
  link: { fontSize: 15, lineHeight: 22, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  linkButton: { minHeight: 44, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 8 },
  input: { minHeight: 130, borderRadius: 16, padding: 16, backgroundColor: '#F8F5FF', borderWidth: 1, borderColor: '#D7CDF2', fontFamily: FONTS.regular, fontSize: 16, color: COLORS.textPrimary, textAlignVertical: 'top' },
  workCard: { backgroundColor: '#F0EBFC', padding: 16, borderRadius: 18, gap: 10 },
  workToggle: { minHeight: 48 },
  confirm: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 12 },
  progressRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 4 }, progressCount: { color: '#9D8EB4', fontFamily: FONTS.bold, fontSize: 13 },
  rail: { flex: 1, flexDirection: 'row', gap: 3, padding: 4, borderRadius: 10, backgroundColor: '#E9F6EF' }, railStep: { flex: 1, height: 7, borderRadius: 4, backgroundColor: '#DCEEE5' },
  railActive: { backgroundColor: '#6CCF99' },
  question: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 23 },
  expression: { backgroundColor: '#F1EBFF', borderRadius: 18, padding: 18 },
  expressionText: { fontSize: 24, lineHeight: 34, color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  choice: { minHeight: 48, borderRadius: 13, padding: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1.5, borderColor: '#DDD4F5', backgroundColor: '#FAF8FF' },
  choiceSelected: { backgroundColor: '#E8DEFF', borderColor: COLORS.primary }, choiceText: { flex: 1, marginRight: 8, color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 15, lineHeight: 21 },
  choiceFocused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed', borderWidth: 2 },
  answerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, alignItems: 'center' }, numberInput: { flex: 1, minWidth: 120, minHeight: 58, borderWidth: 1.5, borderColor: '#D7CDF2', backgroundColor: '#FAF8FF', borderRadius: 16, padding: 16, fontFamily: FONTS.bold, fontSize: 18, color: COLORS.textPrimary },
  fractionAnswer: { flex: 1, minWidth: 120, maxWidth: 300, borderWidth: 1.5, borderColor: '#D7CDF2', backgroundColor: '#FAF8FF', borderRadius: 16, padding: 12, gap: 4 },
  fractionNumber: { minHeight: 48, textAlign: 'center', fontFamily: FONTS.bold, fontSize: 20, color: COLORS.textPrimary },
  fractionBar: { height: 2, backgroundColor: COLORS.primaryDark, marginHorizontal: 16 },
  fractionToggle: { minWidth: 44, minHeight: 44, padding: 8, justifyContent: 'center', alignItems: 'center', borderRadius: 12, borderWidth: 1, borderColor: '#E3D8F6', backgroundColor: '#F4EEFF' },
  unit: { flexShrink: 1, maxWidth: '100%', color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 19 },
  explanation: { backgroundColor: '#E9F5EF', padding: 16, borderRadius: 16 }, feedback: { color: '#226A51', fontFamily: FONTS.bold, fontSize: 15, lineHeight: 23 },
  hintCard: { backgroundColor: '#F4EEFF', borderWidth: 1, borderColor: '#D7CDF2', padding: 16, borderRadius: 16, gap: 10 },
  guidanceCard: { backgroundColor: '#F8F6FF', borderWidth: 1, borderColor: '#E0D8FA', padding: 16, borderRadius: 16, gap: 14 },
  guidanceItem: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  guidanceNumber: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#EAE2FF', color: COLORS.primaryDark, textAlign: 'center', lineHeight: 28, fontFamily: FONTS.bold },
  completedStep: { gap: 8, paddingVertical: 12, borderBottomWidth: 1, borderColor: '#ECE6F5' },
});
