import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Image, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { ImageDraft, recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';
import { divisionText, savedDivision, LessonResponse, NotebookRead, TutorService } from '../../features/tutoring/api/TutorService';
import { DivisionReview } from '../../features/tutoring/DivisionReview';
import { AuthContext } from '../../context/AuthContext';
import { saveLesson } from '../../features/tutoring/learningHistory';
import { MathText } from '../../components/domain/MathText';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';

const MASCOT = require('../../../assets/illustrations/mathvision-star.png');

export default function MathGuideScreen() {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  const params = useLocalSearchParams<{ problemText?: string; workText?: string; lessonId?: string; reflection?: string }>();
  const supplied = typeof params.problemText === 'string' ? params.problemText.slice(0, 4000) : '';
  const suppliedWork = typeof params.workText === 'string' ? params.workText.slice(0, 6000) : '';
  const [draft] = useState(() => supplied || suppliedWork ? null : recognitionDraftStore.getDraft());
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
  const [problemImage, setProblemImage] = useState(context?.problemImageUri || '');
  const [uncertainWork, setUncertainWork] = useState(context?.uncertainWork || false);
  const [problemConfirmed, setProblemConfirmed] = useState(context?.problemConfirmed === true);
  const [workConfirmed, setWorkConfirmed] = useState(context?.workConfirmed === true);
  const [lesson, setLesson] = useState<LessonResponse | null>(null);
  const [attempt, setAttempt] = useState('');
  const [answerEdited, setAnswerEdited] = useState(false);
  const [hintCount, setHintCount] = useState(0);
  const [fractionInput, setFractionInput] = useState(false);
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [busy, setBusy] = useState<'read' | 'lesson' | 'answer' | null>(null);
  const [error, setError] = useState('');
  const [expired, setExpired] = useState(false);
  const [editing, setEditing] = useState<'problem' | 'work' | null>(null);
  const [showWork, setShowWork] = useState(false);
  const [showProblem, setShowProblem] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lessonId] = useState(() => context?.lessonId || (typeof params.lessonId === 'string' ? params.lessonId : `lesson_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`));
  const requestId = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const running = useRef(false);
  const active = useRef(true);
  const initialized = useRef(false);
  const scroll = useRef<ScrollView>(null);
  const lessonPosition = useRef(0);
  const invalidPhoto = reading && ['MULTIPLE', 'UNREADABLE'].includes(reading.kind);
  const divisionLines = reading?.lines.filter(line => line.division) ?? [];
  const divisionLine = !invalidPhoto && divisionLines.length === 1 ? divisionLines[0] : null;
  const division = divisionLine?.division;
  const step = lesson?.step;
  const lessonSessionId = lesson?.sessionId;
  const lessonStepIndex = lesson?.stepIndex;
  useEffect(() => { setAnswerEdited(false); setHintCount(0); setFractionInput(false); }, [lessonSessionId, lessonStepIndex]);
  useEffect(() => {
    if (!lessonSessionId) return;
    const frame = requestAnimationFrame(() => scroll.current?.scrollTo({ y: Math.max(0, lessonPosition.current - 12), animated: false }));
    return () => cancelAnimationFrame(frame);
  }, [lessonSessionId, lessonStepIndex]);
  const cancel = () => {
    requestId.current += 1; controller.current?.abort(); controller.current = null; running.current = false; setBusy(null);
  };
  const failureMessage = useCallback((failure: any) => {
    if (failure?.response?.status === 401) {
      setExpired(true); setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.');
    } else if ([409, 410].includes(failure?.response?.status)) {
      setLesson(null); setError('Bài học đã hết phiên. Đề và bài làm vẫn ở đây; em bắt đầu lại nhé.');
    } else if ([400, 422].includes(failure?.response?.status)) {
      setError('Đề bài còn thiếu hoặc có chỗ chưa rõ. Em kiểm tra lại lời văn, số và câu hỏi nhé.');
    } else if (failure?.response?.status === 503) {
      setError('Mình chưa chuẩn bị được hướng dẫn cho bài này lúc này. Bài của em vẫn ở đây; em kiểm tra đề đầy đủ rồi thử lại nhé.');
    } else setError('Chưa kết nối được lúc này. Bài của em vẫn ở đây, em thử lại nhé.');
  }, []);
  const run = useCallback(async <T,>(kind: 'read' | 'lesson' | 'answer', task: (signal: AbortSignal) => Promise<T>, apply: (value: T) => void) => {
    if (running.current || expired) return;
    const id = ++requestId.current; const abort = new AbortController();
    controller.current = abort; running.current = true; setBusy(kind); setError('');
    try {
      const result = await task(abort.signal);
      if (active.current && id === requestId.current) apply(result);
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
        setWork(text); setWorkImage(imageUri); setUncertainWork(result.lines.some(row => row.uncertain)); setWorkConfirmed(false);
      } else {
        setProblem(draft?.problemText || result.problemText);
        setProblemConfirmed(false); setWorkConfirmed(false);
        setWork(text); setUncertainWork(workRead && result.lines.some(row => row.uncertain));
        if (workRead) setWorkImage(imageUri);
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
        lessonContext: { purpose, problemText: problem, workText: work, workImageUri: workImage, problemImageUri: problemImage,
          lessonId, uncertainWork, problemConfirmed, workConfirmed } };
      recognitionDraftStore.setDraft(pending);
    } else recognitionDraftStore.clearDraft();
    router.push({ pathname: '/camera' as any, params: { mode: 'MATH_TUTOR' } });
  };
  const start = () => {
    if (problem.trim().length < 3 || problem.includes('[?]') || !problemConfirmed) return;
    const confirmedWork = workConfirmed && !work.includes('[?]') ? work : '';
    void run('lesson', signal => TutorService.startLesson(problem.trim(), confirmedWork,
      { problemConfirmed, workConfirmed: !!confirmedWork }, signal), result => {
      setLesson(result); setAttempt(''); setAnswerEdited(false); setShowProblem(false); setSaved(false);
    });
  };
  const answer = (value: string, hint = false) => {
    if (!lesson) return;
    void run('answer', signal => TutorService.answerLesson(lesson, value, hint, signal), result => {
      setLesson(result);
      setAnswerEdited(false);
      if (hint) setHintCount(value => value + 1);
      if (result.stepIndex !== lesson.stepIndex) setAttempt('');
      setSaved(false);
    });
  };
  const archive = async () => {
    if (saving || (!problem.trim() && !work)) return;
    setSaving(true);
    try {
      await saveLesson(owner, { id: lessonId, timestamp: Date.now(), problemText: problem, workText: work,
        reflection: lesson?.completed.filter(row => row.expression).map(row => `${row.title}: ${row.expression} = ${row.answer} ${row.unit}`).join('\n').slice(0, 2000) || '',
        reviewedSteps: lesson?.completed.length ?? 0 });
      if (active.current) setSaved(true);
    } catch { if (active.current) setError('Chưa lưu được bài. Em thử lại nhé.'); }
    finally { if (active.current) setSaving(false); }
  };
  const edit = (field: 'problem' | 'work') => {
    cancel(); setError(''); setEditing(field); setLesson(null); setSaved(false);
    if (field === 'problem') setProblemConfirmed(false); else setWorkConfirmed(false);
  };

  return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <AppHeader title={division ? 'Kiểm tra phép chia' : work ? 'Hiểu bài, kiểm tra cách làm' : 'Cùng em tìm cách giải'} showBack
      rightIcon="calculator-outline" rightAccessibilityLabel="Mở máy tính bỏ túi" onRightPress={() => setCalculatorOpen(true)} />
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      {busy === 'read' ? <RecognitionProgress title="Mình đang đọc bài của em" description="Giữ cả đề và phần bài làm để cùng học nhé." imageUri={imageUri} onCancel={cancel} cancelLabel="Dừng chờ, giữ ảnh" />
      : <ScrollView ref={scroll} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#EEE7FF', '#F5F0FF']} style={styles.hero}>
          <View style={styles.flex}><Text style={styles.eyebrow}>HỌC CÙNG MATHVISIONKID</Text>
            <Text style={styles.title}>{lesson?.status === 'COMPLETE' ? 'Em đã tự làm được!' : lesson?.topic || (division ? 'Cùng kiểm tra phép chia' : !problem && work ? 'Thêm đề, hiểu trọn bài' : 'Hiểu cách làm, tự tìm lời giải')}</Text>
            <Text style={styles.body}>{lesson?.goal || (division ? 'Đối chiếu với ảnh → kiểm tra → tự sửa chỗ chưa đúng.' : !problem && work ? 'Mình giữ bài em đã viết. Có đề gốc, mình mới đối chiếu được cách làm.' : 'Hiểu đề → chọn cách làm → tự tính → kiểm tra lại.')}</Text></View>
          <AppIllustration source={MASCOT} style={styles.mascot} accessible={false} />
        </LinearGradient>

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

        {!!(workImage || problemImage) && !lesson && !division && <View style={styles.photos}>
          {problemImage ? <View style={styles.photoCard}><Image source={{ uri: problemImage }} style={styles.photo} resizeMode="contain" accessibilityLabel="Ảnh đề bài đã che thông tin" /><Text style={styles.caption}>Đề bài</Text></View> : null}
          {workImage && workImage !== problemImage ? <View style={styles.photoCard}><Image source={{ uri: workImage }} style={styles.photo} resizeMode="contain" accessibilityLabel="Ảnh bài em đã làm" /><Text style={styles.caption}>Bài em làm</Text></View> : null}
        </View>}

        {division && !editing && !lesson ? <DivisionReview division={division} imageUri={workImage || imageUri}
          uncertain={divisionLine?.uncertain ?? false} onChange={value => {
            if (!reading) return;
            const text = divisionText(value);
            const lines = reading.lines.map(line => line === divisionLine ? { ...line, division: value, text } : line);
            setReading({ ...reading, lines });
            setWork(lines.map(line => line.text).join('\n')); setWorkConfirmed(false); setSaved(false);
          }} /> : null}
        {division && reading?.lines.some(line => !line.division) ? <View style={styles.card}>
          <Text style={styles.heading}>Nội dung đi kèm</Text>
          <Text style={styles.body}>{reading.lines.filter(line => !line.division).map(line => line.text).join('\n')}</Text>
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
            if (editing === 'work') { setUncertainWork(work.includes('[?]')); setWorkConfirmed(!work.includes('[?]')); }
            else setProblemConfirmed(!problem.includes('[?]'));
            setReading({ kind: work ? 'MIXED' : 'PROBLEM', problemText: problem, lines: [], needsProblem: !problem });
            setEditing(null);
          }} />
        </View> : null}

        {!!problem && !editing ? <View style={styles.card}>
          <View style={styles.problemHeader}>
            {lesson ? <Pressable accessibilityRole="button" accessibilityLabel="Xem lại đề bài" aria-expanded={showProblem}
              onPress={() => setShowProblem(v => !v)} style={({ pressed }) => [styles.problemToggle, pressed && styles.problemPressed]}>
              <View style={styles.problemIcon}><Ionicons name="document-text-outline" size={21} color={COLORS.primaryDark} /></View>
              <View style={styles.flex}><Text style={styles.problemTitle}>Đề bài của em</Text><Text style={styles.problemHint}>{showProblem ? 'Thu gọn đề bài' : 'Xem lại dữ kiện'}</Text></View>
              <View style={styles.problemChevron}><Ionicons name={showProblem ? 'chevron-up' : 'chevron-down'} size={20} color={COLORS.primaryDark} /></View>
            </Pressable> : <View style={styles.problemToggle}>
              <View style={styles.problemIcon}><Ionicons name="document-text-outline" size={21} color={COLORS.primaryDark} /></View>
              <Text style={[styles.problemTitle, styles.flex]}>Đề bài của em</Text>
            </View>}
            <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh đề bài" onPress={() => edit('problem')}
              style={({ pressed }) => [styles.problemEdit, pressed && styles.problemPressed]}><Ionicons name="create-outline" size={20} color={COLORS.primaryDark} /></Pressable>
          </View>
          {!lesson || showProblem ? <View style={styles.problemContent}><MathText style={styles.body}>{problem}</MathText></View> : null}
          {!lesson ? <>
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

        {!!work && !editing && !division ? <View style={styles.workCard}>
          <Pressable style={[styles.row, styles.workToggle]} accessibilityRole="button" accessibilityLabel="Xem bài em đã viết" aria-expanded={showWork} onPress={() => setShowWork(v => !v)}>
            <Ionicons name="book-outline" size={21} color={COLORS.primaryDark} /><Text style={[styles.link, styles.flex]}>Bài em đã viết</Text><Ionicons name={showWork ? 'chevron-up' : 'chevron-down'} size={18} color={COLORS.primaryDark} />
          </Pressable>
          {uncertainWork && !workConfirmed ? <Text style={styles.body}>Có chỗ trong ảnh chưa đọc rõ. Em đối chiếu từng số và dấu phép tính trước khi dùng bài làm nhé.</Text> : null}
          {!workConfirmed && !lesson ? <Text style={styles.body}>Bài làm chưa được xác nhận. Mình có thể hướng dẫn từ đề đã kiểm tra; chỉ đối chiếu cách làm sau khi em xác nhận bài viết.</Text> : null}
          {showWork || (!workConfirmed && !lesson) ? <>
            {workImage ? <Image source={{ uri: workImage }} style={styles.photo} resizeMode="contain" accessibilityLabel="Ảnh bài em đã làm" /> : null}
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

        {busy === 'lesson' ? <View style={styles.card}><RecognitionProgress title="Chuẩn bị các bước học" description="Mỗi bước sẽ có một việc rõ ràng để em thử." onCancel={cancel} cancelLabel="Dừng chờ" /></View> : null}
        {lesson && !editing ? <>
          <View style={styles.rail} accessible accessibilityRole="progressbar" accessibilityLabel="Tiến trình bài học"
            accessibilityValue={{ min: 0, max: lesson.outline.length, now: lesson.stepIndex, text: `Đã hoàn thành ${lesson.stepIndex} trên ${lesson.outline.length} bước` }}>
            {lesson.outline.map((_, index) => <View key={index} style={[styles.railStep, index <= lesson.stepIndex && styles.railActive]} />)}
          </View>
          {lesson.status === 'CORRECT' && lesson.feedback ? <View style={styles.explanation}>
            <Text style={styles.caption}>BƯỚC TRƯỚC ĐÃ HOÀN THÀNH</Text><Text style={styles.feedback}>{lesson.feedback}</Text>
          </View> : null}
          {step ? <View style={styles.card} accessibilityLiveRegion="polite" onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.eyebrow}>BƯỚC {lesson.stepIndex + 1} / {lesson.outline.length}</Text>
            <Text style={styles.heading}>{step.title}</Text>
            <View style={styles.explanation}><MathText style={styles.body}>{step.explanation}</MathText></View>
            {step.workExcerpt ? <View style={styles.workCard}><Text style={styles.caption}>TRONG BÀI EM VIẾT</Text><MathText style={styles.body}>{step.workExcerpt}</MathText></View> : null}
            <MathText style={styles.question}>{step.question}</MathText>
            {step.expression ? <View style={styles.expression}><MathText style={styles.expressionText}>{`${step.expression} = ?`}</MathText></View> : null}
            {step.choices.length ? step.choices.map(choice => <Pressable key={choice} accessibilityRole="button" accessibilityLabel={choice} disabled={!!busy || expired}
              style={[styles.choice, attempt === choice && styles.choiceSelected]} onPress={() => { setAttempt(choice); setAnswerEdited(true); answer(choice); }}>
              <Text style={styles.choiceText}>{choice}</Text><Ionicons name="chevron-forward" size={18} color={COLORS.primaryDark} />
            </Pressable>) : <><View style={styles.answerRow}>
              {fractionInput ? <View style={styles.fractionAnswer}>
                <TextInput style={styles.fractionNumber} accessibilityLabel="Tử số câu trả lời" value={attempt.split('/')[0]} keyboardType="numbers-and-punctuation" maxLength={13}
                  placeholder="Tử số" editable={!busy && !expired} onChangeText={value => { setAttempt(`${value}/${attempt.split('/')[1] || ''}`); setAnswerEdited(true); }} />
                <View style={styles.fractionBar} />
                <TextInput style={styles.fractionNumber} accessibilityLabel="Mẫu số câu trả lời" value={attempt.split('/')[1] || ''} keyboardType="number-pad" maxLength={12}
                  placeholder="Mẫu số" editable={!busy && !expired} onChangeText={value => { setAttempt(`${attempt.split('/')[0]}/${value}`); setAnswerEdited(true); }} />
              </View> : <TextInput style={styles.numberInput} accessibilityLabel="Câu trả lời của em" value={attempt} onChangeText={value => { setAttempt(value); setAnswerEdited(true); }} keyboardType="decimal-pad"
                maxLength={30} placeholder="Em tính được…" placeholderTextColor={COLORS.textMuted} editable={!busy && !expired} onSubmitEditing={() => answer(attempt)} />
              }
              <Text style={styles.unit}>{step.unit}</Text></View>
              {step.expression ? <>
                <Pressable style={styles.linkButton} accessibilityRole="button" accessibilityLabel={fractionInput ? 'Nhập số thường' : 'Nhập kết quả phân số'} disabled={!!busy || expired}
                  onPress={() => { setFractionInput(value => !value); setAttempt(''); setAnswerEdited(true); }}>
                  <Text style={styles.link}>{fractionInput ? 'Đổi sang nhập số thường' : 'Kết quả là phân số? Nhập tử và mẫu'}</Text>
                </Pressable><Text style={styles.caption}>Nếu kết quả là phân số, em nhập tử và mẫu; không làm tròn số thập phân.</Text>
              </> : null}
              <AppButton title="Kiểm tra bước này" onPress={() => answer(attempt)} disabled={!attempt.trim() || (fractionInput && !/^-?\d+\/[1-9]\d*$/.test(attempt)) || !!busy || expired} loading={busy === 'answer'} /></>}
            <AppButton title={hintCount ? 'Gợi ý rõ hơn' : 'Gợi ý cách làm bước này'} variant="secondary" onPress={() => answer('', true)} disabled={!!busy || expired} />
            {lesson.status === 'HINT' && lesson.feedback ? <View style={styles.hintCard}>
              <Text style={styles.link}>Gợi ý cho bước này</Text><MathText style={styles.body}>{lesson.feedback}</MathText>
            </View> : lesson.status === 'TRY_AGAIN' && !answerEdited && lesson.feedback ? <Text style={styles.error}>{lesson.feedback}</Text> : null}
          </View> : <View style={styles.card} onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.heading}>Lời giải em vừa hoàn thành</Text><Text style={styles.body}>{lesson.goal}</Text>
            {lesson.feedback ? <Text style={styles.feedback}>{lesson.feedback}</Text> : null}
            {lesson.completed.map((item, index) => <View key={index} style={styles.completedStep}>
              <Text style={styles.link}>{index + 1}. {item.title}</Text>
              <MathText style={styles.body}>{item.expression ? `${item.expression} = ${item.answer} ${item.unit}` : item.answer}</MathText>
              <MathText style={styles.body}>{item.explanation}</MathText>
            </View>)}
            {work ? <Text style={styles.body}>Em đối chiếu những bước vừa học với bài trong ảnh. Các phép tính vừa nhập đã được kiểm tra; nét chữ và hình vẽ vẫn cần nhìn lại.</Text> : null}
          </View>}
        </> : null}
        {error && problem && !lesson && !expired ? <AppButton title="Bắt đầu lại bài học" variant="secondary" onPress={start} /> : null}
        {!!(problem || work) && !editing && !busy ? <AppButton title={saved ? 'Đã lưu bài của em' : 'Lưu bài để học tiếp'} variant="secondary" loading={saving} disabled={saved || saving} onPress={() => void archive()} /> : null}
        <Pressable style={styles.linkButton} accessibilityRole="button" accessibilityLabel="Chụp bài khác" onPress={() => capture()}><Text style={styles.link}>Chụp bài khác</Text></Pressable>
      </ScrollView>}
    </KeyboardAvoidingView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background }, flex: { flex: 1 },
  content: { padding: 18, paddingBottom: 32, gap: 16, width: '100%', maxWidth: 640, alignSelf: 'center' },
  hero: { padding: 18, borderRadius: 26, flexDirection: 'row', alignItems: 'center', gap: 4 },
  mascot: { width: 94, height: 112 }, eyebrow: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold, fontSize: 11, letterSpacing: 1 },
  title: { fontSize: 23, lineHeight: 29, fontFamily: FONTS.extraBold, color: COLORS.textPrimary, marginVertical: 8 },
  heading: { fontSize: 21, lineHeight: 28, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  body: { fontSize: 15, lineHeight: 23, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  card: { backgroundColor: COLORS.surface, borderRadius: 24, padding: 20, gap: 14, ...SHADOWS.small },
  errorCard: { backgroundColor: '#FFF3ED', padding: 16, borderRadius: 18, gap: 12 },
  error: { color: '#963E22', fontSize: 15, lineHeight: 22, fontFamily: FONTS.semiBold },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  problemHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  problemToggle: { flex: 1, minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 14 },
  problemIcon: { width: 40, height: 40, borderRadius: 13, backgroundColor: COLORS.surfaceSubdued, alignItems: 'center', justifyContent: 'center' },
  problemTitle: { fontSize: 17, lineHeight: 23, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  problemHint: { fontSize: 12, lineHeight: 18, color: COLORS.textSecondary, fontFamily: FONTS.medium },
  problemChevron: { width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.surfaceSubdued, alignItems: 'center', justifyContent: 'center' },
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
  rail: { flexDirection: 'row', gap: 6, paddingVertical: 4 }, railStep: { flex: 1, height: 6, borderRadius: 3, backgroundColor: '#E2DCEB' },
  railActive: { backgroundColor: COLORS.primary },
  question: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 19, lineHeight: 28 },
  expression: { backgroundColor: '#F1EBFF', borderRadius: 18, padding: 18 },
  expressionText: { fontSize: 24, lineHeight: 34, color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  choice: { minHeight: 52, borderRadius: 16, padding: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1.5, borderColor: '#DDD4F5', backgroundColor: '#FAF8FF' },
  choiceSelected: { backgroundColor: '#E8DEFF', borderColor: COLORS.primary }, choiceText: { flex: 1, marginRight: 8, color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 17, lineHeight: 24 },
  answerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, alignItems: 'center' }, numberInput: { flex: 1, minWidth: 120, minHeight: 58, borderWidth: 1.5, borderColor: '#D7CDF2', backgroundColor: '#FAF8FF', borderRadius: 16, padding: 16, fontFamily: FONTS.bold, fontSize: 18, color: COLORS.textPrimary },
  fractionAnswer: { flex: 1, minWidth: 120, borderWidth: 1.5, borderColor: '#D7CDF2', backgroundColor: '#FAF8FF', borderRadius: 16, padding: 12, gap: 4 },
  fractionNumber: { minHeight: 48, textAlign: 'center', fontFamily: FONTS.bold, fontSize: 20, color: COLORS.textPrimary },
  fractionBar: { height: 2, backgroundColor: COLORS.primaryDark, marginHorizontal: 16 },
  unit: { flexShrink: 1, maxWidth: '100%', color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 19 },
  explanation: { backgroundColor: '#E9F5EF', padding: 16, borderRadius: 16 }, feedback: { color: '#226A51', fontFamily: FONTS.bold, fontSize: 15, lineHeight: 23 },
  hintCard: { backgroundColor: '#F4EEFF', borderWidth: 1, borderColor: '#D7CDF2', padding: 16, borderRadius: 16, gap: 10 },
  completedStep: { gap: 8, paddingVertical: 12, borderBottomWidth: 1, borderColor: '#ECE6F5' },
});
