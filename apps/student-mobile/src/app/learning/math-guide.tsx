import React, { useCallback, useContext, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, AppState, Image, Keyboard, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import type { ScrollViewInstance, TextInputInstance, ViewInstance } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { ImageDraft, recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';
import { imageDraftPersistence } from '../../features/recognition/state/imageDraftPersistence';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';
import { divisionText, savedDivision, CompletedLessonStep, LessonResponse, NotebookLine, NotebookRead, TutorService, trimWorkReviewLine, workReviewLines } from '../../features/tutoring/api/TutorService';
import { DivisionReview } from '../../features/tutoring/DivisionReview';
import { AuthContext } from '../../context/AuthContext';
import { saveLesson } from '../../features/tutoring/learningHistory';
import { MathText } from '../../components/domain/MathText';
import { problemPresentation } from '../../components/domain/problemPresentation';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';
import { HintCheckIn } from '../../features/tutoring/HintCheckIn';
import { ProblemSummary } from '../../features/tutoring/ProblemSummary';
import { StudentWorkReview } from '../../features/tutoring/StudentWorkReview';
import { WorkReviewPreparation } from '../../features/tutoring/WorkReviewPreparation';
import { QuestionPicker } from '../../features/tutoring/QuestionPicker';
import { sourceClarification } from '../../features/tutoring/sourceClarification';
import { LessonListening } from '../../features/tutoring/LessonListening';
import { LessonCalculation } from '../../features/tutoring/LessonCalculation';
import { convertAnswerInput } from '../../features/tutoring/answerInput';
import { completedNarration, stepNarration } from '../../features/tutoring/narration';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { LessonQuestion } from '../../features/tutoring/LessonQuestion';
import { LessonProblem } from '../../features/tutoring/LessonProblem';
import { CorrectAnswerFeedback } from '../../features/tutoring/CorrectAnswerFeedback';
import { ComprehensionCheck } from '../../features/tutoring/ComprehensionCheck';
import { loadLearningProgress,saveLearningProgress,sameStoredAnswer,type LearningProgress } from '../../features/tutoring/learningProgress';
import { NarrationPreparation, useNarrationPreparation } from '../../features/tutoring/NarrationPreparation';
import { QuizAfterLearningButton } from '../../features/quiz/QuizInvitation';
import { useQuizPreparation } from '../../features/quiz/useQuizPreparation';
import { submissionId } from '../../features/quiz/quizInput';
import { getCurriculumProblem } from '../../data/primaryMathCurriculum';

const MASCOT = require('../../../assets/illustrations/robot-mascot.png');

function SolutionLine({ item }: { item: CompletedLessonStep }) {
  const [expanded, setExpanded] = useState(false);
  const details = item.calculationDetails?.length ? item.calculationDetails : item.explanation ? [item.explanation] : [];
  return <View style={styles.completedStep}>
    <MathText style={styles.question}>{item.solutionSentence || `${item.title} là:`}</MathText>
    <MathText style={styles.body}>{`${item.expression} = ${item.answer}${item.unit ? ` (${item.unit})` : ''}`}</MathText>
    {details.length ? <Pressable accessibilityRole="button" accessibilityLabel={`${expanded ? 'Thu gọn' : 'Xem chi tiết'}: ${item.title}`}
      accessibilityState={{ expanded }} aria-expanded={expanded} onPress={() => setExpanded(value => !value)} style={styles.solutionToggle}>
      <Text style={styles.historyLabel}>{expanded ? 'Thu gọn chi tiết' : 'Xem chi tiết'}</Text>
      <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color={COLORS.primaryDark} accessible={false} />
    </Pressable> : null}
    {expanded ? <View style={styles.solutionDetails}>{details.map((detail, index) => <MathText key={index} style={styles.body}>{detail}</MathText>)}</View> : null}
  </View>;
}

function checkedStudentAnswer(step: Pick<CompletedLessonStep, 'answer' | 'choices'>, entered?: string): string {
  // Choices keep the server's exact label; equivalent numbers only preserve typed input.
  return !step.choices?.length && entered !== undefined && sameStoredAnswer(entered, step.answer) ? entered : step.answer;
}

type GuideParams = { problemText?: string; workText?: string; lessonId?: string; reflection?: string };
type GuideTask = 'read' | 'lesson' | 'answer' | 'hint';

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
  const [resumePhoto, setResumePhoto] = useState(false);
  // Remount also aborts pending requests: answers/exploration belong to one source and account.
  const sourceKey = JSON.stringify([owner, params.problemText, params.workText, params.lessonId, params.reflection, draft]);
  if (Platform.OS === 'web' && draft?.recoveredAfterReload && draft.processingStarted && !resumePhoto) return <SafeAreaView>
    <AppHeader title="Bài làm của em" showBack />
    <RecoveryNotice title="Ảnh của em vẫn được giữ" message="Lần đọc trước chưa có kết quả xác nhận. Em có muốn tiếp tục đọc ảnh này không?"
      actions={[{ label: 'Tiếp tục đọc ảnh', onPress: () => setResumePhoto(true) }]} />
  </SafeAreaView>;
  return <NarrationPreparation key={sourceKey} owner={owner}><MathGuideLesson owner={owner} params={params} sourceDraft={draft} /></NarrationPreparation>;
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
  const [sourceNeedsReview, setSourceNeedsReview] = useState(context?.problemNeedsReview === true);
  const [quizPreparationKey] = useState(() => context?.quizPreparationKey || submissionId());
  const sourceIssue = sourceClarification(problem);
  const needsSourceClarification = sourceIssue !== null;
  useQuizPreparation(quizPreparationKey, problem, problemConfirmed && !needsSourceClarification);
  const [workConfirmed, setWorkConfirmed] = useState(context?.workConfirmed === true);
  const [lesson, setLesson] = useState<LessonResponse | null>(null);
  const [preparationPaused, setPreparationPaused] = useState(false);
  const [preparationPoll, setPreparationPoll] = useState(0);
  const [attempt, setAttempt] = useState('');
  const [choiceResult, setChoiceResult] = useState<{ sessionId: string; revision: number; choice: string; correct: boolean } | null>(null);
  const [questionDraft,setQuestionDraft]=useState('');
  const [answerEdited, setAnswerEdited] = useState(false);
  const [hintCount, setHintCount] = useState(0);
  const [hintText, setHintText] = useState('');
  const [hintPages, setHintPages] = useState<string[]>([]);
  const [hintPage, setHintPage] = useState(0);
  const [hintExhausted, setHintExhausted] = useState(false);
  const [focusedChoice, setFocusedChoice] = useState<string | null>(null);
  const [reviewedStep, setReviewedStep] = useState<(CompletedLessonStep & { question: string; choices: string[]; studentAnswer: string }) | null>(null);
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const [submittedAnswers, setSubmittedAnswers] = useState<string[]>([]);
  const [fractionInput, setFractionInput] = useState(false);
  const [answerModeNotice, setAnswerModeNotice] = useState('');
  const answerModeDrafts = useRef({ number: '', fraction: '', showingFallback: false });
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [tool, setTool] = useState<'audio' | 'ask' | 'menu' | 'work' | 'summary' | 'hint' | null>(null);
  const [busy, setBusy] = useState<GuideTask | null>(null);
  const [finishing, setFinishing] = useState<{ kind: 'read' | 'lesson'; id: number } | null>(null);
  const [error, setError] = useState('');
  const [failedTask, setFailedTask] = useState<GuideTask | null>(null);
  const [photoNeedsCrop, setPhotoNeedsCrop] = useState(false);
  const [expired, setExpired] = useState(false);
  const [editing, setEditing] = useState<'problem' | 'work' | null>(null);
  const [reviewFocused, setReviewFocused] = useState(false);
  const [reviewStarted, setReviewStarted] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [restoring,setRestoring]=useState(true),[progressNotice,setProgressNotice]=useState('');
  const progressDraft=useRef<LearningProgress|null>(null);
  const [lessonId,setLessonId] = useState(() => context?.lessonId || (typeof params.lessonId === 'string' ? params.lessonId : `lesson_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`));
  const requestId = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const running = useRef(false);
  const active = useRef(true);
  const initialized = useRef(false);
  const scroll = useRef<ScrollViewInstance>(null);
  const answerInput = useRef<TextInputInstance>(null);
  const firstChoice = useRef<ViewInstance>(null);
  const stepHeading = useRef<ViewInstance>(null);
  const previousHistoryIndex = useRef<number | null>(null);
  useEffect(()=>{
    const control=new AbortController();let live=true;
    void loadLearningProgress(owner).then(async saved=>{
      if(!live||work||!saved||saved.problemText!==problem||saved.workText!==work||params.lessonId&&saved.lessonId!==params.lessonId)return;
      setProblemConfirmed(true);setWorkConfirmed(!!work);
      setLessonId(saved.lessonId);
      try{
        const result=await TutorService.resumeLesson(saved.sessionId,problem,control.signal);
        if(!live)return;setLesson(result);setAttempt(result.revision===saved.revision&&result.stepIndex===saved.stepIndex?saved.attempt:'');
        setSubmittedAnswers(result.completed.map((item,index)=>checkedStudentAnswer(item,saved.completedAnswers?.[index])));
        setQuestionDraft(result.revision===saved.revision?saved.question||'':'');
        if(saved.reviewing&&result.revision===saved.revision&&result.review&&result.completed.length){
          setReviewedStep({...result.completed[result.completed.length-1],...result.review,
            studentAnswer:checkedStudentAnswer({...result.completed[result.completed.length-1],...result.review},saved.attempt)});
        }
        setProgressNotice('Đã khôi phục bước đang học của em.');
      }catch{if(live)setProgressNotice('Đề và bài làm đã được giữ. Em bắt đầu lại để mở phiên học mới nhé.');}
    }).finally(()=>{if(live)setRestoring(false);});
    return()=>{live=false;control.abort();};
    // Initial source only; edits create a new lesson rather than restoring the old source.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[owner]);
  useEffect(()=>{
    if(restoring||!lesson||!owner||editing)return;
    const row:LearningProgress={version:1,at:Date.now(),lessonId,sessionId:lesson.sessionId,revision:lesson.revision,stepIndex:lesson.stepIndex,
      problemText:problem,workText:work,attempt:reviewedStep?.studentAnswer||attempt,question:questionDraft,reviewing:!!reviewedStep,completedAnswers:submittedAnswers};
    progressDraft.current=row;
    const timer=setTimeout(()=>{void saveLearningProgress(owner,row).catch(()=>setProgressNotice('Chưa lưu được tiến độ trên thiết bị. Em dùng nút lưu bài nhé.'));},350);
    return()=>clearTimeout(timer);
  },[owner,restoring,lesson,lessonId,problem,work,attempt,reviewedStep,editing,questionDraft,submittedAnswers]);
  useEffect(()=>{
    const flush=()=>{const row=progressDraft.current;if(row&&owner)void saveLearningProgress(owner,row).catch(()=>{});};
    const listener=AppState.addEventListener('change',state=>{if(state!=='active')flush();});
    if(typeof window!=='undefined'&&window.addEventListener)window.addEventListener('pagehide',flush);
    return()=>{listener.remove();if(typeof window!=='undefined'&&window.removeEventListener)window.removeEventListener('pagehide',flush);flush();};
  },[owner]);
  const questionPosition = useRef(0);
  const lessonPosition = useRef(0);
  const invalidPhoto = reading && ['MULTIPLE', 'UNREADABLE'].includes(reading.kind);
  const preparationWork = workConfirmed && !work.includes('[?]') ? work : '';
  useEffect(() => {
    if (!owner || restoring || lesson || editing || busy || invalidPhoto || work || needsSourceClarification || (sourceNeedsReview && !problemConfirmed) || problem.trim().length < 3 || problem.includes('[?]')) return;
    const abort = new AbortController();
    // Private preparation starts while the pupil reviews the transcription.
    // It returns no lesson; the normal Start action still requires confirmation.
    void TutorService.prepareLesson(problem.trim(), preparationWork, abort.signal).catch(() => {});
    return () => abort.abort();
  }, [owner, restoring, problem, preparationWork, work, editing, invalidPhoto, lesson, busy, needsSourceClarification, sourceNeedsReview, problemConfirmed]);
  const divisionLines = workLines.filter(line => line.division);
  const divisionLine = !invalidPhoto && divisionLines.length === 1 ? divisionLines[0] : null;
  const division = divisionLine?.division;
  const step = lesson?.step;
  const immediateChoice = choiceResult && lesson && choiceResult.sessionId === lesson.sessionId
    && choiceResult.revision === lesson.revision && choiceResult.choice === attempt && step?.choices.includes(attempt) ? choiceResult : null;
  const lessonSessionId = lesson?.sessionId;
  const lessonStepIndex = lesson?.stepIndex;
  useEffect(() => { answerModeDrafts.current = { number: '', fraction: '', showingFallback: false }; }, [lessonSessionId, lessonStepIndex]);
  const changeAttempt = (value: string) => {
    answerModeDrafts.current.showingFallback = false;
    setAttempt(value); setAnswerEdited(true); setAnswerModeNotice('');
  };
  const changeAnswerMode = (mode: boolean) => {
    if (mode === fractionInput) return;
    const drafts = answerModeDrafts.current;
    drafts[fractionInput ? 'fraction' : 'number'] = attempt;
    const nextDraft = drafts[mode ? 'fraction' : 'number'];
    const converted = drafts.showingFallback ? null : convertAnswerInput(attempt, mode);
    setAttempt(converted ?? nextDraft);
    setAnswerModeNotice(converted === null && attempt.trim()
      ? `Mỗi kiểu nhập giữ bản nháp riêng. ${nextDraft ? 'Đã khôi phục bản nháp' : 'Em có thể nhập'} ${mode ? 'phân số' : 'số'} hoặc chuyển lại để xem câu trả lời vừa nhập.` : '');
    drafts.showingFallback = converted === null && !drafts.showingFallback;
    setFractionInput(mode); setAnswerEdited(true);
  };
  const currentViewIndex = Math.max(0, (lessonStepIndex ?? 0) - (reviewedStep ? 1 : 0));
  const historicalStep = historyIndex === null ? undefined : lesson?.completed[historyIndex];
  const viewingHistory = !!historicalStep;
  const displayedReview = historicalStep ? { ...historicalStep, question: historicalStep.question || historicalStep.title,
    choices: historicalStep.choices || [], studentAnswer: checkedStudentAnswer(historicalStep, submittedAnswers[historyIndex!]) } : reviewedStep;
  const visibleStepIndex = viewingHistory ? historyIndex! : currentViewIndex;
  const visibleHint = hintPages[hintPage] || hintText;
  const solutionVisible = lesson?.status === 'COMPLETE' && !displayedReview && !step && !editing && !viewingHistory;
  const narrationParts = displayedReview ? completedNarration([displayedReview]) : step ? stepNarration(step, visibleHint)
    : lesson ? completedNarration(lesson.completed.filter(item => item.kind !== 'UNDERSTAND')) : [];
  const preparedCurriculumSpeech = !!getCurriculumProblem(problem);
  useNarrationPreparation(owner && lesson ? { sessionId: lesson.sessionId, revision: lesson.revision,
    ...(preparedCurriculumSpeech ? { useFallback: true } : {}) } : null, narrationParts);
  useEffect(() => {
    if (!lessonSessionId) return;
    const frame = requestAnimationFrame(() => scroll.current?.scrollTo({ y: 0, animated: false }));
    return () => cancelAnimationFrame(frame);
  }, [lessonSessionId, lessonStepIndex]);
  useLayoutEffect(() => {
    if (historyIndex === previousHistoryIndex.current) return;
    previousHistoryIndex.current = historyIndex;
    // Focus after the new card mounts, in both directions, before another keypress.
    if (Platform.OS === 'web') stepHeading.current?.focus();
  }, [historyIndex]);
  const showHistory = (index: number | null) => {
    if (busy || (index !== null && (!lesson || index < 0 || index >= lesson.completed.length || index >= currentViewIndex))) return;
    setTool(null); setHistoryIndex(index); Keyboard.dismiss();
    scroll.current?.scrollTo({ y: 0, animated: false });
  };
  const returnFromTool = () => {
    setTool(null);
    if (displayedReview) stepHeading.current?.focus();
    else if (step?.choices.length) firstChoice.current?.focus();
    else answerInput.current?.focus();
  };
  const cancel = () => {
    requestId.current += 1; controller.current?.abort(); controller.current = null; running.current = false; setBusy(null); setFinishing(null);
  };
  const failureMessage = useCallback((failure: any, task?: GuideTask) => {
    const status = failure?.response?.status;
    const code = failure?.response?.data?.error?.code;
    const timedOut = failure?.code === 'ECONNABORTED' || failure?.code === 'ETIMEDOUT' || code === 'TUTOR_TIMEOUT';
    if (status === 401) {
      setExpired(true); setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.');
    } else if (task === 'read') {
      if (status === 413 || code === 'IMAGE_TOO_LARGE') {
        setPhotoNeedsCrop(true);
        setError('Ảnh hơi lớn. Em chọn vùng nhỏ hơn hoặc nhập đề bằng chữ nhé.');
      } else if ([400, 415, 422].includes(status)) {
        setPhotoNeedsCrop(true);
        setError('Mình chưa mở được ảnh này. Em chọn lại vùng bài toán hoặc nhập đề bằng chữ nhé.');
      } else if (timedOut || status === 504) {
        setError('Đọc ảnh lâu hơn dự kiến. Ảnh vẫn được giữ để em thử lại hoặc nhập đề bằng chữ.');
      } else if (status === 429 || code === 'TUTOR_RATE_LIMITED' || code === 'TUTOR_BUSY') {
        setError('Đang có nhiều yêu cầu đọc ảnh. Ảnh vẫn được giữ. Em đợi một chút rồi thử lại nhé.');
      } else {
        setError('Chưa đọc được ảnh lúc này. Ảnh của em vẫn được giữ để em thử lại hoặc nhập đề bằng chữ.');
      }
    } else if ([409, 410].includes(status)) {
      setLesson(null); setError('Bài học đã hết phiên. Đề và bài làm vẫn ở đây; em bắt đầu lại nhé.');
    } else if ([400, 422].includes(status)) {
      setError('Đề bài còn thiếu hoặc có chỗ chưa rõ. Em kiểm tra lại lời văn, số và câu hỏi nhé.');
    } else if (timedOut) {
      setError('Phần hướng dẫn chưa kịp chuẩn bị trong thời gian chờ. Đề và bài làm vẫn được giữ; em thử lại nhé.');
    } else if (status === 503 || status === 429) {
      setError(code === 'TUTOR_RATE_LIMITED' || code === 'TUTOR_BUSY' || status === 429
        ? 'Đang có nhiều yêu cầu. Em chờ một chút rồi thử lại; đề và bài làm vẫn được giữ.'
        : code === 'LESSON_VALIDATION_FAILED'
          ? 'Bản hướng dẫn vừa tạo chưa đạt kiểm tra nên mình chưa mở cho em. Đề và bài làm vẫn được giữ; em thử lại nhé.'
          : 'Mình chưa chuẩn bị được hướng dẫn lúc này. Bài của em vẫn ở đây; em thử lại nhé.');
    } else setError('Chưa kết nối được lúc này. Bài của em vẫn ở đây, em thử lại nhé.');
  }, [setExpired, setError]);
  const run = useCallback(async <T,>(kind: GuideTask, task: (signal: AbortSignal) => Promise<T>, apply: (value: T) => void) => {
    if (running.current || expired) return;
    const id = ++requestId.current; const abort = new AbortController();
    controller.current = abort; running.current = true; setBusy(kind); setFinishing(null); setError(''); setFailedTask(null); setPhotoNeedsCrop(false);
    try {
      const result = await task(abort.signal);
      if (active.current && id === requestId.current) {
        apply(result);
        if (kind === 'read') setFinishing({ kind, id });
      }
    } catch (failure) {
      if (__DEV__ && !abort.signal.aborted) {
        console.warn('[MATH_TUTOR_REQUEST_FAILED]', { stage: kind, status: (failure as any)?.response?.status, code: (failure as any)?.code });
      }
      if (active.current && id === requestId.current && !abort.signal.aborted) { setFailedTask(kind); failureMessage(failure, kind); }
    } finally {
      if (active.current && id === requestId.current) { running.current = false; controller.current = null; setBusy(null); }
    }
  }, [expired, failureMessage, setError]);
  const preparationSession = lesson?.status === 'PREPARING' ? lesson.sessionId : undefined;
  const preparationRevision = lesson?.revision;
  useEffect(() => {
    if (!preparationSession || preparationRevision === undefined) return;
    const abort = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let polls = 0;
    const deadline = Date.now() + 45000;
    const poll = async () => {
      if (abort.signal.aborted || !active.current) return;
      try {
        const result = await TutorService.lessonPreparation({ sessionId: preparationSession, revision: preparationRevision }, false, abort.signal);
        if (abort.signal.aborted || !active.current) return;
        setPreparationPaused(false);
        setLesson(current => current?.sessionId === preparationSession && current.revision === preparationRevision ? result : current);
        if (!result.preparingMath) {
          setFractionInput(!!result.step?.expression && /phân số|mấy phần/i.test(result.step.question));
          return;
        }
        if (result.status !== 'PREPARING') return;
        if (++polls < 45 && Date.now() < deadline) timer = setTimeout(() => void poll(), 1000);
        else setPreparationPaused(true);
      } catch {
        if (!abort.signal.aborted && active.current) setPreparationPaused(true);
      }
    };
    timer = setTimeout(() => void poll(), 500);
    return () => { abort.abort(); clearTimeout(timer); };
  }, [preparationSession, preparationRevision, preparationPoll]);
  const retryPreparation = () => {
    if (!lesson) return;
    void run('answer', signal => TutorService.lessonPreparation(lesson, true, signal), result => {
      setLesson(result); setReviewedStep(null); setPreparationPaused(false);
      setPreparationPoll(value => value + 1);
      setFractionInput(!!result.step?.expression && /phân số|mấy phần/i.test(result.step.question));
    });
  };
  const inspectPhoto = useCallback(async () => {
    if (!photoAllowed) return;
    await run('read', async signal => {
      if (draft) await imageDraftPersistence.beginProcessing(draft);
      if (signal.aborted) throw new Error('Cancelled');
      return TutorService.inspect(imageUri, true, signal);
    }, result => {
      recognitionDraftStore.updateDraft({ processingStarted: false, recoveredAfterReload: false });
      void imageDraftPersistence.complete();
      setReading(result); setLesson(null);
      if (['MULTIPLE', 'UNREADABLE'].includes(result.kind)) return;
      const workRead = result.kind === 'WORK' || result.kind === 'MIXED';
      const text = workRead ? result.lines.map(row => row.text).join('\n') : '';
      if (context?.purpose === 'ADD_PROBLEM') {
        // A worked page is not silently treated as an original question.
        if (!result.problemText.trim()) { setError('Ảnh này chưa có đề bài. Em chụp phần câu hỏi nhé.'); return; }
        setProblem(result.problemText); setProblemImage(imageUri); setProblemConfirmed(false);
        setSourceNeedsReview(result.problemNeedsReview === true);
      } else if (context?.purpose === 'ADD_WORK') {
        if (!workRead) { setError('Ảnh này chưa có phần em đã làm. Em chụp bài làm nhé.'); return; }
        setWork(text); setWorkImage(imageUri); setWorkImageCurrent(true); setWorkLines(result.lines); setUncertainWork(result.lines.some(row => row.uncertain)); setWorkConfirmed(false);
      } else {
        setProblem(draft?.problemText || result.problemText);
        setSourceNeedsReview(!draft?.problemText && result.problemNeedsReview === true);
        setProblemConfirmed(false); setWorkConfirmed(false);
        setWork(text); setWorkLines(workRead ? result.lines : []); setUncertainWork(workRead && result.lines.some(row => row.uncertain));
        if (workRead) { setWorkImage(imageUri); setWorkImageCurrent(true); }
        if (result.problemText) setProblemImage(imageUri);
      }
    });
  }, [photoAllowed, imageUri, context?.purpose, draft, run]);
