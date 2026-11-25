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
import { HintSheetContent } from '../../features/tutoring/HintSheetContent';
import { buildHintVisual } from '../../features/tutoring/hintVisualModel';
import { ProblemSummary } from '../../features/tutoring/ProblemSummary';
import { StudentWorkReview, type WorkReviewCheckpoint } from '../../features/tutoring/StudentWorkReview';
import { WorkReviewPreparation } from '../../features/tutoring/WorkReviewPreparation';
import { QuestionPicker } from '../../features/tutoring/QuestionPicker';
import { sourceClarification } from '../../features/tutoring/sourceClarification';
import { LessonListening } from '../../features/tutoring/LessonListening';
import { LessonCalculation } from '../../features/tutoring/LessonCalculation';
import { LessonHint } from '../../features/tutoring/LessonHint';
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
import { mathGuideScope, readMathGuideCheckpoint, saveMathGuideCheckpoint, type MathGuideCheckpoint } from '../../features/tutoring/mathGuideCheckpoint';
import { getCurriculumProblem } from '../../data/primaryMathCurriculum';

const MASCOT = require('../../../assets/illustrations/robot-mascot.png');

function SolutionLine({ item }: { item: CompletedLessonStep }) {
  const [expanded, setExpanded] = useState(false);
  const details = [...new Set([...(item.guidance?.length ? item.guidance.slice(0, 1) : item.explanation ? [item.explanation] : []), ...(item.calculationDetails ?? []), ...(item.guidance?.slice(1) ?? [])])];
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

type GuideParams = { problemText?: string; workText?: string; lessonId?: string; reflection?: string; guidePhotoId?: string; guideEntryId?: string };
type GuideTask = 'read' | 'lesson' | 'answer' | 'hint';
type EditableField = 'problem' | 'work';

function startsWithFraction(step: LessonResponse['step']) {
  return step?.answerFormat === 'FRACTION' || (!!step && !step.answerFormat && (step.unit === 'phần' || /phân số|mấy phần/i.test(step.question)));
}

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
  const candidate = draftSource.owner === owner && !params.problemText && !params.workText ? draftSource.draft : null;
  const draft = !params.guidePhotoId || candidate?.imageSessionId === params.guidePhotoId ? candidate : null;
  const imageId = draft?.imageSessionId;
  const checkpointScope = Platform.OS === 'web' ? mathGuideScope(owner) : null;
  const checkpointRoute = JSON.stringify([params.guidePhotoId || imageId, params.guideEntryId, params.lessonId, params.problemText, params.workText]);
  const checkpoint = checkpointScope ? readMathGuideCheckpoint(checkpointScope, checkpointRoute) : null;
  const [photoChoice, setPhotoChoice] = useState<{ owner?: string; imageId: string; edit?: EditableField }>();
  const choice = imageId && photoChoice?.imageId === imageId && photoChoice.owner === owner ? photoChoice : undefined;
  // Remount also aborts pending requests: answers/exploration belong to one source and account.
  const sourceKey = JSON.stringify([owner, params.problemText, params.workText, params.lessonId, params.reflection, Platform.OS === 'web' ? [imageId, params.guideEntryId] : draft, choice?.edit]);
  if (Platform.OS === 'web' && imageId && draft?.mode === 'MATH_TUTOR' && draft.recoveredAfterReload && draft.processingStarted && !choice && !checkpoint) {
    const edit = draft.lessonContext?.purpose === 'ADD_WORK' ? 'work' : 'problem';
    return <SafeAreaView>
      <AppHeader title="Bài làm của em" showBack />
      <RecoveryNotice title="Ảnh của em vẫn được giữ" message="Lần đọc trước chưa có kết quả xác nhận. Em có thể đọc lại ảnh hoặc nhập bằng chữ."
        actions={[
          { label: 'Tiếp tục đọc ảnh', onPress: () => setPhotoChoice({ owner, imageId }) },
          { label: edit === 'work' ? 'Nhập bài làm bằng chữ' : 'Nhập đề bằng chữ', onPress: () => setPhotoChoice({ owner, imageId, edit }) },
        ]} />
    </SafeAreaView>;
  }
  return <NarrationPreparation key={sourceKey} owner={owner}>
    <MathGuideLesson owner={owner} params={params} sourceDraft={draft} initialEdit={choice?.edit}
      checkpoint={checkpoint} checkpointScope={checkpointScope} checkpointRoute={checkpointRoute} />
  </NarrationPreparation>;
}

