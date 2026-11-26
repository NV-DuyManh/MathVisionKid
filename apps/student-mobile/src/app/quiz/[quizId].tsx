import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { AppHeader } from '../../components/ui/AppHeader';
import { ChallengeButton as AppButton, CHALLENGE_COLORS as C, ChallengeWebStyles } from '../../components/ui/ChallengeVisuals';
import { MathText } from '../../components/domain/MathText';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { PendingTask } from '../../components/ui/PendingTask';
import { Quiz, quizApi, quizError } from '../../features/quiz/quizApi';
import { quizTime, submissionId, validQuizAnswer } from '../../features/quiz/quizInput';
import { QuizVoice, QuizNarrationPreparation } from '../../features/quiz/QuizVoice';
import { QuizHelp } from '../../features/quiz/QuizHelp';
import { useQuizActivity } from '../../features/quiz/useQuizActivity';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { NarrationPreparation } from '../../features/tutoring/NarrationPreparation';
import { quizStyles as s } from '../../features/quiz/quizStyles';
import { IS_STUDENT_WEB } from '../../constants/theme';

const QUIZ_ICON_COLOR = C.deepPurple;
const QUIZ_LINK_COLOR = C.deepPurple;

function Reward({ stars }: { stars: number }) {
  const [opacity] = useState(() => new Animated.Value(1));
  useEffect(() => {
    if (IS_STUDENT_WEB && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
    let active = true;
    void AccessibilityInfo.isReduceMotionEnabled().then(reduced => {
      if (active && !reduced && stars > 0) { opacity.setValue(.3); Animated.timing(opacity, { toValue: 1, duration: 500, useNativeDriver: true }).start(); }
    });
    return () => { active = false; opacity.stopAnimation(); };
  }, [opacity, stars]);
  return <Animated.View style={[s.stars, { opacity }]} accessibilityLabel={`${stars} sao`}>
    {[0, 1, 2].map(index => <View key={index} style={s.resultMedal} accessible={false}><Ionicons name={index < stars ? 'star' : 'star-outline'} color={index < stars ? '#A66800' : '#88769C'} size={30} accessible={false} /></View>)}
  </Animated.View>;
}
export default function QuizScreen() {
  const { quizId } = useLocalSearchParams<{ quizId: string }>();
  const auth = useContext(AuthContext), owner = auth?.user?.id || auth?.user?.userId;
  return owner && typeof quizId === 'string' ? <Challenge key={`${owner}:${quizId}`} id={quizId} owner={owner} /> : null;
}
type QuizTask = 'start' | 'submit' | 'challenge' | 'practice' | 'save' | 'reveal';
function Challenge({ id, owner }: { id: string; owner: string }) {
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null), [answer, setAnswer] = useState(''), [feedback, setFeedback] = useState('');
  const [error, setError] = useState(''), [task, setTask] = useState<QuizTask | null>(null), [loading, setLoading] = useState(true);
  const busy = task !== null;
  const [tool, setTool] = useState<'audio' | 'ask' | 'menu' | 'solution' | 'history' | null>(null);
  const elapsed = useQuizActivity(quiz);
  const [retry, setRetry] = useState(0);
  const [invalidAnswer, setInvalidAnswer] = useState(false);
  const [answerFocused, setAnswerFocused] = useState(false);
  const [workspaceWidth, setWorkspaceWidth] = useState(0);
  const wide = workspaceWidth >= 860;
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const pending = useRef<{ requestId: string; answer: string } | null>(null);
  const apply = useCallback((next: Quiz) => {
    setQuiz(next);
  }, []);
  useFocusEffect(useCallback(() => {
    void retry;
    active.current = true; setLoading(true); setError('');
    const abort = new AbortController(); controller.current = abort;
    void quizApi.get(id, abort.signal).then(next => { if (active.current && !abort.signal.aborted) apply(next); })
      .catch(failure => { if (active.current && !abort.signal.aborted) setError(quizError(failure)); })
      .finally(() => { if (active.current && !abort.signal.aborted) { setLoading(false); controller.current = null; } });
    const listener = AppState.addEventListener('change', state => { if (state === 'active') setRetry(value => value + 1); });
    return () => { active.current = false; abort.abort(); controller.current?.abort(); controller.current = null; listener.remove(); setTask(null); };
  }, [id, retry, apply]));
  const perform = async (kind: QuizTask, action: (signal: AbortSignal) => Promise<Quiz>) => {
    if (controller.current || loading) return;
    const abort = new AbortController(); controller.current = abort; setTask(kind); setError('');
    try { const next = await action(abort.signal); if (active.current && !abort.signal.aborted) apply(next); }
    catch (failure) { if (active.current && !abort.signal.aborted) setError(quizError(failure)); }
    finally { if (active.current && !abort.signal.aborted) { controller.current = null; setTask(null); } }
  };
  const submit = () => {
    if (!quiz || busy || loading || controller.current) return;
    if (!validQuizAnswer(answer, quiz.unit)) { setInvalidAnswer(true); setError('Em nhập một số, số thập phân hoặc phân số hợp lệ, ví dụ 48 hoặc 3/4 nhé.'); return; }
    setInvalidAnswer(false);
    if (!pending.current || pending.current.answer !== answer.trim()) pending.current = { requestId: submissionId(), answer: answer.trim() };
    const request = pending.current;
    void perform('submit', async signal => {
      const result = await quizApi.submit(id, request.requestId, request.answer, signal);
      if (active.current && !signal.aborted) {
        pending.current = null;
        setFeedback(result.quiz.status === 'COMPLETED' ? result.quiz.completedWithSolution ? 'Em đã hoàn thành bài luyện tập cùng cách giải. Mình tiếp tục khám phá nhé!'
          : result.attempt.correct ? 'Đúng rồi! Em đã hoàn thành bài luyện tập này.' : 'Quiz này đã được hoàn thành. Em có thể xem lại những lần thử bên dưới nhé.'
          : result.quiz.wrongAttempts < 2 ? 'Chưa đúng rồi, nhưng em thử kiểm tra lại nhé!'
            : 'Em thử lại nhé! Phần Cách giải cũng đã sẵn sàng để cùng em tìm hiểu.');
      }
      return result.quiz;
    });
  };
  const replayQuiz = (mode: 'PRACTICE' | 'CHALLENGE' = 'CHALLENGE') => {
    void perform(mode === 'CHALLENGE' ? 'challenge' : 'practice', async signal => {
      const next = await quizApi.replay(id, mode, signal);
      if (active.current && !signal.aborted) { setAnswer(''); setFeedback(''); setTool(null); pending.current = null; }
      return next;
    });
  };
  const saveForLater = () => { void perform('save', async signal => { const next = await quizApi.defer(id, signal); if (active.current && !signal.aborted) router.replace('/quiz' as never); return next; }); };
  const done = quiz?.status === 'COMPLETED', running = quiz?.status === 'IN_PROGRESS';
  const parts = quiz?.questionText.split(/\n(?=[A-D]\. )/) ?? [''];
  const [question, ...choices] = parts.length >= 3 && parts.length <= 5 ? parts : [quiz?.questionText ?? ''];
  const latestCompletion = quiz?.attempts.slice().reverse().find(attempt => attempt.correct);
  const earnedStars = latestCompletion?.stars ?? quiz?.stars ?? 0;

  return <QuizNarrationPreparation owner={owner} quizId={id} content={quiz?.explanationText ? 'SOLUTION' : 'QUESTION'} paragraphs={quiz && !loading && quiz.startedAt ? [quiz.explanationText || quiz.questionText] : []}>
  <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <AppHeader title="Thử thách nhỏ của em" showBack />
    <KeyboardAvoidingView style={s.scroll} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView style={s.scroll} contentContainerStyle={[s.content,s.workContent]} keyboardShouldPersistTaps="handled">
        {loading ? <View style={s.card}><TaskProgress steps={['Mở câu đố của em', 'Khôi phục tiến trình']} activeStep={1} /></View> : null}
        {error ? <View style={s.note}><Text nativeID="quiz-answer-error" accessibilityRole="alert" style={s.error}>{error}</Text><AppButton title={quiz ? 'Kiểm tra lại trạng thái' : 'Thử tải lại'} variant="secondary" disabled={busy || loading} onPress={() => setRetry(value => value + 1)} /></View> : null}
        {quiz && !loading ? <>
          <View style={s.workspace} onLayout={event => setWorkspaceWidth(event.nativeEvent.layout.width)} testID="quiz-workspace" {...(IS_STUDENT_WEB ? { dataSet: { challenge: 'true' } } : {})}>
          <ChallengeWebStyles />
          <View style={s.challengeHeading}>
            <View style={s.challengeEmblem}><Ionicons name={done ? 'ribbon-outline' : 'flag-outline'} size={28} color={C.deepPurple} accessible={false} /></View>
            <View style={s.challengeHeadingCopy}><Text style={s.eyebrow}>{quiz.replayMode === 'PRACTICE' ? 'GÓC ÔN TẬP' : 'KHÁM PHÁ KHẢ NĂNG CỦA EM'}</Text><Text accessibilityRole="header" style={[s.challengeTitle, wide && s.challengeTitleWide]}>{done ? 'Mỗi lần thử, một bước tiến' : running ? 'Đến lượt em trổ tài!' : 'Sẵn sàng thử sức chưa em?'}</Text></View>
          </View>
          <View style={[s.workspaceColumns, wide && s.workspaceColumnsWide]}>
          <View style={[s.card,s.workCard,s.challengeMain,wide && s.challengeMainWide]} testID="quiz-question-area">
            <View style={s.workTopline}>
              <View style={s.workBadge}><Ionicons name={done?'checkmark-circle-outline':'sparkles-outline'} size={16} color={C.deepPurple} accessible={false}/><Text style={s.workBadgeText}>{done?'ĐÃ HOÀN THÀNH':'BÀI TOÁN CỦA EM'}</Text></View>
              <Text style={s.small}>Lớp {quiz.gradeLevel}</Text>
            </View>
            {!wide ? <View style={s.mobileClock}><Ionicons name="time-outline" size={22} color={C.deepPurple} accessible={false}/><Text testID="quiz-timer" style={s.mobileClockNumber} accessibilityLabel={`Thời gian làm bài ${quizTime(done ? quiz.elapsedMillis : elapsed)}`}>{quizTime(done ? quiz.elapsedMillis : elapsed)}</Text><Text style={[s.small,s.mobileClockHint]}>{done ? 'Đã ghi nhận' : running ? 'Theo nhịp của em' : 'Chưa bắt đầu'}</Text></View> : null}
            <View style={s.questionPanel}>
              <Text style={s.workTopic}>Lớp {quiz.gradeLevel} · {quiz.topicName}</Text>
              <MathText style={s.quizQuestion}>{question}</MathText>
              {!running ? choices.map(choice => <Text key={choice} style={s.body}>{choice}</Text>) : null}
            </View>
            {done ? <View style={s.result}>
              <View style={s.resultPanel}>
              {quiz.replayMode !== 'PRACTICE' ? <Reward stars={earnedStars}/> : null}
              <Text accessibilityLiveRegion={IS_STUDENT_WEB ? 'polite' : undefined} style={[s.heading,{textAlign:'center'}]}>{quiz.completedWithSolution ? 'Mình cùng hiểu thêm một bài!' : 'Em đã hoàn thành rồi!'}</Text>
              <Text style={[s.body,{textAlign:'center'}]}>{quiz.replayMode === 'PRACTICE' ? 'Em đã ôn lại bài cũ. Thành tích của em được giữ nguyên.' : `Lượt này: ${earnedStars} sao · Kỷ lục: ${quiz.stars} sao`}</Text>
              </View>
              <AppButton title="Thử thách nâng sao" loadingTitle="Đang chuẩn bị câu mới…" style={s.workButton} disabled={busy} loading={task === 'challenge'} onPress={() => replayQuiz('CHALLENGE')}/>
              {task === 'challenge' || task === 'practice' ? <PendingTask key={task} title={task === 'challenge' ? 'Đang tạo câu mới cùng dạng' : 'Đang mở lại bài cũ'} detail="Em có thể xem lại cách giải hoặc về trang chủ trong lúc chờ. Bài đã làm vẫn được giữ."/> : null}
            </View> : running ? <>
              {quiz.replayMode === 'CHALLENGE' ? <Text style={s.small}>Thử thách nâng sao · Câu hỏi mới cho em</Text> : quiz.replayMode === 'PRACTICE' ? <Text style={s.small}>Ôn lại bài cũ · Giữ nguyên thành tích</Text> : null}
              <Text nativeID="quiz-answer-label" style={s.title}>Đáp án của em{quiz.unit ? ` (${quiz.unit})` : ''}</Text>
              {choices.length ? <View accessibilityRole="radiogroup" accessibilityLabel="Chọn đáp án của em" style={s.choiceList}
                onKeyDown={IS_STUDENT_WEB ? event => {
                  const key = event.nativeEvent.key;
                  if (busy || !['ArrowRight','ArrowDown','ArrowLeft','ArrowUp','Home','End',' ','Enter'].includes(key)) return;
                  const group = event.currentTarget as unknown as HTMLElement;
                  const options = Array.from(group.querySelectorAll<HTMLElement>('[role="radio"]'));
                  const current = options.findIndex(option => option === document.activeElement);
                  if (key === ' ' || key === 'Enter') {
                    if (current >= 0) { event.preventDefault(); options[current].click(); }
                    return;
                  }
                  const next = key === 'Home' ? 0 : key === 'End' ? options.length - 1 : (Math.max(0,current) + (['ArrowRight','ArrowDown'].includes(key) ? 1 : -1) + options.length) % options.length;
                  event.preventDefault(); options[next]?.focus(); options[next]?.click();
                } : undefined}>
                {choices.map((choice, index) => {
                  let value = quiz.answerFormat === 'CHOICE' ? String(index + 1) : choice.slice(3).trim();
                  if (quiz.unit && value.endsWith(' ' + quiz.unit)) value = value.slice(0, -quiz.unit.length).trim();
                  value = value.replace(/\s+/g, '');
                  const selected = answer === value;
                  return <Pressable key={choice} accessibilityRole="radio" accessibilityLabel={choice} accessibilityState={{ checked: selected, disabled: busy }} aria-checked={selected} aria-disabled={busy}
                    {...(IS_STUDENT_WEB ? { tabIndex: selected || !answer && index === 0 ? 0 : -1 } : {})}
                    disabled={busy} style={({pressed}) => [s.group,s.answerChoice,selected && s.selected,pressed && s.choicePressed,busy && s.choiceDisabled]} onPress={() => { setAnswer(value); setError(''); }}>
                    <View style={[s.choiceLetter,selected && s.choiceLetterSelected]}><Text style={[s.choiceLetterText,selected && s.choiceLetterTextSelected]}>{String.fromCharCode(65 + index)}</Text></View><Text style={[s.body,s.choiceCopy,selected && s.choiceCopySelected]}>{choice.slice(3)}</Text>
                  </Pressable>;
                })}
              </View> : <>
                <TextInput accessibilityLabel={`Đáp án của em${quiz.unit ? `, ${quiz.unit}` : ''}`} aria-describedby={invalidAnswer ? 'quiz-answer-help quiz-answer-error' : 'quiz-answer-help'} aria-invalid={invalidAnswer}
                  value={answer} onChangeText={value => { setAnswer(value); setError(''); setInvalidAnswer(false); }} onFocus={() => setAnswerFocused(true)} onBlur={() => setAnswerFocused(false)} style={[s.input,s.workInput,answerFocused&&s.focusedInput,invalidAnswer&&s.workInputError]} editable={!busy} maxLength={100} autoComplete="off" autoCorrect={false}
                  placeholder={quiz.answerFormat === 'FRACTION' ? 'Ví dụ: 3/4' : 'Em tính được…'} keyboardType={quiz.answerFormat === 'FRACTION' ? 'default' : 'decimal-pad'} returnKeyType="done" onSubmitEditing={submit}/>
                <Text nativeID="quiz-answer-help" style={s.small}>{quiz.answerFormat === 'FRACTION' ? 'Nhập phân số a/b hoặc số thập phân chính xác.' : 'Chỉ cần nhập kết quả cuối cùng.'}</Text>
              </>}
              {!IS_STUDENT_WEB && feedback ? <Text accessibilityLiveRegion="polite" style={s.error}>{feedback}</Text> : null}
              <AppButton title="Hoàn thành" loadingTitle="Đang kiểm tra đáp án…" style={s.workButton} disabled={busy || !answer.trim()} loading={task === 'submit'} onPress={submit}/>
              {IS_STUDENT_WEB ? <Text accessibilityLiveRegion="polite" style={feedback ? [s.error, s.webFeedback] : s.emptyFeedback}>{feedback}</Text> : null}
              {quiz.solutionViewed ? <Text style={s.small}>{quiz.replayMode === 'PRACTICE' ? 'Em cứ luyện theo nhịp của mình nhé.' : 'Em đang luyện cùng hướng dẫn. Hoàn thành lượt này em nhận 1 sao.'}</Text> : null}
            </> : <>
              <View style={s.readyNote}><Ionicons name="bulb-outline" size={24} color={C.deepPurple} accessible={false}/><Text style={[s.body,s.readyCopy]}>Đọc kỹ đề, chọn cách làm của em. Đồng hồ bắt đầu khi em mở thử thách.</Text></View>
              <AppButton title="Bắt đầu thử thách" loadingTitle="Đang mở câu đố…" style={s.workButton} disabled={busy} loading={task === 'start'} icon={<Ionicons name="play" size={18} color="#FFFFFF" accessible={false}/>} onPress={() => void perform('start', signal => quizApi.start(id, signal))}/>
            </>}
            {quiz.explanationText ? <Pressable accessibilityRole="button" accessibilityLabel="Xem cách giải" style={s.detailLink} onPress={()=>setTool('solution')}><Ionicons name="reader-outline" size={19} color={QUIZ_LINK_COLOR}/><Text style={s.topic}>Xem cách giải</Text><Ionicons name="chevron-forward" size={17} color={QUIZ_LINK_COLOR}/></Pressable> : null}
            <View style={[s.secondaryActions,wide && s.secondaryActionsWide]}>
              <View style={s.secondaryAction}>{!done ? <AppButton title="Lưu để làm sau" loadingTitle="Đang lưu bài…" variant="secondary" disabled={busy} loading={task === 'save'} onPress={saveForLater}/> : <AppButton title="Về trang chủ" variant="secondary" icon={<Ionicons name="home-outline" size={19} color={C.deepPurple} accessible={false}/>} onPress={() => router.replace('/(tabs)')}/>}</View>
              <View style={s.secondaryAction}><AppButton title={done ? 'Chọn câu đố khác' : 'Trở về danh sách'} variant="ghost" onPress={() => router.replace('/quiz' as never)}/></View>
            </View>
          </View>
          <View style={[s.challengeAside,wide && s.challengeAsideWide]} testID="quiz-support-panel">
            {wide ? <View style={s.timerPanel}>
              <View style={s.timerHeading}><Ionicons name="time-outline" size={22} color={C.yellow} accessible={false}/><Text style={s.timerLabel}>{done ? 'THỜI GIAN HOÀN THÀNH' : running ? 'THEO NHỊP CỦA EM' : 'ĐỒNG HỒ SẴN SÀNG'}</Text></View>
              <Text testID="quiz-timer" style={s.timerNumber} accessibilityLabel={`Thời gian làm bài ${quizTime(done ? quiz.elapsedMillis : elapsed)}`}>{quizTime(done ? quiz.elapsedMillis : elapsed)}</Text>
              <Text style={s.timerHint}>{done ? 'Kết quả đã được ghi nhận.' : 'Đồng hồ chỉ tính khi em đang làm trong Quiz; rời màn hình sẽ tạm dừng.'}</Text>
            </View> : null}
            <View style={s.supportCard}>
              <Text style={s.supportTitle}>{quiz.replayMode === 'PRACTICE' ? 'Luyện tập theo nhịp của em' : done ? 'Thành tích lượt này' : 'Chinh phục những ngôi sao'}</Text>
              {quiz.replayMode === 'PRACTICE' ? <Text style={s.small}>Ôn lại bài cũ không chấm sao mới. Thành tích của em được giữ nguyên.</Text> : done ? <><View style={s.earnedRow}><Ionicons name="star" size={26} color="#906112" accessible={false}/><Text style={s.earnedNumber}>{earnedStars} sao</Text></View><Text style={s.small}>{quiz.completedWithSolution ? 'Hoàn thành cùng hướng dẫn.' : 'Số sao đã được xác nhận cho lượt này.'} Kỷ lục: {quiz.stars} sao.</Text></> : quiz.solutionViewed ? <Text style={s.small}>Em đang luyện cùng hướng dẫn. Hoàn thành lượt này em nhận 1 sao.</Text> : <>
                {[[3,'Trong 30 giây'],[2,'Trên 30 đến 60 giây'],[1,'Sau 60 giây']].map(([stars,label]) => <View key={stars} style={s.rewardRule}><View style={s.ruleStars} accessible={false}>{[0,1,2].map(index => <Ionicons key={index} name={index < Number(stars) ? 'star' : 'star-outline'} size={17} color={index < Number(stars) ? '#906112' : '#9A8C6E'} accessible={false}/>)}</View><Text style={s.ruleLabel}>{label}</Text></View>)}
                <Text style={s.small}>Trả lời đúng để nhận sao theo thời gian làm bài.</Text>
              </>}
              <View style={s.quizPhases} accessibilityLabel={`Trạng thái: ${done ? 'Hoàn thành' : running ? 'Đang giải bài' : 'Chuẩn bị'}`}>
                {['Chuẩn bị','Giải bài','Hoàn thành'].map((label,index) => {
                  const step = done ? 2 : running ? 1 : 0;
                  return <View key={label} style={s.quizPhase}><View style={[s.journeyDot,index <= step && s.journeyDotActive]}><Ionicons name={index < step || done ? 'checkmark' : index === step ? 'ellipse' : 'ellipse-outline'} size={14} color={index <= step ? '#FFFFFF' : '#8A80AA'} accessible={false}/></View><Text style={[s.phaseLabel,index === step && s.journeyCurrent]}>{label}</Text></View>;
                })}
              </View>
            </View>
          </View>
          </View>
          </View>
        </> : null}
        {!quiz && !loading ? <AppButton title="Trở về danh sách" variant="ghost" onPress={() => router.replace('/quiz' as never)} /> : null}
      </ScrollView>
      {quiz?.startedAt && !loading ? <View style={s.toolsDock} testID="quiz-fixed-tools">
        <View style={[s.tools,s.workTools,IS_STUDENT_WEB&&s.webWorkTools]}>
          {([['audio','volume-high-outline','Nghe giảng'],['ask','mic-outline','Hỏi bài'],['menu','ellipsis-horizontal','Xem thêm']] as const).map(([value,icon,label])=><Pressable key={value} accessibilityRole="button" accessibilityLabel={label} style={({pressed})=>[s.tool,s.workTool,pressed&&s.selected]} onPress={()=>setTool(value)}>
            <Ionicons name={icon} size={22} color={QUIZ_ICON_COLOR} accessible={false}/><Text style={s.toolLabel}>{label}</Text>
          </Pressable>)}
        </View>
      </View> : null}
    </KeyboardAvoidingView>
    {quiz && tool ? <LessonSheet title={{audio:'Nghe giảng',ask:'Hỏi bài',menu:'Em cần gì thêm?',solution:'Cách giải',history:'Những lần em đã thử'}[tool]} onClose={()=>setTool(null)}>
      {tool==='audio' ? <QuizVoice key={`${quiz.quizId}:${quiz.startedAt}:${!!quiz.explanationText}`} quizId={quiz.quizId} content={quiz.explanationText?'SOLUTION':'QUESTION'} paragraphs={[quiz.explanationText || quiz.questionText]}/> : null}
      {tool==='ask' ? busy ? <PendingTask key={task} title="Đang hoàn tất thao tác vừa rồi" detail="Phần hỏi bài sẽ mở ngay khi xong, để câu hỏi của em đi đúng với bài đang làm."/> : <NarrationPreparation owner={owner}><QuizHelp quiz={quiz} onAssisted={apply} onReturn={()=>setTool(null)}/></NarrationPreparation> : null}
      {tool==='solution' ? <MathText style={s.body}>{quiz.explanationText || ''}</MathText> : null}
      {tool==='menu' ? <>
        {quiz.canRevealSolution && !quiz.solutionViewed && !done ? <AppButton title="Xem cách giải" loadingTitle="Đang mở cách giải…" variant="secondary" disabled={busy} loading={task === 'reveal'} onPress={()=>void perform('reveal', async signal=>{const next=await quizApi.reveal(id,signal);if(active.current&&!signal.aborted)setTool('solution');return next;})}/> : null}
        {quiz.explanationText ? <AppButton title="Xem cách giải" variant="secondary" onPress={()=>setTool('solution')}/> : null}
        {quiz.attempts.length ? <AppButton title={`Xem ${quiz.attempts.length} lần đã thử`} variant="secondary" onPress={()=>setTool('history')}/> : null}
        {done ? <AppButton title="Ôn lại bài cũ" variant="secondary" disabled={busy} onPress={()=>{setTool(null);replayQuiz('PRACTICE');}}/> : <AppButton title="Lưu để làm sau" variant="secondary" disabled={busy} onPress={saveForLater}/>}
        <AppButton title="Về trang chủ" variant="ghost" onPress={()=>router.replace('/(tabs)')}/>
      </> : null}
      {tool==='history' ? quiz.attempts.slice().reverse().map(attempt=><View key={attempt.number} style={s.note}>
        {attempt.questionText ? <MathText style={s.small}>{attempt.questionText}</MathText> : null}
        <Text style={s.title}>{`Lần ${attempt.number}: ${attempt.answer} · ${attempt.correct?'Đúng':'Chưa đúng'}`}</Text>
        <Text style={s.small}>{`${quizTime(attempt.elapsedMillis)} · ${attempt.stars || 0} sao · ${new Date(attempt.submittedAt).toLocaleDateString('vi-VN')}`}</Text>
      </View>) : null}
    </LessonSheet> : null}
  </SafeAreaView></QuizNarrationPreparation>;
}