function MathGuideLesson({ owner, params, sourceDraft, initialEdit, checkpoint, checkpointScope, checkpointRoute }: {
  owner?: string; params: GuideParams; sourceDraft: ImageDraft | null; initialEdit?: EditableField;
  checkpoint: MathGuideCheckpoint | null; checkpointScope: string | null; checkpointRoute: string;
}) {
  const router = useRouter();
  const { width, height, fontScale } = useWindowDimensions();
  const spacious = width >= 1100 && fontScale <= 1.3;
  const supplied = typeof params.problemText === 'string' ? params.problemText.slice(0, 4000) : '';
  const suppliedWork = typeof params.workText === 'string' ? params.workText.slice(0, 6000) : '';
  const draft = supplied || suppliedWork ? null : sourceDraft;
  const context = draft?.lessonContext;
  const imageUri = !initialEdit && draft?.mode === 'MATH_TUTOR' ? draft.croppedImageUri ?? '' : '';
  const photoAllowed = !!imageUri && draft?.privacyConfirmed === true && !!draft.privacyImageUri;
  const [reading, setReading] = useState<NotebookRead | null>(checkpoint ? checkpoint.reading : supplied || suppliedWork ? {
    kind: suppliedWork ? 'MIXED' : 'PROBLEM', problemText: supplied,
    lines: savedDivision(suppliedWork) ? [{ text: suppliedWork, box: null, uncertain: true, division: savedDivision(suppliedWork) }] : [], needsProblem: !supplied,
  } : null);
  const [problem, setProblem] = useState(checkpoint?.problem ?? (supplied || context?.problemText || ''));
  const [work, setWork] = useState(checkpoint?.work ?? (suppliedWork || context?.workText || ''));
  const [workImage, setWorkImage] = useState(checkpoint ? (checkpoint.workPhoto && photoAllowed ? imageUri : '') : context?.workImageUri || '');
  const [workImageCurrent, setWorkImageCurrent] = useState(checkpoint?.workImageCurrent ?? (context?.workImageCurrent !== false));
  const [workLines, setWorkLines] = useState<NotebookLine[]>(checkpoint?.workLines ?? (context?.workLines || reading?.lines || []));
  const [problemImage, setProblemImage] = useState(checkpoint ? (checkpoint.problemPhoto && photoAllowed ? imageUri : '') : context?.problemImageUri || '');
  const [uncertainWork, setUncertainWork] = useState(checkpoint?.uncertainWork ?? (context?.uncertainWork || false));
  const [problemConfirmed, setProblemConfirmed] = useState(checkpoint?.problemConfirmed ?? (context?.problemConfirmed === true));
  const [sourceNeedsReview, setSourceNeedsReview] = useState(checkpoint?.sourceNeedsReview ?? (context?.problemNeedsReview === true));
  const [quizPreparationKey] = useState(() => checkpoint?.quizPreparationKey || context?.quizPreparationKey || submissionId());
  const sourceIssue = sourceClarification(problem);
  const needsSourceClarification = sourceIssue !== null;
  useQuizPreparation(quizPreparationKey, problem, problemConfirmed && !needsSourceClarification);
  const [workConfirmed, setWorkConfirmed] = useState(checkpoint?.workConfirmed ?? (context?.workConfirmed === true));
  const [lesson, setLesson] = useState<LessonResponse | null>(null);
  const [summaryStage, setSummaryStage] = useState<'summary' | 'solving' | undefined>();
  const [preparationPaused, setPreparationPaused] = useState(false);
  const [preparationCountdown, setPreparationCountdown] = useState<{ lesson: LessonResponse | null; remaining: number }>({ lesson: null, remaining: 0 });
  const [preparationPoll, setPreparationPoll] = useState(0);
  const [attempt, setAttempt] = useState('');
  const [questionDraft,setQuestionDraft]=useState('');
  const [answerEdited, setAnswerEdited] = useState(false);
  const [hintPage, setHintPage] = useState(0);
  const [hintOpen, setHintOpen] = useState(false);
  const [focusedChoice, setFocusedChoice] = useState<string | null>(null);
  const [reviewedStep, setReviewedStep] = useState<(CompletedLessonStep & { question: string; choices: string[]; studentAnswer: string }) | null>(null);
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const [submittedAnswers, setSubmittedAnswers] = useState<string[]>([]);
  const [fractionInput, setFractionInput] = useState(false);
  const [answerModeNotice, setAnswerModeNotice] = useState('');
  const answerModeDrafts = useRef({ number: '', fraction: '', showingFallback: false });
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  useEffect(() => {
    const shown = Keyboard.addListener('keyboardDidShow', () => setKeyboardVisible(true));
    const hidden = Keyboard.addListener('keyboardDidHide', () => setKeyboardVisible(false));
    return () => { shown.remove(); hidden.remove(); };
  }, []);
  const [tool, setTool] = useState<'audio' | 'ask' | 'menu' | 'work' | 'summary' | 'hint' | 'parent' | null>(null);
  const [busy, setBusy] = useState<GuideTask | null>(null);
  const [finishing, setFinishing] = useState<{ kind: 'read' | 'lesson'; id: number } | null>(null);
  const [error, setError] = useState('');
  const [failedTask, setFailedTask] = useState<GuideTask | null>(null);
  const [photoNeedsCrop, setPhotoNeedsCrop] = useState(false);
  const [expired, setExpired] = useState(false);
  const [editing, setEditing] = useState<EditableField | null>(checkpoint ? checkpoint.editing : initialEdit ?? null);
  const [reviewFocused, setReviewFocused] = useState(checkpoint?.reviewFocused ?? false);
  const [reviewStarted, setReviewStarted] = useState(checkpoint?.reviewStarted ?? false);
  const [workReviewCheckpoint, setWorkReviewCheckpoint] = useState<WorkReviewCheckpoint | null>(checkpoint?.workReview ?? null);
  const [autoStartReview, setAutoStartReview] = useState(!checkpoint?.reviewStarted);
  const [workOptionsOpen, setWorkOptionsOpen] = useState(false);
  const [saved, setSaved] = useState(checkpoint?.savedToHistory ?? false);
  const [saving, setSaving] = useState(false);
  const [restoring,setRestoring]=useState(true),[progressNotice,setProgressNotice]=useState('');
  const progressDraft=useRef<LearningProgress|null>(null);
  const [lessonId,setLessonId] = useState(() => checkpoint?.lessonId || context?.lessonId || (typeof params.lessonId === 'string' ? params.lessonId : `lesson_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`));
  const requestId = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const running = useRef(false);
  const active = useRef(true);
  const initialized = useRef(!!checkpoint?.reading || !!checkpoint?.editing);
  const resumeProgress = useRef(checkpoint?.progress ?? null);
  const scroll = useRef<ScrollViewInstance>(null);
  const answerInput = useRef<TextInputInstance>(null);
  const firstChoice = useRef<ViewInstance>(null);
  const stepHeading = useRef<ViewInstance>(null);
  const previousHistoryIndex = useRef<number | null>(null);
  useEffect(()=>{
    const control=new AbortController();let live=true;
    const savedProgress = checkpointScope && !params.lessonId
      ? Promise.resolve(checkpoint?.progress ?? null)
      : checkpoint ? Promise.resolve(checkpoint.progress) : loadLearningProgress(owner);
    void savedProgress.then(async saved=>{
      if(!live||(!checkpoint && work)||!saved||saved.problemText!==problem||saved.workText!==work||params.lessonId&&saved.lessonId!==params.lessonId)return;
      setProblemConfirmed(true);setWorkConfirmed(!!work);
      setLessonId(saved.lessonId);
      try{
        const result=await TutorService.resumeLesson(saved.sessionId,problem,control.signal);
        if (!live) return;
        resumeProgress.current = null;
        const sameStep = result.revision === saved.revision && result.stepIndex === saved.stepIndex;
        const restored = sameStep ? (checkpoint?.pendingAnswer ?? saved.attempt) : '';
        const asFraction = sameStep && checkpoint ? checkpoint.fractionInput
          : startsWithFraction(result.step) || (!result.step?.answerFormat && restored.includes('/'));
        if (sameStep && checkpoint) {
          setHistoryIndex(checkpoint.historyIndex !== null && checkpoint.historyIndex < result.completed.length ? checkpoint.historyIndex : null);
          setHintOpen(checkpoint.hintOpen);
          setHintPage(Math.min(checkpoint.hintPage, Math.max(0, (result.revealedHints?.length ?? 1) - 1)));
          setAnswerEdited(checkpoint.answerEdited);
        }
        setLesson(result);
        setSummaryStage(result.revision === saved.revision ? saved.summaryStage
          : result.understandingSteps === 3 && result.stepIndex === 3 ? 'summary' : undefined);
        setFractionInput(asFraction);
        setAttempt(asFraction && restored && !restored.includes('/') ? convertAnswerInput(restored, true) ?? restored : restored);
        setSubmittedAnswers(result.completed.map((item,index)=>checkedStudentAnswer(item,saved.completedAnswers?.[index])));
        setQuestionDraft(result.revision===saved.revision?saved.question||'':'');
        if (saved.reviewing && sameStep && (checkpoint || result.review) && result.completed.length) {
          const completed = result.completed[result.completed.length - 1];
          const review = { ...completed, ...result.review };
          setReviewedStep({ ...review, question: review.question || completed.title, choices: review.choices || [],
            studentAnswer: checkedStudentAnswer(review, saved.attempt) });
        }
        setProgressNotice('Đã khôi phục bước đang học của em.');
      } catch (failure) {
        if (!live) return;
        const status = (failure as { response?: { status?: number } })?.response?.status;
        if (status === 404 || status === 409 || status === 410) resumeProgress.current = null;
        setProgressNotice('Đề và bài làm đã được giữ. Em bắt đầu lại để mở phiên học mới nhé.');
      }
    }).finally(()=>{if(live)setRestoring(false);});
    return()=>{live=false;control.abort();};
    // Initial source only; edits create a new lesson rather than restoring the old source.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[owner]);
  useEffect(()=>{
    if(restoring||!lesson||!owner||editing)return;
    const row:LearningProgress={version:1,at:Date.now(),lessonId,sessionId:lesson.sessionId,revision:lesson.revision,stepIndex:lesson.stepIndex,
      problemText:problem,workText:work,attempt:reviewedStep?.studentAnswer||attempt,question:questionDraft,reviewing:!!reviewedStep,completedAnswers:submittedAnswers,summaryStage};
    progressDraft.current=row;
    const timer=setTimeout(()=>{void saveLearningProgress(owner,row).catch(()=>setProgressNotice('Chưa lưu được tiến độ trên thiết bị. Em dùng nút lưu bài nhé.'));},350);
    return()=>clearTimeout(timer);
  },[owner,restoring,lesson,lessonId,problem,work,attempt,reviewedStep,editing,questionDraft,submittedAnswers,summaryStage]);
  useEffect(()=>{
    const flush=()=>{const row=progressDraft.current;if(row&&owner)void saveLearningProgress(owner,row).catch(()=>{});};
    const listener=AppState.addEventListener('change',state=>{if(state!=='active')flush();});
    if(typeof window!=='undefined'&&window.addEventListener)window.addEventListener('pagehide',flush);
    return()=>{listener.remove();if(typeof window!=='undefined'&&window.removeEventListener)window.removeEventListener('pagehide',flush);flush();};
  },[owner]);
  useLayoutEffect(() => {
    if (restoring || !checkpointScope || mathGuideScope(owner) !== checkpointScope) return;
    if (!reading && !problem && !work && !editing) return;
    const progress: LearningProgress | null = lesson ? {
      version: 1, at: Date.now(), lessonId, sessionId: lesson.sessionId, revision: lesson.revision, stepIndex: lesson.stepIndex,
      problemText: problem, workText: work, attempt: reviewedStep?.studentAnswer || attempt,
      question: questionDraft, reviewing: !!reviewedStep, completedAnswers: submittedAnswers, summaryStage,
    } : resumeProgress.current;
    const savedCheckpoint = saveMathGuideCheckpoint(checkpointScope, checkpointRoute, {
      lessonId, quizPreparationKey, reading, problem, work, workLines, problemConfirmed, sourceNeedsReview,
      workConfirmed, workImageCurrent, uncertainWork, problemPhoto: !!imageUri && problemImage === imageUri,
      workPhoto: !!imageUri && workImage === imageUri, editing, reviewStarted, reviewFocused,
      progress, historyIndex, hintOpen, hintPage, fractionInput, answerEdited, pendingAnswer: attempt, savedToHistory: saved,
      workReview: workReviewCheckpoint,
    });
    if (!savedCheckpoint) setProgressNotice('Chưa lưu được tiến độ trên thiết bị. Em dùng nút lưu bài nhé.');
  }, [restoring, checkpointScope, checkpointRoute, owner, lesson, lessonId, quizPreparationKey, reading, problem, work,
    workLines, problemConfirmed, sourceNeedsReview, workConfirmed, workImageCurrent, uncertainWork,
    imageUri, problemImage, workImage, editing, reviewStarted, reviewFocused, attempt, questionDraft, reviewedStep,
    submittedAnswers, summaryStage, historyIndex, hintOpen, hintPage, fractionInput, answerEdited, saved, workReviewCheckpoint]);
  const calculationPosition = useRef(0);
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
  const publishedStep = lesson?.step;
  const step = publishedStep && publishedStep.kind !== 'UNDERSTAND' && lesson?.revealedHints == null ? {
    ...publishedStep, explanation: 'Em xác định đại lượng cần tìm rồi nhập kết quả của bước này.', guidance: [], workExcerpt: '',
  } : publishedStep;
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
  const hintPages = lesson?.revealedHints ?? [];
  const hintCount = hintPages.length;
  const hintLimit = lesson?.revealedHints == null ? 0 : lesson.hintCount ?? 0;
  const visibleHint = hintOpen ? hintPages[hintPage] || '' : '';
  const showCalculation = !!step?.expression && hintPage >= 1 && hintCount > hintPage;
  const shortCalculationHint = height <= 740 && showCalculation && !displayedReview ? visibleHint : '';
  useEffect(() => {
    if (!shortCalculationHint) return;
    const frame = requestAnimationFrame(() => scroll.current?.scrollTo({
      y: Math.max(0, lessonPosition.current + calculationPosition.current - 6), animated: false,
    }));
    return () => cancelAnimationFrame(frame);
  }, [shortCalculationHint]);
  const fractionDenominator = fractionInput ? attempt.split('/')[1] || '' : '';
  const validAttempt = !!attempt.trim() && (!fractionInput || /^-?\d+\/[1-9]\d*$/.test(attempt));
  const summaryVisible = !!lesson && summaryStage === 'summary' && !viewingHistory && !editing;
  const solutionVisible = lesson?.status === 'COMPLETE' && !displayedReview && !step && !editing && !viewingHistory;
  const narrationParts = summaryVisible && lesson?.summary ? ['Đề bài đã cho.', ...lesson.summary.givens, 'Điều cần tìm.', lesson.summary.question]
    : displayedReview ? completedNarration([displayedReview]) : step ? stepNarration(step, visibleHint)
    : lesson ? completedNarration(lesson.completed.filter(item => item.kind !== 'UNDERSTAND')) : [];
  const preparedCurriculumSpeech = !!getCurriculumProblem(problem);
  useNarrationPreparation(owner && lesson && !(Platform.OS === 'web' && preparedCurriculumSpeech) ? { sessionId: lesson.sessionId, revision: lesson.revision,
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
  const preparationRetryDelay = lesson?.retryAfterSeconds || 0;
  const preparationRetrySeconds = preparationCountdown.lesson === lesson ? preparationCountdown.remaining : preparationRetryDelay;
  useEffect(() => {
    const until = Date.now() + preparationRetryDelay * 1000;
    if (!preparationRetryDelay) return;
    const timer = setInterval(() => {
      const remaining = Math.max(0, Math.ceil((until - Date.now()) / 1000));
      setPreparationCountdown({ lesson, remaining });
      if (!remaining) clearInterval(timer);
    }, 1000);
    return () => clearInterval(timer);
  }, [preparationRetryDelay, lesson]);
  useEffect(() => {
    if (!preparationSession || preparationRevision === undefined) return;
    const abort = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let polls = 0;
    let transientFailures = 0;
    const deadline = Date.now() + 45000;
    const poll = async () => {
      if (abort.signal.aborted || !active.current) return;
      try {
        const result = await TutorService.lessonPreparation({ sessionId: preparationSession, revision: preparationRevision }, false, abort.signal);
        if (abort.signal.aborted || !active.current) return;
        transientFailures = 0;
        setPreparationPaused(false);
        setLesson(current => current?.sessionId === preparationSession && current.revision === preparationRevision ? result : current);
        if (!result.preparingMath) {
          setFractionInput(startsWithFraction(result.step));
          return;
        }
        if (result.status !== 'PREPARING') return;
        if (++polls < 45 && Date.now() < deadline) timer = setTimeout(() => void poll(), 1000);
        else setPreparationPaused(true);
      } catch (failure) {
        if (abort.signal.aborted || !active.current) return;
        const error = failure as { code?: string; response?: { status?: number } };
        const transient = [408, 429, 500, 502, 503, 504].includes(error.response?.status || 0)
          || !error.response && ['ERR_NETWORK', 'ECONNABORTED', 'ETIMEDOUT', 'ECONNRESET'].includes(error.code || '');
        if (transient && ++transientFailures <= 3 && Date.now() < deadline) {
          timer = setTimeout(() => void poll(), Math.min(4000, 1000 * transientFailures, Math.max(0, deadline - Date.now())));
        } else setPreparationPaused(true);
      }
    };
    timer = setTimeout(() => void poll(), 500);
    return () => { abort.abort(); clearTimeout(timer); };
  }, [preparationSession, preparationRevision, preparationPoll]);
  const retryPreparation = () => {
    if (!lesson || preparationRetrySeconds > 0) return;
    void run('answer', signal => TutorService.lessonPreparation(lesson, true, signal), result => {
      setLesson(result); setPreparationPaused(false);
      setPreparationPoll(value => value + 1);
      setFractionInput(startsWithFraction(result.step));
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
      // The Web checkpoint stores text only; the existing masked-photo store retains the preview.
      if (Platform.OS !== 'web') void imageDraftPersistence.complete();
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
  }, [photoAllowed, imageUri, context?.purpose, draft, run, setError, setWorkConfirmed]);

  useFocusEffect(useCallback(() => {
    active.current = true;
    return () => { active.current = false; requestId.current += 1; controller.current?.abort(); running.current = false; };
  }, []));
  useFocusEffect(useCallback(() => {
    if (!initialized.current && photoAllowed) { initialized.current = true; void inspectPhoto(); }
  }, [photoAllowed, inspectPhoto]));

  const capture = (purpose?: 'ADD_PROBLEM' | 'ADD_WORK') => {
    cancel();
    if (purpose) {
      const pending: ImageDraft = { rawUri: '', uri: '', width: 0, height: 0, mimeType: 'image/jpeg', filename: 'pending.jpg', mode: 'MATH_TUTOR',
        lessonContext: { purpose, problemText: problem, workText: work, workImageUri: workImage, workImageCurrent, workLines, problemImageUri: problemImage,
          lessonId, uncertainWork, problemConfirmed, problemNeedsReview: sourceNeedsReview, workConfirmed, quizPreparationKey } };
      recognitionDraftStore.setDraft(pending);
    } else recognitionDraftStore.clearDraft();
    router.push({ pathname: '/camera' as any, params: { mode: 'MATH_TUTOR' } });
  };
  const start = () => {
    if (restoring || needsSourceClarification || problem.trim().length < 3 || problem.includes('[?]') || !problemConfirmed) return;
    resumeProgress.current = null;
    setTool(null);
    Keyboard.dismiss();
    const confirmedWork = workConfirmed && !work.includes('[?]') ? work : '';
    void run('lesson', signal => TutorService.startLesson(problem, confirmedWork,
      { problemConfirmed, workConfirmed: !!confirmedWork, guidedUnderstanding: true, startWithReading: true }, signal), result => {
      setProgressNotice('');
      setLesson(result); setSummaryStage(undefined); setReviewedStep(null); setHistoryIndex(null); setSubmittedAnswers([]); setAttempt(''); setAnswerEdited(false); setAnswerModeNotice(''); setSaved(false);
      setFractionInput(startsWithFraction(result.step));
      setHintPage(0); setHintOpen(false); setFocusedChoice(null);
    });
  };
  const onHasSolution = () => {
    if (busy || expired || restoring || problem.includes('[?]') || work.includes('[?]') || sourceClarification(problem)) return;
    if (work && work.trim()) {
      setWorkReviewCheckpoint(null);
      setAutoStartReview(true);
      setProblemConfirmed(true);
      setWorkConfirmed(true);
      setReviewStarted(true);
      setReviewFocused(true);
      setError('');
      requestAnimationFrame(() => scroll.current?.scrollTo({ y: 0, animated: false }));
    } else if (Platform.OS === 'web') {
      setWorkOptionsOpen(true);
    } else {
      Alert.alert(
        'Bài đã làm',
        'Ảnh hiện tại chưa nhận diện được phần bài giải viết tay của em. Em hãy chụp lại ảnh trọn vẹn cả đề bài và bài giải nhé!',
        [
          { text: 'Chụp lại cả đề và bài giải', onPress: () => capture() },
          { text: 'Nhập bài làm bằng chữ', onPress: () => edit('work') },
          { text: 'Đóng', style: 'cancel' },
        ]
      );
    }
  };
  const answer = (value: string, hint = false) => {
    if (!lesson || viewingHistory || running.current || expired || (hint ? hintCount >= hintLimit
      : !value.trim() || (!step?.choices.length && fractionInput && !/^-?\d+\/[1-9]\d*$/.test(value)))) return;
    void run(hint ? 'hint' : 'answer', signal => TutorService.answerLesson(lesson, value, hint, signal), result => {
      // Retain already displayed questions during a rolling server upgrade too.
      const completed = result.completed.map((item, index) => {
        const previous = index === lesson.stepIndex ? lesson.step : lesson.completed[index];
        return !item.question && previous?.question ? { ...item, question: previous.question, choices: previous.choices || [] } : item;
      });
      setLesson({ ...result, completed });
      setAnswerEdited(false);
      if (hint && result.status === 'HINT' && result.revealedHints?.length) {
        setHintPage(result.revealedHints.length - 1);
        setHintOpen(true);
      }
      if (result.stepIndex !== lesson.stepIndex) {
        setHistoryIndex(null);
        setAnswerModeNotice('');
        setSubmittedAnswers(result.completed.map((item, index) => index === lesson.stepIndex ? value : submittedAnswers[index] || item.answer));
        setQuestionDraft('');
        setHintPage(0); setHintOpen(false); setFocusedChoice(null);
        setFractionInput(startsWithFraction(result.step));
        setReviewedStep({ ...result.completed[result.completed.length - 1], question: lesson.step?.question || '',
          choices: [...(lesson.step?.choices || [])], studentAnswer: value });
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
    resumeProgress.current = null;
    setWorkReviewCheckpoint(null);
    cancel(); setError(''); setEditing(field); setLesson(null); setSaved(false); setReviewFocused(false); setReviewStarted(false);
    if (field === 'problem') setProblemConfirmed(false); else { setWorkConfirmed(false); setWorkLines([]); setWorkImageCurrent(false); }
  };
  const sourceRows = workReviewLines(work);
  // A changed/flattened transcription cannot reuse physical boxes from an older image reading.
  const boundLines = workLines.length === sourceRows.length && workLines.every((line, index) => trimWorkReviewLine(line.text) === sourceRows[index] && !line.division)
    ? workLines : sourceRows.map(text => ({ text, box: null, uncertain: text.includes('[?]') }));
  // The pupil has explicitly checked these readable symbols; keep the original OCR flags in workLines.
  const evidenceLines = workConfirmed && !work.includes('[?]') ? boundLines.map(line => ({ ...line, uncertain: false })) : boundLines;
  const workReviewMode = !!work && !division && !lesson;

  const openHint = () => {
    if (hintCount) { setHintOpen(true); return; }
    if (lesson?.revealedHints != null) { answer('', true); return; }
    if (!lesson) return;
    void run('hint', signal => TutorService.resumeLesson(lesson.sessionId, problem, signal), result => {
      setLesson(result);
      setFractionInput(startsWithFraction(result.step));
      if (result.revealedHints == null || !result.hintCount) {
        setError('Chưa mở được gợi ý cho phiên này. Em thử lại hoặc mở lại bài để tiếp tục nhé.');
      } else if (result.revealedHints.length) {
        setHintPage(0); setHintOpen(true);
      } else {
        setProgressNotice('Đã chuẩn bị gợi ý. Em chạm Gợi ý cách làm để xem nhé.');
      }
    });
  };
  const atReadingBoundary = !!lesson && lesson.understandingSteps === 3 && lesson.stepIndex === 3;
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
      backFallback={Platform.OS === 'web' && supplied ? '/(tabs)/lessons' : undefined}
      rightIcon="calculator-outline" rightAccessibilityLabel="Mở máy tính bỏ túi" onRightPress={() => setCalculatorOpen(true)} /></View>
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
    <View style={[styles.learningBody, spacious && styles.learningBodyWide]}>
    {spacious && lesson ? <ScrollView style={styles.lessonSidebar} contentContainerStyle={styles.lessonSidebarContent} showsVerticalScrollIndicator={false}>
      <Text style={styles.sidebarEyebrow}>HÀNH TRÌNH CỦA EM</Text><Text style={styles.sidebarTitle}>Hiểu từng bước</Text>
      {lesson.outline.map((title, index) => <View key={`${index}:${title}`} style={[styles.outlineRow, index === visibleStepIndex && styles.outlineCurrent]} accessible
        accessibilityLabel={`Bước ${index + 1}: ${title}. ${viewingHistory && index === visibleStepIndex ? 'Đang xem lại' : index < lesson.stepIndex ? 'Đã hoàn thành' : index === lesson.stepIndex ? 'Đang học' : 'Sắp tới'}`}>
        <View style={[styles.outlineNumber, index <= lesson.stepIndex && styles.outlineNumberActive]}>{index < lesson.stepIndex ? <Ionicons name="checkmark" size={16} color="#FFF" /> : <Text style={[styles.outlineNumberText, index === visibleStepIndex && { color: '#FFF' }]}>{index + 1}</Text>}</View>
        <Text style={[styles.outlineText, index === visibleStepIndex && { color: COLORS.primaryDark }]}>{title}</Text>
      </View>)}
      <AppIllustration source={MASCOT} style={styles.sidebarMascot} accessible={false} /><Text style={styles.sidebarCaption}>Cứ thử từng ý nhỏ. Robot luôn ở đây cùng em.</Text>
    </ScrollView> : null}
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      {lesson && !editing && problem ? <View style={[styles.reference, spacious && styles.referenceWide]}>
        <LessonProblem key={lesson.sessionId} problem={problem} imageUri={problemImage} onEdit={() => { setTool(null); edit('problem'); }} />
      </View> : null}
      <ScrollView ref={scroll} testID="lesson-working-area" contentContainerStyle={[styles.content, Platform.OS === 'web' && styles.webContent, spacious && styles.contentWide]} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        {restoring?<Text accessibilityLiveRegion="polite" style={styles.caption}>Đang kiểm tra bài đang học…</Text>:progressNotice?<Text accessibilityLiveRegion="polite" style={styles.caption}>{progressNotice}</Text>:null}
        {reviewFocused && !lesson ? <Pressable accessibilityRole="button" accessibilityLabel="Xem lại đề và bài làm" style={styles.reviewBack} onPress={() => setReviewFocused(false)}>
          <Ionicons name="chevron-back" size={18} color={COLORS.primaryDark} /><Text style={styles.link}>Xem lại đề và bài làm</Text></Pressable> : null}
        {!lesson && !reviewFocused && !reviewStarted ? <LinearGradient colors={['#EEE7FF', '#F5F0FF']} style={styles.hero}>
          <View style={styles.flex}><Text style={styles.eyebrow}>HỌC CÙNG MATHVISIONKID</Text>
            <Text style={styles.title}>{division ? 'Cùng kiểm tra phép chia' : !problem && work ? 'Thêm đề, hiểu trọn bài' : work ? 'Cùng nhìn lại bài em làm' : 'Hiểu cách làm, tự tìm lời giải'}</Text>
            <Text style={styles.body}>{division ? 'Đối chiếu với ảnh → kiểm tra → tự sửa chỗ chưa đúng.' : !problem && work ? 'Mình giữ bài em đã viết. Có đề gốc, mình mới đối chiếu được cách làm.' : work ? 'Đọc đúng đề và bài làm → nhận xét từng dòng → em tự sửa và kiểm tra lại.' : 'Hiểu đề → chọn cách làm → tự tính → kiểm tra lại.'}</Text></View>
          <AppIllustration source={MASCOT} style={styles.mascot} accessible={false} />
        </LinearGradient> : null}

        {error ? <RecoveryNotice title={expired ? 'Em cần đăng nhập lại' : 'Chưa thực hiện được'} message={error} actions={expired
          ? [{ label: 'Đăng nhập lại', onPress: () => router.push('/login' as any) }]
          : failedTask === 'read' && imageUri && photoAllowed ? [
            photoNeedsCrop
              ? { label: 'Chọn lại vùng bài toán', icon: 'crop-outline', onPress: () => router.push('/crop' as any), disabled: !!busy }
              : { label: 'Đọc lại ảnh', icon: 'refresh-outline', onPress: () => { void inspectPhoto(); }, disabled: !!busy },
            context?.purpose === 'ADD_WORK'
              ? { label: 'Nhập bài làm bằng chữ', icon: 'create-outline', onPress: () => edit('work'), disabled: !!busy }
              : { label: 'Nhập đề bằng chữ', icon: 'create-outline', onPress: () => edit('problem'), disabled: !!busy },
          ]
          : problem && !lesson && !workReviewMode ? [{ label: problemConfirmed && !problem.includes('[?]') ? 'Thử lại' : 'Kiểm tra đề', accessibilityLabel: 'Bắt đầu lại bài học', icon: 'refresh-outline', onPress: () => { if (problemConfirmed && !problem.includes('[?]')) start(); else edit('problem'); }, disabled: !!busy }]
          : imageUri && photoAllowed && !lesson ? [{ label: 'Thử lại', accessibilityLabel: 'Đọc lại ảnh bài làm', icon: 'refresh-outline', onPress: () => { void inspectPhoto(); }, disabled: !!busy }]
          : []} /> : null}

        {!!imageUri && !photoAllowed ? <View style={styles.card}><Text style={styles.body}>Em kiểm tra thông tin cá nhân trên ảnh trước nhé.</Text>
          <AppButton title="Kiểm tra thông tin cá nhân trên ảnh" onPress={() => router.replace('/privacy' as any)} /></View> : null}
        {photoAllowed && !reading && !error && !editing && !expired ? <AppButton title="Đọc lại ảnh" variant="secondary" onPress={() => void inspectPhoto()} /> : null}

        {reading?.kind === 'MULTIPLE' && reading.questions?.length && context?.purpose !== 'ADD_WORK' ? <View style={styles.card}>
          <QuestionPicker questions={reading.questions} onCrop={() => router.push('/crop' as any)} onChoose={question => {
            cancel(); setError(''); setLesson(null); setReviewedStep(null);
            setProblem(question.problemText); setProblemImage(imageUri); setProblemConfirmed(false);
            setSourceNeedsReview(question.uncertain);
            if (context?.purpose !== 'ADD_PROBLEM') { setWork(''); setWorkLines([]); setWorkImage(''); setUncertainWork(false); setWorkConfirmed(false); }
            setReading({ kind: 'PROBLEM', problemText: question.problemText, lines: [], needsProblem: false });
            scroll.current?.scrollTo({ y: 0, animated: false });
          }}/>
        </View> : invalidPhoto ? <View style={styles.card}>
          <Text style={styles.heading}>{reading?.needsCrop ? 'Chọn một vùng nhỏ hơn nhé' : reading?.kind === 'MULTIPLE' ? 'Mỗi lần một bài nhé' : 'Mình chưa đọc rõ bài toán'}</Text>
          <Text style={styles.body}>{reading?.needsCrop ? 'Ảnh có nhiều nội dung. Em chia thành từng phần để mình đọc đủ, rồi cùng xem từng bài nhé.' : 'Em chọn trọn một bài, gồm lời văn, số và hình vẽ nếu có.'}</Text>
          <AppButton title="Chọn lại vùng bài toán" onPress={() => router.push('/crop' as any)} />
          <Pressable style={styles.linkButton} accessibilityRole="button" onPress={() => edit('problem')}><Text style={styles.link}>Em muốn nhập đề bằng chữ</Text></Pressable>
        </View> : null}

        {!!(workImage || problemImage) && !lesson && !division && !reviewFocused && !reviewStarted && <View style={styles.photos}>
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
          <MathText style={styles.body}>{workLines.filter(line => !line.division).map(line => line.text).join('\n')}</MathText>
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
            else { setProblemConfirmed(!problem.includes('[?]')); setSourceNeedsReview(false); }
            setReading({ kind: work ? 'MIXED' : 'PROBLEM', problemText: problem, lines: [], needsProblem: !problem });
            setEditing(null);
          }} />
        </View> : null}

        {workReviewMode && problem && !editing && !reviewFocused && !invalidPhoto ? <WorkReviewPreparation
          problem={problem} work={work} problemImage={problemImage} workImage={workImage} photoCurrent={workImageCurrent}
          problemNeedsReview={sourceNeedsReview && !problemConfirmed}
          confirmLabel="Bài đã làm" disabled={!!busy || expired || restoring || !!sourceIssue}
          onEdit={edit} onConfirm={onHasSolution} /> : null}

        {!!problem && !editing && !lesson && !reviewFocused && !reviewStarted && !workReviewMode ? <View style={styles.card}>
          <View style={styles.problemHeader}>
            <View style={styles.problemToggle}>
              <View style={styles.problemIcon}><Ionicons name="document-text-outline" size={21} color={COLORS.primaryDark} /></View>
              <Text style={[styles.problemTitle, styles.flex]}>Đề bài của em</Text>
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh đề bài" onPress={() => edit('problem')}
              style={({ pressed }) => [styles.problemEdit, pressed && styles.problemPressed]}><Ionicons name="create-outline" size={20} color={COLORS.primaryDark} /><Text style={styles.link}>Chỉnh sửa</Text></Pressable>
          </View>
          <View style={styles.problemContent} nativeID="confirmed-problem-body">
            <MathText style={[styles.body, styles.confirmedProblemText]}>{problemPresentation(problem)}</MathText>
          </View>
          {!lesson ? <>
            {sourceIssue ? <View style={styles.hintCard} accessibilityLiveRegion="polite">
              <Text style={styles.question}>Cần làm rõ một chỗ trong đề</Text>
              <Text style={styles.body}>{sourceIssue.message}</Text>
              {sourceIssue.mixedPreview ? <>
                <MathText style={styles.body}>{problemPresentation(sourceIssue.mixedPreview)}</MathText>
                <AppButton title="Đúng, đây là các hỗn số" variant="secondary" onPress={() => {
                  setProblem(sourceIssue.mixedPreview!); setProblemConfirmed(false); setSaved(false); setError('');
                }} />
              </> : null}
              <AppButton title="Chỉnh chỗ chưa rõ trong đề" variant="ghost" onPress={() => edit('problem')} />
            </View> : null}
            {sourceNeedsReview && !problemConfirmed ? <Text style={styles.error} accessibilityRole="alert">Có chỗ cần kiểm tra lại với ảnh. Em đối chiếu số, đơn vị và hình; chỉnh lại nếu cần rồi xác nhận nhé.</Text> : null}
            {Platform.OS === 'web' && problem.includes('[?]') ? <Text style={styles.error} accessibilityRole="alert">Có chỗ chưa chắc trong đề. Em chọn chỉnh đề, đối chiếu với ảnh và bỏ dấu [?] sau khi sửa nhé.</Text> : null}
            <Text style={styles.body}>{Platform.OS === 'web'
              ? 'Bố mẹ và con có thể cùng đọc đề, đối chiếu các số và đơn vị rồi chỉnh chỗ chưa đúng. Khi đề đã đúng, để con tự trả lời từng bước nhé.'
              : 'Em kiểm tra lời văn, các số và đơn vị. Nếu chưa giống ảnh, chọn chỉnh đề trước nhé.'}</Text>
            <Pressable accessibilityRole="checkbox" accessibilityLabel="Em đã kiểm tra đề bài và các số"
              aria-checked={problemConfirmed} accessibilityState={{ checked: problemConfirmed, disabled: !!busy || problem.includes('[?]') }}
              disabled={!!busy || problem.includes('[?]')} style={styles.confirm}
              onPress={() => setProblemConfirmed(value => !value)}>
              <Ionicons name={problemConfirmed ? 'checkbox' : 'square-outline'} size={26} color={COLORS.primaryDark} />
              <Text style={[styles.body, styles.flex]}>Em đã kiểm tra đề bài và các số</Text>
            </Pressable>
          </> : null}
          {problem.includes('[?]') ? <Text style={styles.error}>Có dữ kiện chưa rõ. Em chỉnh lại chỗ đánh dấu trước nhé.</Text> : !lesson && !busy ? (
            <View style={styles.actionButtons}>
              <AppButton
                title="Bắt đầu từng bước"
                onPress={start}
                disabled={!!sourceIssue || restoring || expired || !!invalidPhoto || !problemConfirmed}
              />
              <AppButton
                title="Bài đã làm"
                variant="secondary"
                style={styles.reviewAction}
                onPress={onHasSolution}
                disabled={restoring || expired || !!invalidPhoto}
                accessibilityLabel="Bài đã làm"
              />
            </View>
          ) : null}
        </View> : null}

        {problem && work && !editing && !division && !invalidPhoto && !lesson && reviewStarted ? <View style={!reviewFocused ? styles.hidden : undefined}><StudentWorkReview
          problemText={problem} workText={work} imageUri={workImage} photoCurrent={workImageCurrent} lines={evidenceLines}
          enabled={problemConfirmed && workConfirmed && !problem.includes('[?]') && !work.includes('[?]')}
          autoStart={autoStartReview}
          checkpoint={workReviewCheckpoint} onCheckpoint={checkpointScope ? setWorkReviewCheckpoint : undefined}
          disabled={!!busy || expired} onCaptureWork={() => capture('ADD_WORK')}
          onSessionExpired={() => { setExpired(true); setError('Phiên học đã hết hạn. Em đăng nhập lại để tiếp tục nhé.'); }}
          onReviseWork={text => {
            setWorkReviewCheckpoint(null);
            cancel(); Keyboard.dismiss(); setWork(text); setWorkLines([]); setWorkImageCurrent(false);
            setWorkConfirmed(true); setUncertainWork(false); setSaved(false);
            requestAnimationFrame(() => scroll.current?.scrollTo({ y: 0, animated: false }));
          }} /></View> : null}
        {problem && work && reviewStarted && !lesson && !editing && !division && !invalidPhoto ?
          <AppButton title={saved ? 'Đã lưu bài của em' : 'Lưu bài để học tiếp'} loadingTitle="Đang lưu bài…" variant="secondary" disabled={saved || saving} loading={saving} onPress={() => void archive()} /> : null}

        {lesson && !editing ? <>
          <View style={styles.progressRow}><View style={styles.rail} accessible accessibilityRole="progressbar" accessibilityLabel="Tiến trình bài học"
            accessibilityValue={{ min: 0, max: lesson.outline.length, now: lesson.stepIndex, text: `Đã hoàn thành ${lesson.stepIndex} trên ${lesson.outline.length} bước` }}>
            {lesson.outline.map((_, index) => <View key={index} style={[styles.railStep, index < lesson.stepIndex && styles.railActive]} />)}
          </View><Text style={styles.progressCount}>Đã xong {lesson.stepIndex}/{lesson.outline.length} bước</Text></View>
          {currentViewIndex > 0 ? <View style={styles.stepNavigation}>
            <Pressable accessibilityRole="button" accessibilityLabel="Bước trước" disabled={!!busy || visibleStepIndex === 0}
              accessibilityState={{ disabled: !!busy || visibleStepIndex === 0 }} onPress={() => {
                if (atReadingBoundary && !viewingHistory && !summaryVisible && !displayedReview) {
                  setSummaryStage('summary'); scroll.current?.scrollTo({ y: 0, animated: false });
                } else if (summaryVisible) {
                  setHistoryIndex(2); scroll.current?.scrollTo({ y: 0, animated: false });
                } else showHistory(visibleStepIndex - 1);
              }}
              style={({ pressed }) => [styles.historyButton, pressed && styles.problemPressed, (!!busy || visibleStepIndex === 0) && styles.historyDisabled]}>
              <Ionicons name="arrow-back" size={18} color={COLORS.primaryDark} accessible={false} /><Text style={styles.historyLabel}>Bước trước</Text>
            </Pressable>
            {viewingHistory ? <Pressable accessibilityRole="button" accessibilityLabel={step || reviewedStep ? 'Về bước đang học' : 'Về bài giải'}
              onPress={() => showHistory(null)} disabled={!!busy} accessibilityState={{ disabled: !!busy }}
              style={({ pressed }) => [styles.historyButton, pressed && styles.problemPressed]}>
              <Text style={styles.historyLabel}>{step || reviewedStep ? 'Về bước đang học' : 'Về bài giải'}</Text><Ionicons name="arrow-forward" size={18} color={COLORS.primaryDark} accessible={false} />
            </Pressable> : null}
          </View> : null}
          {summaryVisible ? <View testID="lesson-summary-screen" style={styles.card}>
            <Text accessibilityRole="header" style={styles.heading}>Tóm tắt bài toán</Text>
            <Text style={styles.body}>Trước khi giải, mình cùng xem lại những điều đề bài đã cho và điều cần tìm nhé!</Text>
            <ProblemSummary lesson={lesson} compact />
            {lesson.preparingMath ? <>
              <Text style={styles.caption}>Phần hiểu đề đã được giữ. Mình đang chuẩn bị các bước giải cho em.</Text>
              {lesson.status === 'RETRYABLE' || lesson.status === 'UNAVAILABLE' || preparationPaused
                ? <AppButton title="Thử chuẩn bị lại" onPress={retryPreparation} loading={busy === 'answer'} disabled={!!busy || expired || preparationRetrySeconds > 0} />
                : <ActivityIndicator accessibilityLabel="Đang chuẩn bị các bước giải" color={COLORS.primaryDark} />}
              {preparationRetrySeconds > 0 ? <Text style={styles.caption}>Em có thể thử chuẩn bị lại sau {preparationRetrySeconds} giây.</Text> : null}
            </> : null}
            <AppButton title="Bắt đầu giải" disabled={!!busy || expired || !step || lesson.preparingMath} onPress={() => {
              if (reviewedStep) { setAttempt(''); setAnswerEdited(false); }
              setSummaryStage('solving'); setReviewedStep(null); setHistoryIndex(null);
              scroll.current?.scrollTo({ y: 0, animated: false });
            }} />
          </View> : <>
          {lesson.preparingMath && step ? <Text style={styles.caption}>Em đọc đề trước nhé, phần hướng dẫn đang được chuẩn bị.</Text> : null}
          {lesson.preparingMath && !step && !viewingHistory && !displayedReview ? <View style={styles.card} accessibilityLiveRegion="polite">
            <View ref={stepHeading} tabIndex={-1} accessible accessibilityRole="header" accessibilityLabel="Em đã hiểu đề"><Text style={styles.heading}>Em đã hiểu đề</Text></View>
            <MathText style={styles.body}>{lesson.feedback}</MathText>
            <AppButton title="Tiếp tục" onPress={() => setSummaryStage('summary')} />
            {lesson.status === 'RETRYABLE' || lesson.status === 'UNAVAILABLE' || preparationPaused ? <AppButton title="Thử chuẩn bị lại" loadingTitle="Đang chuẩn bị lại bài…" onPress={retryPreparation} loading={busy === 'answer'} disabled={!!busy || expired || preparationRetrySeconds > 0} /> : null}
            {preparationRetrySeconds > 0 ? <Text style={styles.caption}>Em có thể thử chuẩn bị lại sau {preparationRetrySeconds} giây.</Text> : null}
            {lesson.status === 'PREPARING' && !preparationPaused ? <ActivityIndicator accessibilityLabel="Đang chuẩn bị các bước giải" color={COLORS.primaryDark} /> : null}
          </View> : displayedReview ? <View style={styles.card} accessibilityLiveRegion="polite" onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.eyebrow}>{viewingHistory ? `XEM LẠI · BƯỚC ${visibleStepIndex + 1}` : displayedReview.kind === 'UNDERSTAND' ? 'CÙNG HIỂU ĐỀ' : `ĐÃ KIỂM TRA BƯỚC ${lesson.stepIndex - (lesson.understandingSteps || 0)}`}</Text>
            <View ref={stepHeading} tabIndex={-1} accessible accessibilityRole="header" accessibilityLabel={displayedReview.title}>
              <Text style={styles.heading}>{displayedReview.title}</Text>
            </View>
            <MathText style={styles.question}>{displayedReview.question}</MathText>
            {displayedReview.choices.length ? displayedReview.choices.map(choice => {
              const selected = choice === displayedReview.studentAnswer;
              return <Pressable key={choice} accessibilityRole="button" accessibilityLabel={choice} disabled
                accessibilityHint={selected ? 'Em đã chọn đáp án này và đã được kiểm tra đúng.' : undefined}
                aria-pressed={selected} accessibilityState={{ selected, disabled: true }} style={[styles.choice, selected && styles.choiceCorrect]}>
                <View style={[styles.flex, { marginRight: 8 }]}><MathText style={styles.choiceText}>{choice}</MathText>
                  {selected ? <Text style={styles.chosenCorrect}>Em đã chọn · Đúng</Text> : null}</View>
                <Ionicons name={selected ? 'checkmark-circle' : 'ellipse-outline'} size={20} color={selected ? '#24794E' : '#B6A9CD'} accessible={false} />
              </Pressable>;
            }) : <View testID="checked-student-answer" style={styles.checkedAnswer}><Text style={styles.caption}>{viewingHistory ? 'EM ĐÃ NHẬP' : 'EM VỪA NHẬP'}</Text>
              <MathText style={styles.body}>{displayedReview.studentAnswer + (displayedReview.unit ? ` ${displayedReview.unit}` : '')}</MathText></View>}
            {viewingHistory && displayedReview.explanation ? <MathText style={styles.body}>{displayedReview.explanation}</MathText> : null}
            {viewingHistory ? <View style={styles.historyChecked}><Ionicons name="checkmark-circle" size={20} color="#24794E" accessible={false} />
              <Text style={styles.chosenCorrect}>Bước này đã được kiểm tra đúng</Text></View> : <CorrectAnswerFeedback key={`feedback:${lesson.sessionId}:${lesson.stepIndex}`} message="Đúng rồi!" detail={displayedReview.kind === 'UNDERSTAND' ? lesson.feedback || displayedReview.explanation : displayedReview.explanation || lesson.feedback} />}
            {displayedReview.expression ? <><Text style={styles.heading}>{lesson.outline.length === 1 ? 'Đối chiếu kết quả' : 'Viết vào bài giải'}</Text><SolutionLine item={displayedReview} /></> : null}
            {!viewingHistory&&displayedReview.kind!=='UNDERSTAND'&&lesson.completed.filter(item=>item.kind!=='UNDERSTAND').length%2===0?<ComprehensionCheck key={`check:${lesson.sessionId}:${lesson.revision}`} sessionId={lesson.sessionId} revision={lesson.revision}/>:null}
            <AppButton title={atReadingBoundary && displayedReview.kind === 'UNDERSTAND' && visibleStepIndex === 2 ? 'Tiếp tục' : viewingHistory ? 'Bước tiếp theo' : !step ? 'Xem bài giải' : 'Tiếp tục bước tiếp theo'} disabled={!!busy || (!viewingHistory && expired)} onPress={() => {
              if (atReadingBoundary && displayedReview.kind === 'UNDERSTAND' && visibleStepIndex === 2) {
                setSummaryStage('summary'); setHistoryIndex(null); return;
              }
              if (viewingHistory) { showHistory(visibleStepIndex + 1 < currentViewIndex ? visibleStepIndex + 1 : null); return; }
              setReviewedStep(null); setAttempt(''); setAnswerEdited(false); scroll.current?.scrollTo({ y: 0, animated: false });
            }} />
          </View> : step ? <View style={[styles.card, styles.activeStep]} accessibilityLiveRegion="polite" onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <Text style={styles.eyebrow}>{step.kind === 'UNDERSTAND' ? 'HIỂU ĐỀ' : 'CÙNG GIẢI'} · BƯỚC {step.kind === 'UNDERSTAND' ? lesson.stepIndex + 1 : lesson.stepIndex + 1 - (lesson.understandingSteps || 0)} / {step.kind === 'UNDERSTAND' ? lesson.understandingSteps : lesson.outline.length - (lesson.understandingSteps || 0)}</Text>
            <View style={styles.stepPrompt}><View ref={stepHeading} tabIndex={-1} accessible accessibilityRole="header" accessibilityLabel={step.title}><Text style={styles.heading}>{step.title}</Text></View>
            {step.kind === 'UNDERSTAND' ? <Text style={styles.stepCaption}>Hiểu đề trước khi tính</Text>
              : lesson.outline.length === 1 ? <Text style={styles.stepCaption}>Làm xong, em kiểm tra lại kết quả nhé!</Text> : null}</View>
            {step.kind === 'UNDERSTAND' && !visibleHint ? <MathText style={styles.body}>{step.explanation}</MathText> : null}
            <MathText style={styles.question}>{step.question}</MathText>
            {showCalculation ? <View onLayout={event => { calculationPosition.current = event.nativeEvent.layout.y; }}>
              <LessonCalculation expression={step.expression} />
            </View> : null}
            {visibleHint ? <LessonHint text={visibleHint} level={hintPage + 1} count={hintLimit} busy={!!busy || expired}
              onPrevious={hintPage > 0 ? () => setHintPage(value => value - 1) : undefined}
              onNext={hintPage < hintCount - 1 || hintCount < hintLimit
                ? () => hintPage < hintPages.length - 1 ? setHintPage(value => value + 1) : answer('', true) : undefined}
              onClose={() => setHintOpen(false)}
              onExplain={step.kind === 'UNDERSTAND' || showCalculation ? () => setTool('hint') : undefined} /> : null}
            {!visibleHint && step.kind !== 'UNDERSTAND' && step.explanation ? <MathText style={styles.stepNoteText}>{step.explanation}</MathText> : null}
            {step.choices.length ? step.choices.map((choice, index) => <Pressable key={choice} ref={index === 0 ? firstChoice : undefined} accessibilityRole="button" accessibilityLabel={choice} disabled={!!busy || expired}
              aria-pressed={attempt === choice} accessibilityState={Platform.OS === 'web' ? { disabled: !!busy || expired } : { selected: attempt === choice, disabled: !!busy || expired }}
              accessibilityHint={attempt === choice && lesson.status === 'TRY_AGAIN' && !answerEdited ? 'Em vừa chọn đáp án này. Chưa đúng, em có thể chọn lại.' : undefined}
              onFocus={() => setFocusedChoice(choice)} onBlur={() => setFocusedChoice(null)}
              style={[styles.choice, attempt === choice && styles.choiceSelected,
                attempt === choice && lesson.status === 'TRY_AGAIN' && !answerEdited && styles.choiceIncorrect,
                focusedChoice === choice && styles.choiceFocused]} onPress={() => {
                if (running.current || expired) return;
                setAttempt(choice); setAnswerEdited(true);
                // Every choice is checked by the authority that also explains it.
                answer(choice);
              }}>
              <View style={[styles.flex, { marginRight: 8 }]}><MathText style={styles.choiceText}>{choice}</MathText>
                {attempt === choice ? <Text accessibilityLiveRegion="polite" style={styles.caption}>{busy === 'answer' ? 'Đang kiểm tra đáp án này…' : `Em vừa chọn${lesson.status === 'TRY_AGAIN' && !answerEdited ? ' · Chưa đúng' : ''}`}</Text> : null}</View>
              {attempt === choice && busy === 'answer' ? <ActivityIndicator size="small" color={COLORS.primaryDark} accessibilityLabel="Đang kiểm tra đáp án đã chọn" />
                : attempt === choice ? <Ionicons name={lesson.status === 'TRY_AGAIN' && !answerEdited ? 'close-circle' : 'radio-button-on'} size={18} color={lesson.status === 'TRY_AGAIN' && !answerEdited ? '#AC4936' : COLORS.primaryDark} accessible={false} /> : null}
            </Pressable>) : <>
              {step.answerFormat == null ? <Pressable style={styles.answerMode} accessibilityRole="button"
                accessibilityLabel={fractionInput ? 'Nhập số thường' : 'Nhập kết quả phân số'} disabled={!!busy || expired}
                onPress={() => changeAnswerMode(!fractionInput)}>
                <Text style={styles.answerModeLabel}>{fractionInput ? 'Nhập số thường' : 'Nhập phân số'}</Text>
              </Pressable> : null}
              <View style={styles.answerRow}>
              {fractionInput ? <View style={styles.fractionAnswer}>
                <TextInput ref={answerInput} style={styles.fractionNumber} accessibilityLabel="Tử số câu trả lời" value={attempt.split('/')[0]} keyboardType="numeric" maxLength={13}
                  placeholder="Tử số" editable={!busy && !expired} onFocus={() => scroll.current?.scrollToEnd({ animated: true })} onChangeText={value => changeAttempt(`${value}/${attempt.split('/')[1] || ''}`)} />
                <View style={styles.fractionBar} />
                <TextInput style={styles.fractionNumber} accessibilityLabel="Mẫu số câu trả lời" value={attempt.split('/')[1] || ''} keyboardType="number-pad" maxLength={12}
                  placeholder="Mẫu số" editable={!busy && !expired} aria-invalid={fractionDenominator === '0'} onFocus={() => scroll.current?.scrollToEnd({ animated: true })}
                  onChangeText={value => changeAttempt(`${attempt.split('/')[0]}/${value}`)} onSubmitEditing={() => answer(attempt)} />
              </View> : <TextInput ref={answerInput} style={styles.numberInput} accessibilityLabel="Câu trả lời của em" value={attempt} onChangeText={changeAttempt} keyboardType={step.answerFormat === 'INTEGER' ? 'numeric' : 'decimal-pad'}
                maxLength={30} placeholder="Em tính được…" placeholderTextColor={COLORS.textMuted} editable={!busy && !expired} onFocus={() => scroll.current?.scrollToEnd({ animated: true })} onSubmitEditing={() => answer(attempt)} />
              }
              {step.unit && !(fractionInput && step.unit === 'phần') ? <Text style={styles.unit}>{step.unit}</Text> : null}
              </View>
              {fractionInput ? <Text style={styles.caption}>Em nhập tử và mẫu; không làm tròn số thập phân.</Text> : null}
              {fractionInput && fractionDenominator === '0' ? <Text accessibilityRole="alert" style={styles.error}>Mẫu số phải khác 0. Em kiểm tra lại mẫu số nhé.</Text> : null}
              {answerModeNotice ? <Text style={styles.caption} accessibilityLiveRegion="polite">{answerModeNotice}</Text> : null}
              <AppButton title="Kiểm tra bước này" loadingTitle="Đang kiểm tra đáp án…" style={styles.stepButton} onPress={() => answer(attempt)} disabled={!validAttempt || !!busy || expired} loading={busy === 'answer'} /></>}
            {busy === 'answer' || busy === 'hint' ? <View style={styles.checking} accessibilityLiveRegion="polite" accessibilityState={{ busy: true }}>
              <ActivityIndicator size="small" color={COLORS.primaryDark} /><Text style={styles.checkingText}>{busy === 'hint' ? 'Đang mở gợi ý…' : 'Đang kiểm tra câu trả lời…'}</Text>
            </View> : null}
            {!visibleHint && (hintLimit > 0 || lesson.revealedHints == null) ? <AppButton title="Gợi ý cách làm bước này" icon={<Ionicons name="bulb-outline" size={18} color={COLORS.primaryDark} accessible={false} />} loading={busy === 'hint'} loadingTitle="Đang mở gợi ý…" style={styles.stepButton} variant="secondary" onPress={openHint} disabled={!!busy || expired} /> : null}
            {lesson.status === 'TRY_AGAIN' && !answerEdited && lesson.feedback ? <View accessibilityRole="alert" style={styles.incorrectFeedback} testID="incorrect-answer-feedback">
              <View style={styles.row}><Ionicons name="refresh-circle-outline" size={24} color="#975A24" accessible={false} /><Text style={styles.question}>Em thử xem lại nhé!</Text></View>
              <MathText style={styles.body}>{lesson.feedback}</MathText>
              <AppButton title="Thử lại" variant="ghost" onPress={() => { setAnswerEdited(true); if (step.choices.length) { setAttempt(''); firstChoice.current?.focus(); } else answerInput.current?.focus(); }} />
            </View> : null}
          </View> : <View style={styles.card} onLayout={e => { lessonPosition.current = e.nativeEvent.layout.y; }}>
            <View ref={stepHeading} tabIndex={-1} accessible accessibilityRole="header" accessibilityLabel="Bài giải"><Text style={styles.heading}>Bài giải</Text></View><Text style={styles.body}>Đây là các bước em đã tự tính và kiểm tra. Em có thể viết lại vào vở.</Text>
            {lesson.completed.filter(item => item.expression).map((item, index) => <SolutionLine key={index} item={item} />)}
            {lesson.conclusion ? <MathText style={styles.question}>{lesson.conclusion}</MathText> : null}
            {work ? <Text style={styles.body}>Em đối chiếu những bước vừa học với bài trong ảnh. Các phép tính vừa nhập đã được kiểm tra; nét chữ và hình vẽ vẫn cần nhìn lại.</Text> : null}
          </View>}
          </>}
        </> : null}
        {solutionVisible && lesson ? <QuizAfterLearningButton sourceType="LESSON" sourceId={lesson.sessionId} /> : null}
        {solutionVisible ? <AppButton title="Về trang chủ" variant="outlined" onPress={() => router.replace('/(tabs)')} /> : null}
      </ScrollView>
      {lesson && !editing && !keyboardVisible ? <View style={[styles.toolsDock, spacious && styles.toolsDockWide]} testID="lesson-fixed-tools">
        <View style={styles.tools}>
          {([['audio', 'volume-high-outline', 'Nghe giảng'], ['ask', 'mic-outline', 'Hỏi bài'], ['menu', 'ellipsis-horizontal', 'Xem thêm']] as const).map(([value, icon, label]) => <Pressable
            key={value} accessibilityRole="button" accessibilityLabel={label} disabled={expired} accessibilityState={{ disabled: expired }} style={({ pressed }) => [styles.tool, pressed && { backgroundColor: '#F0E8FF' }, expired && { opacity: .5 }]} onPress={() => setTool(value)}>
            <Ionicons name={icon} size={22} color={COLORS.primaryDark} accessible={false} /><Text style={styles.toolLabel}>{label}</Text>
          </Pressable>)}
        </View>
      </View> : null}
    </KeyboardAvoidingView></View>
    {workOptionsOpen ? <LessonSheet title="Thêm bài em đã làm" compact onClose={() => setWorkOptionsOpen(false)}>
      <Text style={styles.body}>Mình chưa có phần bài làm của em. Em chụp thêm hoặc nhập những bước đã viết nhé.</Text>
      <AppButton title="Chụp thêm bài làm" onPress={() => { setWorkOptionsOpen(false); capture('ADD_WORK'); }} />
      <AppButton title="Nhập bài làm bằng chữ" variant="secondary" onPress={() => { setWorkOptionsOpen(false); edit('work'); }} />
    </LessonSheet> : null}
    {lesson && tool && !expired && !editing ? <LessonSheet compact={tool === 'parent'} appearance={tool === 'hint' ? 'hint' : undefined} title={{ audio: 'Nghe giảng', ask: 'Hỏi bài', menu: 'Em cần gì thêm?', work: 'Bài em đã viết', summary: 'Tóm tắt đề', hint: 'Cùng hiểu gợi ý', parent: 'Gợi ý cho bố mẹ' }[tool]} onClose={() => setTool(null)}>
      {tool === 'hint' && step ? <HintSheetContent key={`${owner}:${lesson.sessionId}:${lesson.stepIndex}:${hintPage}`}
        hint={visibleHint} visual={problemConfirmed && showCalculation && step.kind !== 'UNDERSTAND' && !displayedReview
          ? buildHintVisual(problem, step.expression) : null}>
        <HintCheckIn expression={showCalculation ? step.expression : ''} reading={step.kind === 'UNDERSTAND'} depth={hintPage + 1}
          hint={visibleHint} stepTitle={step.title} stepQuestion={step.question} unit={step.unit}
          onReady={() => { setTool(null); if (step.choices.length) firstChoice.current?.focus(); else answerInput.current?.focus(); }} />
      </HintSheetContent> : null}
      {tool === 'audio' ? <LessonListening scope={JSON.stringify([owner, lesson.sessionId, visibleStepIndex, lesson.revision, hintCount, !!displayedReview])}
        sessionId={lesson.sessionId} revision={lesson.revision} stepIndex={summaryVisible ? 2 : Math.min(visibleStepIndex, Math.max(0, lesson.outline.length - 1))}
        step={summaryVisible ? { kind: 'UNDERSTAND', title: 'Tóm tắt bài toán', expression: '' } : displayedReview || step}
        onReturn={returnFromTool}
        paragraphs={narrationParts} preparedFallback={preparedCurriculumSpeech} /> : null}
      {tool === 'ask' ? <LessonQuestion initialQuestion={viewingHistory ? '' : questionDraft} onDraftChange={viewingHistory ? undefined : setQuestionDraft} onReturn={returnFromTool} key={`${owner}:${lesson.sessionId}:${lesson.revision}:${visibleStepIndex}:${!!displayedReview}`} scope={`${owner}:${lesson.sessionId}:${lesson.revision}:${visibleStepIndex}:${!!displayedReview}`}
        sessionId={lesson.sessionId} revision={lesson.revision} stepIndex={summaryVisible ? 2 : Math.min(visibleStepIndex, Math.max(0, lesson.outline.length - 1))} /> : null}
      {tool === 'summary' ? <ProblemSummary lesson={lesson} compact /> : null}
      {tool === 'parent' && step && !displayedReview && !summaryVisible ? <>
        <Text accessibilityRole="header" style={styles.heading}>Bước {visibleStepIndex + 1}/{lesson.outline.length} · {step.title}</Text>
        <MathText style={styles.body}>{step.question}</MathText>
        <Text style={styles.body}>{step.kind === 'UNDERSTAND'
          ? 'Hỏi con: “Đề cho biết gì? Đề hỏi gì?” Mời con chỉ vào câu trong đề và kể lại bằng lời của mình.'
          : 'Hỏi con: “Con định làm thế nào?” Cho con giải thích cách nghĩ và thử lại. Nếu còn bí, mời con mở một gợi ý.'}</Text>
      </> : null}
      {tool === 'work' ? <>{workImage ? <Image source={{ uri: workImage }} style={[styles.photo, { height: 220 }]} resizeMode="contain" accessibilityLabel={workImageCurrent ? 'Ảnh bài em đã làm' : 'Ảnh bài làm trước khi sửa bằng chữ'} /> : null}
        {!workConfirmed ? <Text style={styles.error}>Bài làm chưa được xác nhận; mình đang hướng dẫn từ đề đã kiểm tra. Có chỗ chưa đọc rõ, em đối chiếu lại với ảnh nhé.</Text> : null}
        <MathText style={styles.body}>{work}</MathText>
        <AppButton title="Chỉnh chỗ chưa đọc đúng" variant="secondary" onPress={() => { setTool(null); edit('work'); }} /></> : null}
      {tool === 'menu' ? <>
        {Platform.OS === 'web' && step && !displayedReview && !summaryVisible
          ? <AppButton title="Gợi ý cho bố mẹ" variant="secondary" onPress={() => setTool('parent')} /> : null}
        {work ? <AppButton title="Xem bài em đã viết" variant="secondary" onPress={() => setTool('work')} /> : null}
        {lesson.understandingSteps === 3 && lesson.stepIndex >= 2 ? <AppButton title="Xem lại tóm tắt đề" variant="secondary" onPress={() => setTool('summary')} /> : null}
        <AppButton title={saved ? 'Đã lưu bài của em' : 'Lưu bài để học tiếp'} loadingTitle="Đang lưu bài…" variant="secondary" disabled={saved || saving} loading={saving} onPress={() => void archive()} />
        <AppButton title="Chụp bài em đã làm để nhận xét" variant="secondary" onPress={() => { setTool(null); capture('ADD_WORK'); }} />
        <AppButton title="Chụp bài khác" variant="ghost" onPress={() => { setTool(null); capture(); }} /></> : null}
    </LessonSheet> : null}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  hidden: { display: 'none' },
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
  webContent: { paddingBottom: 104 },
  reference: { width: '100%', maxWidth: 680, alignSelf: 'center', paddingHorizontal: 16, paddingTop: 4, paddingBottom: 0 }, referenceWide: { maxWidth: 820, paddingHorizontal: 24 },
  toolsDock: { flexShrink: 0, width: '100%', maxWidth: 680, alignSelf: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, backgroundColor: COLORS.background, borderTopWidth: 1, borderTopColor: '#EAE2F7' },
  toolsDockWide: { maxWidth: 820, paddingHorizontal: 24 },
  tools: { flexDirection: 'row', gap: 8, padding: 6, borderRadius: 20, backgroundColor: '#F1EAFB' },
  tool: { flex: 1, minHeight: 52, justifyContent: 'center', alignItems: 'center', gap: 4, borderRadius: 14, backgroundColor: '#FFFFFF' },
  toolLabel: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark },
  checking: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8 },
  checkingText: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, color: COLORS.primaryDark },
  hero: { padding: 22, borderRadius: 26, flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderColor: '#E8DEF7', minHeight: 181 },
  mascot: { width: 94, height: 112 }, eyebrow: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold, fontSize: 11, letterSpacing: 1 },
  title: { fontSize: 23, lineHeight: 29, fontFamily: FONTS.extraBold, color: COLORS.textPrimary, marginVertical: 8 },
  heading: { fontSize: 17, lineHeight: 23, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  stepPrompt: { borderRadius: 12, padding: 12, gap: 3, backgroundColor: '#F1EAFF' }, stepCaption: { fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 18, color: COLORS.textSecondary },
  body: { fontSize: 14, lineHeight: 21, color: COLORS.textSecondary, fontFamily: FONTS.regular },
  confirmedProblemText: { fontFamily: FONTS.bold, color: COLORS.textPrimary, fontSize: 16, lineHeight: 24 },
  reviewAction: { backgroundColor: '#EAF2FF', borderColor: '#C9DDF7', borderWidth: 1 },
  actionButtons: { gap: 10 },
  card: { backgroundColor: COLORS.surface, borderRadius: 18, padding: 14, gap: 12, borderWidth: 1, borderColor: '#EAE2F7', ...SHADOWS.small },
  activeStep: { gap: 10 }, stepNote: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, borderRadius: 13, backgroundColor: '#FFF9ED', padding: 10 },
  reviewBack: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 7 },
  stepNoteText: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: '#79698C' }, stepButton: { minHeight: 48, paddingVertical: 11, borderRadius: 16 },
  error: { color: '#963E22', fontSize: 15, lineHeight: 22, fontFamily: FONTS.semiBold },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  problemHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  problemToggle: { flex: 1, minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 14 },
  problemIcon: { width: 40, height: 40, borderRadius: 13, backgroundColor: COLORS.surfaceSubdued, alignItems: 'center', justifyContent: 'center' },
  problemTitle: { fontSize: 17, lineHeight: 23, color: COLORS.textPrimary, fontFamily: FONTS.extraBold },
  problemEdit: { minHeight: 48, paddingHorizontal: 8, borderRadius: 15, borderWidth: 1, borderColor: '#E8E1F4', flexDirection: 'row', gap: 4, alignItems: 'center', justifyContent: 'center' },
  problemPressed: { backgroundColor: COLORS.surfaceSubdued },
  problemContent: { borderTopWidth: 1, borderColor: '#EEE8F7', paddingTop: 14 },
  photos: { flexDirection: 'row', gap: 12 }, photoCard: { flex: 1, backgroundColor: COLORS.surface, borderRadius: 18, padding: 8, gap: 5 },
  photo: { width: '100%', height: 120, borderRadius: 12, backgroundColor: '#F1EEF8' },
  caption: { fontSize: 12, color: COLORS.textSecondary, fontFamily: FONTS.bold },
  link: { fontSize: 15, lineHeight: 22, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  linkButton: { minHeight: 44, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 8 },
  input: { minHeight: 130, borderRadius: 16, padding: 16, backgroundColor: '#F8F5FF', borderWidth: 1, borderColor: '#D7CDF2', fontFamily: FONTS.regular, fontSize: 16, color: COLORS.textPrimary, textAlignVertical: 'top' },
  workCard: { backgroundColor: '#F0EBFC', padding: 16, borderRadius: 18, gap: 10 },
  confirm: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 12 },
  progressRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 4 }, progressCount: { color: '#9D8EB4', fontFamily: FONTS.bold, fontSize: 13 },
  stepNavigation: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 6 },
  historyButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 8, borderRadius: 12 },
  historyLabel: { color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 13 }, historyDisabled: { opacity: .4 },
  historyChecked: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12, borderRadius: 14, backgroundColor: '#ECF8F0' },
  rail: { flex: 1, flexDirection: 'row', gap: 3, padding: 4, borderRadius: 10, backgroundColor: '#E9F6EF' }, railStep: { flex: 1, height: 7, borderRadius: 4, backgroundColor: '#DCEEE5' },
  railActive: { backgroundColor: '#6CCF99' },
  question: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 23 },
  expression: { backgroundColor: '#F1EBFF', borderRadius: 18, padding: 18 },
  expressionText: { fontSize: 24, lineHeight: 34, color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  choice: { minHeight: 48, borderRadius: 13, padding: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1.5, borderColor: '#DDD4F5', backgroundColor: '#FAF8FF' },
  choiceSelected: { backgroundColor: '#E8DEFF', borderColor: COLORS.primary }, choiceText: { color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 15, lineHeight: 21 },
  choiceCorrect: { backgroundColor: '#ECF8F0', borderColor: '#7CBA96' }, chosenCorrect: { fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 18, color: '#24794E', marginTop: 4 },
  choiceIncorrect: { backgroundColor: '#FFF4F0', borderColor: '#DBA396' }, checkedAnswer: { padding: 12, borderRadius: 13, borderWidth: 1.5, borderColor: '#7CBA96', backgroundColor: '#ECF8F0', gap: 5 },
  choiceFocused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed', borderWidth: 2 },
  answerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, alignItems: 'center' }, numberInput: { flex: 1, minWidth: 120, minHeight: 58, borderWidth: 1.5, borderColor: '#D7CDF2', backgroundColor: '#FAF8FF', borderRadius: 16, padding: 16, fontFamily: FONTS.bold, fontSize: 18, color: COLORS.textPrimary },
  fractionAnswer: { flex: 1, minWidth: 120, maxWidth: 300, borderWidth: 1.5, borderColor: '#D7CDF2', backgroundColor: '#FAF8FF', borderRadius: 16, padding: 12, gap: 4 },
  fractionNumber: { minHeight: 48, textAlign: 'center', fontFamily: FONTS.bold, fontSize: 20, color: COLORS.textPrimary },
  fractionBar: { height: 2, backgroundColor: COLORS.primaryDark, marginHorizontal: 16 },
  answerMode: { alignSelf: 'flex-start', minHeight: 44, paddingHorizontal: 12, justifyContent: 'center', borderRadius: 12, backgroundColor: '#F0EBF8' },
  answerModeLabel: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark },
  unit: { flexShrink: 1, maxWidth: '100%', color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 19 },
  explanation: { backgroundColor: '#E9F5EF', padding: 16, borderRadius: 16 }, feedback: { color: '#226A51', fontFamily: FONTS.bold, fontSize: 15, lineHeight: 23 },
  hintCard: { backgroundColor: '#F4EEFF', borderWidth: 1, borderColor: '#D7CDF2', padding: 16, borderRadius: 16, gap: 10 },
  hintBody: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 23, color: COLORS.textPrimary },
  hintNavigation: { flexDirection: 'row', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 },
  hintNavButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, borderRadius: 10 },
  incorrectFeedback: { gap: 5, padding: 12, borderRadius: 14, backgroundColor: '#FFF4F0', borderWidth: 1, borderColor: '#DBA396' },
  solutionToggle: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start', paddingHorizontal: 6, borderRadius: 10 },
  solutionDetails: { gap: 8, padding: 12, borderRadius: 12, backgroundColor: '#F5F1FC' },
  guidanceCard: { backgroundColor: '#F8F6FF', borderWidth: 1, borderColor: '#E0D8FA', padding: 16, borderRadius: 16, gap: 14 },
  guidanceItem: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  guidanceNumber: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#EAE2FF', color: COLORS.primaryDark, textAlign: 'center', lineHeight: 28, fontFamily: FONTS.bold },
  completedStep: { gap: 8, paddingVertical: 12, borderBottomWidth: 1, borderColor: '#ECE6F5' },
});
